# 3. Postprocess the alerts

> :warning: Before launching the process, make sure that your instance is powerful enough to run the process. `m4` is the minimum for country-size computation.

By clicking on `run postprocessing`, you will launch the analysis of the glad alerts on your SEPAL computer. The different steps are described here:

- Merge the tiles to produce a single raster (.tif) 
- Delete the downloaded tiles
- Create patches of glad alerts in a tmp file
- Produce a distribution of the glad alert patches 

> :warning: This action is performed in your sepal computer, you don't want to close the Sepal module before it's finished.

![postprocessing](./img/postprocess.png) 

---
[ go to  &rarr; 4. Use the results](./results.md)  

[return to &larr; 2. Retreive the alerts](./retreive_alert.md)
