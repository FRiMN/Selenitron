from typing import Union, Optional

from infrastructure.dto import ExternalTaskDTO
from infrastructure.exceptions import CamundaException


class Camunda:

    def __init__(self, url_prefix, logger, session):
        self.url_prefix = url_prefix
        self.logger = logger
        self.session = session

    def get_tasks_for_topic(self, topic: str) -> Union[ExternalTaskDTO, list]:
        """
        Queries for the external tasks that fulfill given parameters. Parameters may be static as well as dynamic
        runtime properties of executions. The size of the result set can be retrieved by using the Get External
        Task Count method.
        https://docs.camunda.org/manual/7.7/reference/rest/external-task/get-query/
        :param topic:
        :return:
        """

        url = "{api_host}/engine-rest/external-task?topicName={topic}".format(
            api_host=self.url_prefix, topic=topic)

        self.logger.debug('getting the task list from camunda, url: %r' % (url))

        resp = self.session.get(url)

        if resp.status_code != 200:
            raise CamundaException(
                "Camunda can't return task data, details: {}".format(resp.text))

        return [ExternalTaskDTO(**j) for j in resp.json()]

    def get_tasks_count(self, topic: str) -> int:
        """
        Queries for the number of external tasks that fulfill given parameters. Takes the same parameters as the Get External Tasks method.
        https://docs.camunda.org/manual/latest/reference/rest/external-task/get-query-count/
        :param topic:
        :return:
        """

        url = "{api_host}/engine-rest/external-task/count?topicName={topic}".format(
            api_host=self.url_prefix, topic=topic)

        self.logger.debug('getting the task count from camunda, url: %r' % (url))

        resp = self.session.get(url)

        if resp.status_code != 200:
            raise CamundaException(
                "Camunda can't return tasks count data, details: {}".format(resp.text))

        return resp.json()["count"]

    def lock(self, worker_id: str, topic: str, maxtasks: int = 1,
             lockduration: int = 10000, variables: Optional[list] = None) -> Union[ExternalTaskDTO, list]:
        """
        Fetches and locks a specific number of external tasks for execution by a worker. Query can be restricted
        to specific task topics and for each task topic an individual lock time can be provided.
        https://docs.camunda.org/manual/7.7/reference/rest/external-task/fetch/
        :param worker_id:
        :param topic:
        :param maxtasks:
        :param lockduration:
        :param variables:
        :return:
        """

        if variables is None:
            variables = []

        url = "{api_host}/engine-rest/external-task/fetchAndLock".format(
            api_host=self.url_prefix)
        payload = {"workerId": worker_id,
                   "maxTasks": maxtasks,
                   "usePriority": True,
                   "topics": [{"topicName": topic,
                               "lockDuration": lockduration,
                               "variables": variables
                               }]
                   }

        self.logger.debug('locking the task in camunda, url: %r, topicName: %s, lockDuration: %s' % (url, topic, lockduration))

        resp = self.session.post(url, json=payload)

        if resp.status_code != 200:
            raise CamundaException(
                "Camunda can't return task data, details: {}".format(resp.text))

        return [ExternalTaskDTO(**j) for j in resp.json()]

    def complete(self, worker_id: str, task_id: str, variables: dict = None) -> bool:
        """
        Completes an external task by id and updates process variables.
        https://docs.camunda.org/manual/7.7/reference/rest/external-task/post-complete/
        :param worker_id:
        :param task_id:
        :param variables:
        :return:
        """
        if variables is None:
            variables = {}

        url = "{api_host}/engine-rest/external-task/{task_id}/complete".format(
            api_host=self.url_prefix, task_id=task_id)
        payload = {"workerId": worker_id,
                   "variables": variables
                   }
        self.logger.debug('completing the external task in camunda, url: %r, worker_id: %s' % (url, worker_id))

        resp = self.session.post(url, json=payload)

        if resp.status_code != 204:
            self.errorhandler(resp)

        return True

    def unlock(self, task_id: str) -> bool:
        """
        Unlocks an external task by id. Clears the task’s lock expiration time and worker id.
        https://docs.camunda.org/manual/7.6/reference/rest/external-task/post-unlock/
        :param task_id:
        :return:
        """

        url = "{api_host}/engine-rest/external-task/{task_id}/unlock".format(
            api_host=self.url_prefix, task_id=task_id)

        self.logger.debug(
            'unlocking the external task in camunda, url: %r' % url)

        resp = self.session.post(url)

        if resp.status_code != 204:
            self.errorhandler(resp)

        return True

    def extend_duration(self, task_id: str, worker_id: str, duration: int) -> bool:
        """
        Extends the timeout of the lock by a given amount of time.
        https://docs.camunda.org/manual/7.13/reference/rest/external-task/post-extend-lock/
        :param task_id:
        :return:
        """

        url = "{api_host}/engine-rest/external-task/{task_id}/extendLock".format(
            api_host=self.url_prefix, task_id=task_id)

        self.logger.debug(
            'extending lock the external task in camunda, url: %r' % url)

        payload = {
            "workerId": worker_id,
            "newDuration": duration
        }

        resp = self.session.post(url, json=payload)

        if resp.status_code != 204:
            self.errorhandler(resp)

        return True

    def failure(self, worker_id: str, task_id: str, errormessage: str, errordetails: str, retries=3,
                retrytimeout=10000) -> bool:
        """
        Reports a failure to execute an external task by id. A number of retries and a
        timeout until the task can be retried can be specified.
        If retries are set to 0, an incident for this task is created.
        https://docs.camunda.org/manual/7.7/reference/rest/external-task/post-failure/
        :param worker_id:
        :param task_id:
        :param errormessage:
        :param errordetails:
        :param retries:
        :param retrytimeout:
        :return:
        """

        url = "{api_host}/engine-rest/external-task/{task_id}/failure".format(api_host=self.url_prefix,
                                                                              task_id=task_id)
        payload = {"workerId": worker_id,
                   "errorMessage": errormessage,
                   "errorDetails": errordetails,
                   "retries": retries,
                   "retryTimeout": retrytimeout
                   }

        self.logger.debug(
            'Sending the failure to camunda, url: %r, worker_id: %s,'
            ' errormessage: %s, retries: %s, retrytimeout: %s' % (url, worker_id, errormessage, retries, retrytimeout))

        resp = self.session.post(url, json=payload)

        if resp.status_code != 204:
            self.errorhandler(resp)

        return True

    def bpmnError(self, worker_id: str, task_id: str, errorcode: int, errorMessage: str = "Processing Error", variables: Optional[dict] = None) -> bool:
        """
        Reports a business error in the context of a running external task by id.
        The error code must be specified to identify the BPMN error handler.
        https://docs.camunda.org/manual/7.7/reference/rest/external-task/post-bpmn-error/
        :param worker_id:
        :param task_id:
        :param errorcode:
        :return:
        """

        url = "{api_host}/engine-rest/external-task/{task_id}/bpmnError".format(api_host=self.url_prefix,
                                                                                task_id=task_id)
        if variables is None:
            variables = {}

        payload = {"workerId": worker_id,
                   "errorCode": errorcode,
                   "errorMessage": errorMessage,
                   "variables": variables
                   }

        self.logger.debug(
            'Sending the bpmnError to camunda, url: %r, worker_id: %s, errorcode: %s' % (url, worker_id, errorcode))

        resp = self.session.post(url, json=payload)

        if resp.status_code != 204:
            self.errorhandler(resp)

        return True

    def put_process_variable(self, process_instance_id: str, var_name: str, payload: str) -> bool:
        """
        Sets a variable of a given process instance by id.

        https://docs.camunda.org/manual/7.7/reference/rest/process-instance/variables/put-variable/
        """

        url = "{api_host}/engine-rest/process-instance/{id}/variables/{varName}".format(
            api_host=self.url_prefix, id=process_instance_id, varName=var_name)

        self.logger.debug('Updating variable {} in camunda {}'.format(var_name, payload))

        resp = self.session.put(url, json=payload)

        if resp.status_code != 204:
            raise CamundaException(
                "Camunda can't update variable, details: {}".format(resp.text))

        return True

    def errorhandler(self, resp):
        if resp.status_code == 400:
            raise CamundaException("Task's most recent lock was not acquired "
                                   "by the provided worker, details: {}".format(resp.text))
        elif resp.status_code == 404:
            raise CamundaException("Task does not exist. This could indicate a wrong "
                                   "task id as well as a cancelled task, e.g., due to "
                                   "a caught BPMN boundary event, details: {}".format(resp.text))
        elif resp.status_code == 500:
            raise CamundaException("Corresponding process instance could not be resumed "
                                   "successfully, details: {}".format(resp.text))
        else:
            raise CamundaException(
                "Camunda can't post the data, details: {}".format(resp.text))
