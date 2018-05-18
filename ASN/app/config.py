# coding=utf-8
import os
from flask_uploads import DOCUMENTS


class Config:

    DEBUG = True  # debug 模式下网页不会缓存

    SECRET_KEY = '1frMFuWRVPV1'
    SECURITY_PASSWORD_SALT = 'my_precious_two'

    # MySql
    SQLALCHEMY_DATABASE_URI = "mysql://%s:%s@%s/%s" % ('root', 'stx11stx11', '127.0.0.1', 'dblp_ref')
    SQLALCHEMY_BINDS = {
        # 'paper':    r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',

        # 'expert':   r'mysql://root:stx11stx11@127.0.0.1/expert_example',

        'ali':      r'mysql://root:123456@47.106.157.16/citation',
        }

    # Mongo
    MONGO_HOST = '110.64.66.221'
    # MONGO_HOST = '47.106.157.16'
    # MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    MONGO_USERNAME = ''
    MONGO_PASSWORD = ''
    MONGO_CONNECT = False
    MONGO_DBNAME = 'Paper'
    # MONGO_AUTHORS_DBNAME = 'Co_authors'

    # 默认存储路径配置
    UPLOADS_DEFAULT_DEST = './app/static/paper'
    UPLOADS_DEFAULT_URL = '../static/paper'

    # 图片存储路径配置
    UPLOADED_PHOTOS_DEST = './app/static/avatar/'
    UPLOADED_PHOTOS_URL = '../static/avatar/'

    # 文件存储路径配置
    UPLOADED_PAPERS_DEST = './app/static/paper/'
    UPLOADED_PAPERS_URL = '../static/paper/'
    UPLOADED_PAPERS_ALLOW = set(['txt', 'pdf', 'doc', 'docx'])

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    # FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    # email server
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'stx17@163.com'
    MAIL_PASSWORD = '2860533'

    # administrator list
    ADMINS = ['your-gmail-username@gmail.com']

    # mail accounts
    MAIL_DEFAULT_SENDER = 'stx17@163.com'

    @staticmethod
    # 此注释可表明使用类名可以直接调用该方法
    def init_app(app):
        # 执行当前需要的环境的初始化
        pass