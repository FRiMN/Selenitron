import boto3
import pytest

from consumers import S3Consumer
from generators import Task
from settings import SCREENSHOT_BUCKET_COMMON, AWS_REGION_NAME

boto_session = boto3.Session()
s3_client = boto_session.client('s3', region_name=AWS_REGION_NAME)


def test_size_label():
    c = S3Consumer(base_file_name='base_name', seomator_task_id=1, client=s3_client)
    task = Task(width=1920, height=1080)
    assert c.get_size_label(task) == '1920x1080'


def test_default_bucket():
    c = S3Consumer(base_file_name='base_name', seomator_task_id=1, client=s3_client)
    task = Task(width=0, height=0)
    assert c.get_bucket(task) == SCREENSHOT_BUCKET_COMMON


def test_default_remote_path():
    c = S3Consumer(base_file_name='base_name', seomator_task_id=1, client=s3_client)
    task = Task(width=0, height=0)
    assert c.get_remote_path(task) == f"scr/1/base_name.jpg"


def test_none_init():
    with pytest.raises(TypeError, match='required positional arguments'):
        S3Consumer()
