"""
Django settings for chatbot project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import logging
import sentry_sdk
import boto3
import socket
from boto3.session import Session


hostname = socket.gethostname()

if 'd2v-silvasstarmbp' in hostname.lower():
    environment = 'dev'
    print("Running on local machine")
    DEBUG = True
    NGROK = True
else:
    environment = 'prod'
    print("Running on production server")
    DEBUG = False


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

if environment == "dev":
    dotenv_path = BASE_DIR / '.env'
    AWS_LOG_GROUP = "Chat4Heart"
    AWS_LOG_STREAM = "Chat4Heart-StridePilotTestingStream-dev"
    AWS_LOGGER_NAME = 'Chat4Heart-watchtower-logger-StridePilotTesting-dev'
else:
    dotenv_path = BASE_DIR.parent / '.env'
    AWS_LOG_GROUP = "Chat4Heart"
    AWS_LOG_STREAM = "StridePilotTestingStream-prod"
    AWS_LOGGER_NAME = 'watchtower-logger-StridePilotTesting-prod'

# Load the .env file
load_dotenv(dotenv_path=dotenv_path)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_KMS_ARN = os.getenv('AWS_KMS_ARN')
AWS_REGION_NAME = os.getenv('AWS_REGION_NAME', 'us-east-1')

WELCOME_MESSAGE_CONTROL = "Your healthcare provider is sending you three messages each week for the next 2 months to help you manage your health. Look for them every Monday, Wednesday and Friday starting next week."
WELCOME_MESSAGE_CONTROL_ES = "Su proveedor de atención médica le enviará tres mensajes cada semana durante los próximos 2 meses para ayudarlo a controlar su salud. Búscalos todos los lunes, miércoles y viernes a partir de la próxima semana."
WELCOME_MESSAGE="Denver Health welcomes you to Chat 4 Heart Health! Starting Monday, we'll send you 4-5 messages each week for 2 months about things like healthy eating, physical activity & getting a good night's sleep. You will be able ask me questions anytime, day or night and working with me could help you stay healthy. Anything you ask me is kept private. If you prefer messages in Spanish, text '1' here; Si prefieres mensajes en español, envía el mensaje '1' aquí. To start, please click on the link here to complete this 5 minute survey about your health--we will send you $5 when it is completed. If you have already taken the survey, you don't need to do this--thank you!"
WELCOME_MESSAGE_ES="¡Denver Health le da la bienvenida a Chat 4 Heart Health! A partir de Lunes, le enviaremos de 4 a 5 mensajes cada semana durante 2 meses sobre aspectos como alimentación saludable, actividad física y sueño reparador. Podrás hacerme preguntas en cualquier momento, de día o de noche, y trabajar conmigo podría ayudarte a mantenerte saludable. Todo lo que me preguntes se mantendrá privado. Para comenzar, haga clic en el enlace aquí para completar esta encuesta de 5 minutos sobre su salud. Le enviaremos $5 cuando la complete. Si ya ha realizado la encuesta, no es necesario que la haga. ¡Gracias!"
FINAL_MESSAGE_CONTROL = "Thank you for participating in the Chat for Heart Health study! Please take a moment to complete this survey about your healthy behaviors. It should take you 5 minutes to complete and we will send you $5 when you do."
FINAL_MESSAGE_CONTROL_ES = "¡Gracias por participar en el estudio Chat for Heart Health! Tómese un momento para completar esta encuesta sobre sus comportamientos saludables. Debería llevarle 5 minutos completarlo y le enviaremos $5 cuando lo haga."
FINAL_MESSAGE = "Thank you for participating in the Chat for Heart Health study! We will no longer send you messages, but please feel free to ask us questions about your heart health any time! Please take a moment to complete this survey about your healthy behaviors. It should take you 5 minutes to complete and we will send you $5 when you do."
FINAL_MESSAGE_ES = "¡Gracias por participar en el estudio Chat for Heart Health! Ya no le enviaremos mensajes, pero no dude en hacernos preguntas sobre la salud de su corazón en cualquier momento. Tómese un momento para completar esta encuesta sobre sus comportamientos saludables. Debería llevarle 5 minutos completarlo y le enviaremos $5 cuando lo haga."
print("WELCOME_MESSAGE: ", WELCOME_MESSAGE)
print("WELCOME_MESSAGE_ES: ", WELCOME_MESSAGE_ES)

#disable registration
REGISTRATION_OPEN = False


logger_boto3_client = boto3.client(
    "logs",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME,
)

# Choose the DSN based on the environment
if environment != "dev":
    dsn = "https://14488fb05ca96dc073a7ef56ab2c36ea@o4505835707957248.ingest.sentry.io/4506791275003904"
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY','django-insecure-mned9+=7!iw3=ly33w_b-fd3g%gja9iy(jb6g%0nrse$5jth$3')

# SECURITY WARNING: don't run with debug turned on in production!

CORS_ORIGIN_ALLOW_ALL = True

ALLOWED_HOSTS = [
'localhost','3.211.47.166','dh-c4h.clinicchat.com','127.0.0.1','ec2-3-211-47-166.compute-1.amazonaws.com'
]


# Application definition

INSTALLED_APPS = [

    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'base.apps.BaseConfig',
    'import_export',
    'customLogs',
    'django_extensions',
    'rangefilter',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # corsheaders
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]


ROOT_URLCONF = 'chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if environment == "dev":
    POSTGRES_HOST = 'localhost'
    POSTGRES_PORT = '5432'
    POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME_DEV', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD_DEV', None)

else:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = '5434'
    POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_DATABASE', None),
        'USER': POSTGRES_USERNAME,
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
    }
}


ADMINS = [
    # ('Joshua Silvasstar', 'joshva.silvasstar@clinicchat.com'),
    ('Joshua Silvasstar', 'joshva.silvasstar@ucdenver.edu'),
    # ('Admin Name 2', 'admin2@example.com'),
]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Denver'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR,'static')
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

IMPORT_EXPORT_USE_TRANSACTIONS = True

FREQUENCY_PER_TOPC = os.getenv('FREQUENCY_PER_TOPC', None)

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

CRISPY_TEMPLATE_PACK = 'bootstrap5'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# store images
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Use Gmail as the email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Replace with your Gmail email address
EMAIL_HOST_USER = os.getenv('GOOGLE_EMAIL', None)
# Replace with your Gmail app password (not your account password)
EMAIL_HOST_PASSWORD = os.getenv('GOOGLE_PASSWORD', None)

# Sender email address
# Replace with your Gmail email address
DEFAULT_FROM_EMAIL = os.getenv('GOOGLE_EMAIL', None)
DEFAULT_TO_EMAIL = [
                    # 'joshva.silvasstar@clinicchat.com',
                    'joshva.silvasstar@ucdenver.edu'
                    ]

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug.log')
HANDLER_OPTIONS = ['console', 'file', 
                   'db_log',
                #    'watchtower',
                   ]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'filters': {
        'ignore_urls': {
            '()': 'base.filters.IgnoreUrls',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['ignore_urls'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'maxBytes': 1024 * 1024 * 100,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'filters': ['ignore_urls'],
        },
        'db_log': {
            'level': 'DEBUG',
            'class': 'customLogs.db_log_handler.DatabaseLogHandler',
            'filters': ['ignore_urls'],
        },
        'watchtower': {
            "level": "INFO",
            "class": "watchtower.CloudWatchLogHandler",
            "boto3_client": logger_boto3_client,
            "log_group": AWS_LOG_GROUP,
            # Different stream for each environment
            "stream_name": AWS_LOG_STREAM,
            "formatter": "verbose",
            'filters': ['ignore_urls'],
        },

    },
    'root': {
        'handlers': HANDLER_OPTIONS,
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        'filters': ['ignore_urls'],
    },
    'loggers': {
        'django': {
            'handlers': HANDLER_OPTIONS,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
            'filters': ['ignore_urls'],
        },
    },
}


# SCHEDULER_CONFIG = {
#     "apscheduler.jobstores.default": {
#         "class": "django_apscheduler.jobstores:DjangoJobStore"
#     },
#     'apscheduler.executors.processpool': {
#         "type": "threadpool"
#     },
# }
# SCHEDULER_AUTOSTART = True
# SCHEDULER_SETTING = os.environ.get('SCHEDULER_SETTING')

# WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE', None)
OPT_IN_MESSAGE = os.getenv('OPT_IN_MESSAGE', None)
OPT_IN_MESSAGE_ES = os.getenv('OPT_IN_MESSAGE_ES', None)
# WELCOME_MESSAGE_ES = os.getenv('WELCOME_MESSAGE_ES', None)
TOTAL_TOPICS = os.getenv('TOTAL_TOPICS', 9)

SCHEDULE_MESSAGE_HOUR = os.getenv('SCHEDULE_MESSAGE_HOUR', 8)
SCHEDULE_MESSAGE_MINUTE = os.getenv('SCHEDULE_MESSAGE_MINUTE', 0)

TOPIC_SELECTOR_DAY_NUMBER = os.getenv('TOPIC_SELECTOR_DAY_NUMBER', 5)

TARGET_ARM_NAME = os.getenv('TARGET_ARM_NAME', 'test')

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
VONAGE_KEY=os.getenv('VONAGE_KEY', None)
VONAGE_SECRET=os.getenv('VONAGE_SECRET', None)
VONAGE_NUMBER=os.getenv('VONAGE_NUMBER','18334298629')
print("VONAGE_NUMBER: ", VONAGE_NUMBER)

WATSON_API_KEY = os.getenv('WATSON_API_KEY')
WATSON_ASSISTANT_ID = os.getenv('WATSON_ASSISTANT_ID')
WATSON_URL = f'https://api.us-south.assistant.watson.cloud.ibm.com/v2/assistants/{WATSON_ASSISTANT_ID}/sessions'

# Load IBM Language Translator API key and service URL from environment variables
IBM_LANGUAGE_TRANSLATOR_API = os.getenv('IBM_LANGUAGE_TRANSLATOR_API')
IBM_LANGUAGE_TRANSLATOR_URL = os.getenv('IBM_LANGUAGE_TRANSLATOR_URL')


import re

IGNORABLE_404_URLS = [
    re.compile(r"^/apple-touch-icon.*\.png$"),
    re.compile(r"^/favicon\.ico$"),
    re.compile(r"^/robots\.txt$"),
]

AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY')

EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'


############################ Celery ############################
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'America/Denver'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

JOSH_NUMBER = os.getenv('JOSH_NUMBER', None)