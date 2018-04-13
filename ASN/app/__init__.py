# coding=utf-8
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_login import login_required, current_user
from flask_pymongo import PyMongo

from app.route.user import user
from app.api import api
from app.api.model import db, User
from app.api.mysql_model import ASNUser, Expert_detail_total
# 由于无法从 __init__.py (此文件)导入 mongo 到 user.py , 所以沿用 mongodb_model 中 mongo
from app.api.mongodb_model import mongo
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
import json
import os
# app = Flask("Paper", template_folder=r'C:\Users\hphp\Desktop\graduation_design\chujq-baike-master\baike-master\app\templates')
app = Flask(__name__)
app.secret_key = '1frMFuWRVPV1'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s" % ('root', 'stx11stx11', '127.0.0.1', 'dblp_ref')
app.config['SQLALCHEMY_BINDS'] = {
    'paper':    r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',
    'expert':   r'mysql://root:stx11stx11@127.0.0.1/expert_example',
    # 'expert_detail_total':  r'mysql://root:stx11stx11@127.0.0.1/expert_detail_total'

}
db.init_app(app)

#mongodb 配置
# app.config['MONGO3_HOST'] = '127.0.0.1'
# app.config['MONGO3_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'Paper'
app.config['MONGO_AUTHORS_DBNAME'] = 'Co_authors'

# mongo = PyMongo(app, config_prefix='MONGO3')
# mongo = PyMongo(app)
mongo.init_app(app)

login_manager = LoginManager()
login_manager.login_view = '.login'
login_manager.login_message = '请登录'
login_manager.init_app(app)

# app.config['UPLOADS_DEFAULT_DEST'] = os.getcwd() + '\\app\\avatar'

app.config['UPLOADS_DEFAULT_DEST'] = './app/static/avatar'
app.config['UPLOADS_DEFAULT_URL'] = '../static/avatar'

app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(api, url_prefix='/api')

@login_manager.user_loader
def load_user(email):
    # print "ASNUser load_user: ", ASNUser.query.get(email)
    print "db load_user: ", db.session.query(ASNUser).filter(ASNUser.email==email).first()
    return db.session.query(ASNUser).filter(ASNUser.email==email).first()

@app.route('/')
def home():
    status = {"loginStatus": False,
              "logoutStatus": True}
    return render_template('home.html', Status=status)
