import time 

import ee 

ee.Initialize()

# messages 
STATUS = "Status : {0}"

def custom_wait_for_completion(task_descripsion, output):
    """Wait until the selected process are finished. Display some output information

    Args:
        task_descripsion ([str]) : name of the running tasks
        widget_alert (v.Alert) : alert to display the output messages
    
    Returns: state (str) : final state
    """
    state = 'UNSUBMITTED'
    while not (state == 'COMPLETED' or state =='FAILED'):
        output.add_live_msg(STATUS.format(state))
        time.sleep(5)
                    
        #search for the task in task_list
        for task in task_descripsion:
            current_task = search_task(task)
            state = current_task.state
            if state == 'RUNNING': break
    
    return state