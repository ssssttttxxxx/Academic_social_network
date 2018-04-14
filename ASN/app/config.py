# coding=utf-8
import os



class Config:
    SECRET_KEY = '1frMFuWRVPV1'
    SQLALCHEMY_DATABASE_URI = "mysql://%s:%s@%s/%s" % ('root', 'stx11stx11', '127.0.0.1', 'dblp_ref')
    SQLALCHEMY_BINDS = {
        'paper':    r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',
        'expert':   r'mysql://root:stx11stx11@127.0.0.1/expert_example',
        }
    MONGO_DBNAME = 'Paper'
    MONGO_AUTHORS_DBNAME = 'Co_authors'
    UPLOADED_PHOTOS_DEST = './app/static/avatar/'
    UPLOADED_PHOTOS_URL = '../static/avatar/'

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')


    @staticmethod
    # 此注释可表明使用类名可以直接调用该方法
    def init_app(app):
        # 执行当前需要的环境的初始化
        pass