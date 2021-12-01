"""Program to read tickets from JIRA and automate the process of solving the issues"""
import logging
import time

from jira_service import JiraService
from setup import set_logger, get_config


PROCESS_QUEUE = []
SLEEP_TIME = 1
PROCESS_QUEUE_SIZE = 10
LOGGER = logging.getLogger(__name__)
SERVICE: JiraService = None
CONFIG = {}

def main():
    """Main function"""
    global LOGGER
    global CONFIG
    try:
        # main service execution
        LOGGER = set_logger()
        CONFIG = get_config('config.ini', LOGGER)
        LOGGER.info('Starting the service')
        start_service(CONFIG['JIRA'], CONFIG['ORACLE'])
        wait_service()
    except OSError:
        kill_processes()
    except KeyboardInterrupt:
        kill_processes()
    finally:
        LOGGER.info('Ending service')

def wait_service():
    """Wait for the service to finish"""
    # SERVICE.join()
    while SERVICE.is_alive():
        time.sleep(1)

def start_service(jira_config: dict, database_config: dict):
    """Start the service"""
    global SERVICE
    SERVICE = JiraService(logger=LOGGER, jira_config=jira_config, database_config=database_config,
                          PROCESS_QUEUE=PROCESS_QUEUE,
                          PROCESS_QUEUE_SIZE=PROCESS_QUEUE_SIZE, sleep_time=5)
    SERVICE.start()


def kill_processes():
    """Kill the processes on the queue"""
    for process in PROCESS_QUEUE:
        # process['process'].kill()
        LOGGER.info("Process {} killed".format(process['issue']))
        PROCESS_QUEUE.remove(process)

    SERVICE.stop()


if __name__ == '__main__':
    main()
