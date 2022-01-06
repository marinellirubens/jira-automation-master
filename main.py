"""Program to read tickets from JIRA and automate the process of solving the issues"""
import configparser
import logging
import time
from typing import List

from automation_service.jira_service import JiraService, JiraProcess
from automation_service.config import set_logger, get_config


PROCESS_QUEUE: List[JiraProcess] = []
SLEEP_TIME: int = 1
PROCESS_QUEUE_SIZE: int = 1
LOGGER = logging.getLogger(__name__)
SERVICE: JiraService = None
CONFIG: configparser.ConfigParser = None


def main():
    """Main function"""
    global LOGGER # pylint: disable=global-statement
    global CONFIG # pylint: disable=global-statement
    global PROCESS_QUEUE_SIZE # pylint: disable=global-statement
    try:
        # main service execution
        LOGGER = set_logger()
        CONFIG = get_config('config.ini', LOGGER)
        PROCESS_QUEUE_SIZE = int(CONFIG['SETUP']['process_queue_size'])
        LOGGER.info('Starting the service')
        start_service(CONFIG['JIRA'], CONFIG['ORACLE'])
        wait_service()
    except (OSError, KeyboardInterrupt):
        kill_processes()
    finally:
        LOGGER.info('Ending service')

def wait_service():
    """Wait for the service to finish"""
    # SERVICE.join()
    while SERVICE.is_alive():
        check_processes()
        time.sleep(1)


def check_processes():
    """Check the processes on the queue"""
    for queue_item in PROCESS_QUEUE:
        if not queue_item.process.is_alive():
            LOGGER.info("Process %s ended", queue_item.issue_key)
            PROCESS_QUEUE.remove(queue_item)


def start_service(jira_config: dict, database_config: dict):
    """Start the service"""
    global SERVICE # pylint: disable=global-statement
    SERVICE = JiraService(
        logger=LOGGER,
        jira_config=jira_config,
        database_config=database_config,
        PROCESS_QUEUE=PROCESS_QUEUE,
        PROCESS_QUEUE_SIZE=PROCESS_QUEUE_SIZE,
        sleep_time=int(CONFIG['SETUP']['sleep_time']),
        mail_list_lookup_code=CONFIG['SETUP']['mail_list_lookup_code']
    )
    SERVICE.start()


def kill_processes():
    """Kill the processes on the queue"""
    for queue_item in PROCESS_QUEUE:
        queue_item.process.kill()
        LOGGER.info("Process %s killed", queue_item.issue_key)
        PROCESS_QUEUE.remove(queue_item)

    SERVICE.stop()


if __name__ == '__main__':
    main()
