from unittest.mock import patch

import pytest

import logger
import task_worker
from generators import Task
from infrastructure.dto import ExternalTaskDTO
from infrastructure.service import BaseRemoteService, Camunda
from infrastructure.service.camunda_external_task import ExternalTask

camunda_task = ExternalTaskDTO(
    **{'activityId': 'ScreenshotterExternalTask',
       'activityInstanceId': 'ScreenshotterExternalTask:19defb34-13c9-11eb-99c2-0242ac170003',
       'errorMessage': None, 'errorDetails': None,
       'executionId': '19defb33-13c9-11eb-99c2-0242ac170003',
       'id': '19df9775-13c9-11eb-99c2-0242ac170003',
       'lockExpirationTime': '2020-10-21T13:15:25.296+0000',
       'processDefinitionId': 'internal_Screenshotter:1:024b11a7-13be-11eb-99c2-0242ac170003',
       'processDefinitionKey': 'internal_Screenshotter',
       'processInstanceId': '19d8e0ab-13c9-11eb-99c2-0242ac170003', 'tenantId': None,
       'retries': None,
       'workerId': '68f837120f18', 'priority': 0, 'topicName': 'screenshotter',
       'variables': {
           'mainUrl': {'type': 'String', 'value': 'http://seomator.com', 'valueInfo': {}},
           'instanceTaskId': {'type': 'Long', 'value': 19395, 'valueInfo': {}}}}
)

args = ExternalTask.cli_args().parse_args(['--topic', 'screenshotter',
                                           '--lock_duration', '300000',
                                           '--tasks_per_run', '1',
                                           '--variables', 'instance_task_id,main_URL'])
workflow_session = BaseRemoteService(url_prefix=args.workflow)

workflow = Camunda(url_prefix=workflow_session.url_prefix,
                   logger=logger.initLogging().getLogger(__name__),
                   session=workflow_session.session)
worker = task_worker.ScreenshotWorker(workflow, params=args.__dict__)

task = Task(0, 0)


def test_complete():
    with patch.object(task_worker.ScreenshotGenerator, 'execute_tasks') as mocked_execute_tasks, \
            patch.object(task_worker.ScreenshotWorker, 'complete') as mocked_complete:

        mocked_execute_tasks.return_value = [task]

        worker._process_task(camunda_task)

        assert mocked_execute_tasks.call_count == 1
        assert mocked_complete.call_count == 1

        params = {
            'task_id': '19df9775-13c9-11eb-99c2-0242ac170003',
            'variables': None
        }
        mocked_complete.assert_called_with(**params)


def test_error():
    with patch.object(task_worker.ScreenshotGenerator, 'generate') as mocked_generate, \
            patch.object(task_worker.ScreenshotWorker, 'bpmnError') as mocked_bpmnError:

        mocked_generate.side_effect = Exception('test_exception')

        worker._process_task(camunda_task)

        assert mocked_generate.call_count == 3
        assert mocked_bpmnError.call_count == 1

        params = {
            'task_id': '19df9775-13c9-11eb-99c2-0242ac170003',
            'command': ['bpmnError', 13],
            'errorMessage': 'Some exception occured: test_exception'
        }
        mocked_bpmnError.assert_called_with(**params)


def test_task_key_error():
    task = ExternalTaskDTO()

    with pytest.raises(KeyError):
        worker._extract_fields(task)

    worker._process_task(task)
