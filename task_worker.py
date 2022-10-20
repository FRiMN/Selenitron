#!/usr/bin/env python
import boto3

import logger
from consumers import S3Consumer
from generators.screenshot import ScreenshotGenerator
from infrastructure.dto import ExternalTaskDTO
from infrastructure.service import BaseRemoteService, Camunda
from infrastructure.service.camunda_external_task import ExternalTask
from settings import AWS_REGION_NAME
from utils import inject_fields_in_logger, reject_fields_from_logger

log = logger.initLogging().getLogger(__name__)

boto_session = boto3.Session()
s3_client = boto_session.client('s3', region_name=AWS_REGION_NAME)


class ScreenshotWorker(ExternalTask):
    screenshot_dimensions = (
        (375, 667),
        (1024, 768),
        (1280, 800)
    )
    extra_log = None

    @staticmethod
    def _extract_fields(task: ExternalTaskDTO):
        if not task['variables']:
            raise KeyError

        camunda_task_id = task['id']
        task_id = task['variables']['instanceTaskId']['value']
        main_url = task['variables']['mainUrl']['value']

        return camunda_task_id, task_id, main_url

    def _process_task(self, task: ExternalTaskDTO):
        try:
            camunda_task_id, task_id, main_url = self._extract_fields(task)

            self.extra_log = {'camunda_id': camunda_task_id, 'task_id': task_id}
            inject_fields_in_logger(self.extra_log, (log, self.workflow.logger))
        except KeyError:
            log.error("Couln't grab task_id or main url for screenshoter task")
            return

        log.info(f"Got screenshoter task for {main_url}")
        try:
            consumer = S3Consumer(task_id, task_id, s3_client)
            generator = ScreenshotGenerator(main_url, consumer)
            [generator.add_task(width, height) for width, height in self.screenshot_dimensions]
            generator.execute_tasks()

            params = {
                'task_id': camunda_task_id,
                'variables': None
            }
            self.complete(**params)

        except Exception as e:
            log.error(f"Error processing screenshoter task for {main_url}: {e}")
            params = {
                'task_id': camunda_task_id,
                'command': ['bpmnError', 13],
                'errorMessage': 'Some exception occured: {}'.format(e)
            }
            self.bpmnError(**params)

    def screenshoter(self):
        params = {
            'topic': 'screenshotter',
            'lock_duration': '300000',
            'tasks_per_run': '1',
            'variables': 'instanceTaskId,mainUrl'
        }
        tasks = self.fetch(**params)
        for task in tasks:
            self._process_task(task)
            reject_fields_from_logger(self.extra_log, (log, self.workflow.logger))


if __name__ == '__main__':
    args = ExternalTask.cli_args().parse_args(['--topic', 'screenshotter',
                                               '--lock_duration', '300000',
                                               '--tasks_per_run', '1',
                                               '--variables', 'instance_task_id,main_URL'])

    workflow_session = BaseRemoteService(url_prefix=args.workflow)

    workflow = Camunda(url_prefix=workflow_session.url_prefix,
                       logger=logger.initLogging().getLogger(__name__),
                       session=workflow_session.session)

    worker = ScreenshotWorker(workflow, params=args.__dict__)

    worker.fetch_looped(worker.screenshoter)

