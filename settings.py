import os

WORKFLOW = os.getenv("WORKFLOW", "http://demo:demo@camunda:8090")

LOG_HANDLERS = os.getenv("LOG_HANDLERS", 'console').split(",")

LOGSTASH = os.getenv("LOGSTASH", "seomator-elk")

# LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")

SCREENSHOT_BUCKET_S3 = os.getenv('SCREENSHOT_BUCKET_S3', 'seomator-screenshots-beta')

# SCREENSHOTER SETTINGS
AWS_REGION_NAME = os.getenv('AWS_REGION_NAME', 'us-west-1')
SCREENSHOT_BUCKET_MOBILE = os.getenv('SCREENSHOT_BUCKET_MOBILE', 'seomator-mobile')
SCREENSHOT_BUCKET_TABLET = os.getenv('SCREENSHOT_BUCKET_TABLET', 'seomator-screenshots')
SCREENSHOT_BUCKET_COMMON = os.getenv('SCREENSHOT_BUCKET_COMMON', 'seomator-screenshots')
