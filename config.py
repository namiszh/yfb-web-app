# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""
import os
from app import app


ENV='production'
DEBUG=None

SECRET_KEY = 'you-will-never-guess-hahahahaha-jdsf90asufwkjfcjsofusfchjs9027urhjwofj'


# project root directory
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
app.logger.debug('project Root {}'.format(PROJECT_ROOT))
# # data directory
# DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'data'))

# # web application directory
# WEB_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'app'))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(PROJECT_ROOT, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_MIGRATE_REPO = os.path.join(PROJECT_ROOT, 'db_repository')

CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, 'credentials')
app.logger.debug('credential file {}'.format(CREDENTIALS_FILE))

# This font file is used to support Chinese in chart
CHINESE_FONT_FILE = os.path.join(PROJECT_ROOT, 'static/fonts/SimSun-01.ttf')
app.logger.debug('Chinese font file {}'.format(CHINESE_FONT_FILE))
# app.logger.debug(CHINESE_FONT_FILE)




