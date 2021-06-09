from pathlib import Path
import io
from googleapiclient.http import MediaIoBaseDownload
from apiclient import discovery

import ee
from sepal_ui.scripts import gee

from component.message import cm



import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

class gdrive(object):

    def __init__(self):
        
        self.initialize = ee.Initialize()
        self.credentials = ee.Credentials()
        self.service = discovery.build(serviceName='drive', version='v3', cache_discovery=False, credentials=self.credentials)
        
    def tasks_list(self):
        """for debugging purpose, print the list of all the tasks in gee"""
        service = self.service
        
        tasks = service.tasks().list(tasklist='@default', q="trashed = false").execute()

        for task in tasks['items']:
            print(task['title'])


    def print_file_list(self):
        """ for debugging purpose, print the list of all the file in the Gdrive"""
        service = self.service

        results = service.files().list(
            pageSize=50, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print('{0} ({1})'.format(item['name'], item['id']))

    def get_items(self):
        """ get all the items in the Gdrive, items will have 2 columns, 'name' and 'id' """ 
        service = self.service
        
        # get list of files
        results = service.files().list( 
            q ="mimeType='image/tiff' and trashed = false",
            pageSize=1000, 
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        return items
    
    
    def get_files(self, file_name):
        """ look for the file_name patern in my Gdrive files and retreive a list of Ids"""
        
        items = self.get_items()
        files = []
        for item in items:
            if (file_name in item['name']):
                files.append({'id':item['id'], 'name': item['name']})
                
        return files
                                
    def download_files(self, files, local_path):
        """download the files from gdrive to the local_path"""
        
        # create path object 
        local_path = Path(local_path)
        
        #open the gdrive service
        service = self.service
        
        # request the files from gdrvie in chunks
        for file in files:
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            # write them in a local based file
            with local_path.joinpath(file['name']).open('wb') as f:
                f.write(fh.getvalue())
            
    def delete_files(self, files):
        """ delete files from gdrive disk"""
        
        # open gdrive service
        service = self.service
        
        # remove the files
        for file in files:
            service.files().delete(fileId=file['id']).execute()
            
    def download_to_disk(self, filename, image, aoi_model, output):
        """download the tile to the GEE disk
        
        Args:
            filename (str): descripsion of the file
            image (ee.FeatureCollection): image to export
            aoi_model (AoiModel): the aoi used to clip the image
            
        Returns:
            download (bool) : True if a task is running, false if not
        """
        
        def launch_task(filename, image, aoi_io, output):
            """check if file exist and launch the process if not"""
            
            download = False
            
            files = self.get_files(filename) 
            
            if files == []:
                task_config = {
                    'image':image,
                    'description':filename,
                    'scale': 30,
                    'region':aoi_model.feature_collection.geometry(),
                    'maxPixels': 1e13
                }
                
                task = ee.batch.Export.image.toDrive(**task_config)
                task.start()
                download = True
            else:
                output.add_live_msg(cm.driver.already_completed.format(filename), 'success')
            
            return download
        
        task = gee.is_task(filename)
        if not task:
            download = launch_task(filename, image, aoi_model, output)
        else:
            if task.state == 'RUNNING':
                output.add_live_msg(cm.driver.task_running.format(filename))
                download = True
            else: 
                download = launch_task(filename, image, aoi_model, output)
                
        return download