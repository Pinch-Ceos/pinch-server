import os
from .base import *

DEBUG = False  # 꼭 필요합니다.

ALLOWED_HOSTS = [
    '127.0.0.1',
    '.ap-northeast-2.compute.amazonaws.com',
]

DATABASES = secrets['DB_SETTINGS']
