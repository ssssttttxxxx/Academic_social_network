# coding=utf-8
import os



class Config:

    DEBUG = True  # debug 模式下网页不会缓存

    SECRET_KEY = '1frMFuWRVPV1'

    # MySql
    SQLALCHEMY_DATABASE_URI = "mysql://%s:%s@%s/%s" % ('root', 'stx11stx11', '127.0.0.1', 'dblp_ref')
    SQLALCHEMY_BINDS = {
        'paper':    r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',
        'expert':   r'mysql://root:stx11stx11@127.0.0.1/expert_example',
        }

    # Mongo
    MONGO_DBNAME = 'Paper'
    MONGO_AUTHORS_DBNAME = 'Co_authors'

    # 默认存储路径配置
    UPLOADS_DEFAULT_DEST = './app/static/avatar'
    UPLOADS_DEFAULT_URL = '../static/avatar'

    # 图片存储路径配置
    UPLOADED_PHOTOS_DEST = './app/static/avatar/'
    UPLOADED_PHOTOS_URL = '../static/avatar/'

    # 文件存储路径配置
    UPLOADED_FILES_DEST ='./app/static/paper'
    UPLOADS_FILES_URL = '../static/paper'


    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')


    @staticmethod
    # 此注释可表明使用类名可以直接调用该方法
    def init_app(app):
        # 执行当前需要的环境的初始化
        pass