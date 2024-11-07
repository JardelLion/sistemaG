"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-baj1r(h=tu6bj4*!k4*umw#@^c+eh!4c1n05=3dscm(7vcv8el'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['sistemag.onrender.com', 'localhost', '127.0.0.1', '[::1]',
                 'http://localhost:3000']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'backend',
    'rest_framework_simplejwt',
    "orders",
    'people',

]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # backend padrão para autenticação de usuários do Django
    'backend.backend.UsernameBackend',  # ou outro backend que você criou
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
         'rest_framework.authentication.SessionAuthentication',  # Para sessões de login
        'rest_framework.authentication.BasicAuthentication',     # Autenticação básica
        'rest_framework.authentication.TokenAuthentication',  
    ),
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
     'django.contrib.auth.middleware.AuthenticationMiddleware',
]

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}


ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'


# accept all requisition
#CORS_ALLOW_ALL_ORIGINS = True

# accept only the port 3000
CORS_ALLOWED_ORIGINS = [
   "https://sistemag.onrender.com",
    'http://localhost:3000',
]

# allow the specific method to use
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS',
    "PATCH",
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
import os


#db host at render
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'sistemag',  # Nome do banco de dados
         'USER': 'lion',  # Nome do usuário
         'PASSWORD': 'UAeEPGWYCaUrSTIDbDS52Lu1xQgChLeC',  # Senha
         'HOST': 'dpg-cs79j3btq21c73cqdbe0-a.oregon-postgres.render.com',  # Host
         'PORT': '5432',  # Porta
     }
}


# database local at localhost
# DATABASES = {
#     'default': {
#         'ENGINE':'django.db.backends.postgresql',
#         'NAME':'sistemag',
#         'USER':'postgres',
#         "PASSWORD":'@jardeljr.7',
#         'HOST':'localhost',
#         'PORT':'5432'
#     }
# }

      


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
