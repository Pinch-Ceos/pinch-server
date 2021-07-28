import os
from .base import *

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'secrets_dev.json'), 'rb') as secret_file:
    secrets = json.load(secret_file)

DEBUG = True

ALLOWED_HOSTS = ['*']


DATABASES = secrets['DB_SETTINGS']
