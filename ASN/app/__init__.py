# coding=utf-8
from flask import Flask, render_template, request, session, logging, g
from flask_login import LoginManager
from flask_login import login_required, current_user
from flask_pymongo import PyMongo
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class, DOCUMENTS
from flask_mail import Mail

from route.user import user
from api.app_api import api, login_manager
from datetime import timedelta
# from app.api.model import db, User

from api.mysql_model import ASNUser, Expert_detail_total
from api.mysql_model import db
from api.app_api import photos, papers, mail, mongo
# from api.mongodb_model import mongo

from config import Config

import os


app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(api, url_prefix='/api')

mail.init_app(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=5)
    session.modified = True


app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'
# app.secret_key = '1frMFuWRVPV1'
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s" % ('root', 'stx11stx11', '127.0.0.1', 'dblp_ref')
# app.config['SQLALCHEMY_BINDS'] = {
#     'paper':    r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',
#     'expert':   r'mysql://root:stx11stx11@127.0.0.1/expert_example',
#
# }
db.init_app(app)

#mongodb 配置

# app.config['MONGO_HOST'] = '47.106.157.16'
# app.config['MONGO_PORT'] = 27017
# app.config['MONGO_DBNAME'] = 'Paper'
mongo.init_app(app, config_prefix='MONGO')

# login_manager = LoginManager()
# login_manager.login_view = 'user.login'
# login_manager.login_message = '请登录'
login_manager.init_app(app)

# app.config['UPLOADS_DEFAULT_DEST'] = os.getcwd() + '\\app\\avatar'

# 默认存储路径配置
# app.config['UPLOADS_DEFAULT_DEST'] = './app/static/avatar'
# app.config['UPLOADS_DEFAULT_URL'] = '../static/avatar'

# # 图片存储路径配置
# app.config['UPLOADED_PHOTOS_DEST'] = './app/static/avatar/'
# app.config['UPLOADED_PHOTOS_URL'] = '../static/avatar/'
#
# # 文件存储路径配置
# app.config['UPLOADED_PAPERS_DEST '] ='./app/static/paper/'
# app.config['UPLOADED_PAPERS_URL'] = '../static/paper/'
# app.config['UPLOADED_PAPERS_ALLOW'] = DOCUMENTS
# 注册
# photos = UploadSet('PHOTOS', IMAGES)
# configure_uploads(app, photos)
# patch_request_class(app)
#
# files = UploadSet('FILES')
configure_uploads(app, (photos, papers))
patch_request_class(app)


# @login_manager.user_loader
# def load_user(email):
#     # print "ASNUser load_user: ", ASNUser.query.get(email)
#     print "db load_user: ", db.session.query(ASNUser).filter(ASNUser.email==email).first()
#     return db.session.query(ASNUser).filter(ASNUser.email==email).first()

@app.route('/')
def home():
    status = {"loginStatus": False,
              "logoutStatus": True}
    return render_template('home.html', Status=status)
