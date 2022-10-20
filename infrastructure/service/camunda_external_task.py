#!/usr/bin/env python
# usage example:
# python ./infrastructure/service/camunda_external_task.py unlock --task_id 6de2ba78-c0cf-11ea-b844-0ee97f00053b --topic screenshotter
import socket
from time import sleep

import logger
from infrastructure.exceptions import CamundaException
from infrastructure.service import BaseRemoteService, Camunda
from settings import WORKFLOW

# to use as worker id:
hostname = socket.gethostname()


class ExternalTask:
    def __init__(self, workflow: Camunda, params: dict):
        self.workflow = workflow
        self.log = logger.initLogging().getLogger(__name__)
        self.params = params

    def run(self):
        method = getattr(ExternalTask, self.params['command'][0], None)
        if method:
            return method(self, **self.params)
        else:
            self.log.error("Command {} not found...".format(self.params['command'][0]))
            return None

    def fetch(self, **kwargs) -> list:
        self.log.info("Fetching and locking camunda tasks in {} topic".format(kwargs['topic']))
        if kwargs['variables']:
            variables = kwargs['variables'].split(',')
        else:
            variables = None
        try:
            camunda_tasks = self.workflow.lock(worker_id=hostname,
                                               topic=kwargs['topic'],
                                               maxtasks=kwargs['tasks_per_run'],
                                               lockduration=kwargs['lock_duration'],
                                               variables=variables)
        except CamundaException:
            self.log.error("Cant get tasks from camunda, CamundaException", exc_info=True)
            return []
        except KeyError:
            self.log.error("One of the required parameters missing (topic, tasks_per_run, lock_duration, variables)")
            return []

        if camunda_tasks:
            self.log.info("Got {} - {} tasks from {} topic, locked for {} seconds".format(len(camunda_tasks),
                                                                                          camunda_tasks,
                                                                                          kwargs['topic'],
                                                                                          kwargs['lock_duration']))
            return camunda_tasks
        else:
            self.log.info("No tasks in {} topic for now".format(kwargs['topic']))
            return []

    def fetch_looped(self, func=fetch, **kwargs):
        try:
            delay = kwargs['command'][1]
        except (KeyError, IndexError):
            delay = 5
        while True:
            func(**kwargs)
            sleep(delay)

    def unlock(self, **kwargs):
        self.log.info("Unlocking task ".format(kwargs['task_id']))
        try:
            return self.workflow.unlock(kwargs['task_id'])
        except CamundaException:
            self.log.error("Cant unlock external tasks in camunda, CamundaException", exc_info=True)
            return None
        except KeyError:
            self.log.error("One of the required parameters missing (task_id)")
            return None

    def complete(self, **kwargs):
        self.log.info("Completing task ".format(kwargs['task_id']))
        # variables = {
        #     'pages_done': {
        #         'value': 200,
        #         'type': 'Integer'
        #     },
        #     'crawlerUrl': {
        #         'value': 'http://seomator.com',
        #         'type': 'String'
        #     },
        #     'crawlerError': {
        #         'value': 0,
        #         'type': 'Integer'
        #     },
        #     'hasErrors': {
        #         'value': False,
        #         'type': 'Boolean'
        #     }
        # }
        try:
            return self.workflow.complete(worker_id=hostname, task_id=kwargs['task_id'],
                                          variables=kwargs['variables'])
        except CamundaException:
            self.log.error("Cant complete external task in camunda, CamundaException", exc_info=True)
            raise CamundaException
        except KeyError:
            self.log.error("One of the required parameters missing (task_id, variables)")
            raise Exception

    def extend_duration(self, **kwargs):
        self.log.info("Extending task lock duration ".format(kwargs['task_id']))
        try:
            return self.workflow.extend_duration(worker_id=hostname,
                                                 task_id=kwargs['task_id'],
                                                 duration=kwargs['command'][1])
        except CamundaException:
            self.log.error("Cant extend lock for external task in camunda, CamundaException", exc_info=True)
            return None
        except KeyError:
            self.log.error("One of the required parameters missing (task_id, duration)")
            return None

    def bpmnError(self, **kwargs):
        self.log.info("bpmnError for task {}".format(kwargs['task_id']))
        try:
            errorMessage = kwargs['errorMessage'] if kwargs['errorMessage'] else ""
            return self.workflow.bpmnError(worker_id=hostname,
                                           task_id=kwargs['task_id'],
                                           errorcode=kwargs['command'][1],
                                           errorMessage=errorMessage)
        except CamundaException:
            self.log.error("Cant issue bpmnError for external task in camunda, CamundaException", exc_info=True)
            return None
        except KeyError:
            self.log.error("One of the required parameters missing (task_id, errorcode)")
            return None

    @staticmethod
    def cli_args():
        import argparse
        parser = argparse.ArgumentParser(usage="%(prog)s [COMMAND] [COMMAND_ARG] OPTIONS",
                                         description='Camunda/External Tasks CLI',
                                         epilog="HZ")

        requered_group = parser.add_argument_group('required arguments')

        requered_group.add_argument('--topic', help='Camunda External Tasks Topic for the worker to fetch tasks from',
                                    type=str,
                                    required=True, metavar='<TOPIC(S)>')

        parser.add_argument('command', help="command to execute, options: fetch(fetch task from topic), "
                                            "fetch_looped {delay}(fetch tasks from topic in infinite loop with delay)"
                                            ", unlock(unlock external task in camunda)"
                                            ", complete(complete external task in camunda)"
                                            ", extend_duration {duration} (extend lock for external task in camunda)"
                                            ", bpmnError {errorCode} (issue bmpnError with code for external task in "
                                            "camunda)",
                            nargs='*',
                            # TODO: bug in this default: expected list, but return string,
                            #  as a result, indexing by command return letters
                            default='fetch')

        parser.add_argument(
            '-ld', '--lock_duration', help='Lock duration for fetched and locked tasks before they are getting back'
                                           ' to the queue, default=300000 (5mins)',
            dest='lock_duration', type=int, default=300000)

        parser.add_argument(
            '--tasks_per_run', help='Number of tasks to fetch and lock per iteration, default=1',
            dest='tasks_per_run', type=int, default=1)

        # TODO: convert to list?
        parser.add_argument(
            '--variables', help='Variables list to fetch from Camunda',
            dest='variables', type=str)

        parser.add_argument(
            '-t', '--task_id', help='External task id',
            dest='task_id', type=str)

        parser.add_argument(
            '--workflow', help='Camunda url to connect to',
            dest='workflow', type=str, default=WORKFLOW)

        return parser


if __name__ == '__main__':

    args = ExternalTask.cli_args().parse_args()

    workflow_session = BaseRemoteService(url_prefix=args.workflow)

    workflow = Camunda(url_prefix=workflow_session.url_prefix, logger=logger.initLogging().getLogger(__name__),
                                           session=workflow_session.session)

    worker = ExternalTask(workflow=workflow, params=args.__dict__)

    worker.run()
