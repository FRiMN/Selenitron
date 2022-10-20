from io import BytesIO

import botocore

from generators import Task
from settings import SCREENSHOT_BUCKET_MOBILE, SCREENSHOT_BUCKET_COMMON


class Consumer:
    """ Interface for consumers """
    def execute_task(self, task: Task):
        raise NotImplementedError


class StreamConsumer(Consumer):
    """ Simple consumer, just return result of generator task data """
    def execute_task(self, task):
        return task.data


class S3Consumer(Consumer):
    """ AWS S3 consumer for screenshots """
    size_buckets = {'375x667': SCREENSHOT_BUCKET_MOBILE,
                    '1024x768': SCREENSHOT_BUCKET_COMMON,
                    '1280x800': SCREENSHOT_BUCKET_COMMON}

    size_file_names = {
        '375x667': 'main_1',
        '1024x768': 'main_4'
    }

    def __init__(self, base_file_name: str, seomator_task_id: int, client: 'botocore.client.S3'):
        self.seomator_task_id = seomator_task_id
        self.base_file_name = base_file_name
        self.s3_client = client

    @staticmethod
    def get_size_label(task: Task):
        return f"{task.width}x{task.height}"

    def get_bucket(self, task: Task):
        label = self.get_size_label(task)
        return self.size_buckets.get(label, SCREENSHOT_BUCKET_COMMON)

    def get_remote_path(self, task: Task):
        label = self.get_size_label(task)
        file_name = self.size_file_names.get(label, self.base_file_name)
        return f"scr/{self.seomator_task_id}/{file_name}.jpg"

    def execute_task(self, task):
        bucket = self.get_bucket(task)
        path = self.get_remote_path(task)
        f_bytes = BytesIO(task.data)
        self.s3_client.upload_fileobj(f_bytes, bucket, path)
