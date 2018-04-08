# coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s" % ('root', '123456', '127.0.0.1', 'baike')
db = SQLAlchemy(app)
import datetime

#db = SQLAlchemy()

class User(db.Model, UserMixin):

    __tablenanme__= 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(40))

    def __str__(self):
        return '用户<id:%s, 姓名:%s>' % (self.id, self.name)

    def __init__(self, name = None, password = None ):
        self.name = name
        self.password = password

class Lemma(db.Model):

    __tablenanme__= 'lemma'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    content = db.Column(db.Text)
    comments = db.relationship('Comment', backref='lemmas', lazy='dynamic')

    def __str__(self):
        return '词条<title:%s, contet:%s>' % (self.title, self.content)

    def __init__(self, title = None, content = None ):
        self.title = title
        self.content =content

class Comment(db.Model):

    __tablenanme__= 'comment'
    id = db.Column(db.Integer, primary_key=True)
    #user_name = db.Column(db.String(30), db.ForeignKey('User.name'))
    user_name = db.Column(db.String(30))
    lemma_id = db.Column(db.Integer, db.ForeignKey('lemma.id'))
    #title = db.Column(db.String(40))
    content = db.Column(db.String(320))
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        return '评论<%s>' % (self.title)

    def __init__(self, user_name = None, lemma_title = None, content = None ):
        self.user_name = current_user
        self.lemma_title = lemma_title
        self.content = content
        self.time = datetime.now()
