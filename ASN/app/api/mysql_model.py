# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf8')
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from flask import Flask, current_app
import datetime



# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = r'mysql://root:stx11stx11@127.0.0.1/dblp_ref'
# app.config['SQLALCHEMY_BINDS'] = {
#     'paper': r'mysql://root:stx11stx11@127.0.0.1/dblp_ref',
#     'expert': r'mysql://root:stx11stx11@127.0.0.1/expert_example',
# }
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy()


class ASNUser(db.Model, UserMixin):
    __bind_key__ = 'expert'
    __tablename__ = 'user'
    email = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(40))
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    gender = db.Column(db.String(10))
    education = db.Column(db.String(10))
    department = db.Column(db.String(45))
    phone = db.Column(db.String(45))
    address = db.Column(db.String(45))
    avatar = db.Column(db.String(100))
    focus_area = db.Column(db.String(100))
    confirmed = db.Column(db.Boolean)

    def __str__(self):
        return '用户<email:%s, password:%s>' % (self.email, self.password)

    def __init__(self, email="", password="", gender="",
                 education="", department="", phone="",
                 first_name="", last_name="", address="",
                 avatar="../static/avatar/init.png",
                 focus_area="", confirmed=False):
        self.email = email
        self.password = password
        self.gender = gender
        self.education = education
        self.department = department
        self.first_name = first_name
        self.last_name = last_name
        self.department = department
        self.phone = phone
        self.address = address
        self.avatar = avatar
        self.focus_area = focus_area
        self.confirmed = confirmed

    def __repr__(self):
        return '<ASNUser %r>' % self.usernam

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return self.email
        except AttributeError:
            raise NotImplementedError('No `email` attribute - override `get_id`')


class Expert_detail_total(db.Model):
    __bind_key__ = 'ali'
    __tablename__ = 'expert_user_detail'
    id = db.Column(db.String(45),  primary_key=True)
    mid = db.Column(db.String(45))
    name = db.Column(db.String(45))
    name_zh = db.Column(db.String(45))
    position = db.Column(db.String(45))
    phone = db.Column(db.String(45))
    fax = db.Column(db.String(45))

    email = db.Column(db.String(100))
    department = db.Column(db.String(100))
    address = db.Column(db.String(100))
    homepage = db.Column(db.String(100))
    education = db.Column(db.String(100))
    experience = db.Column(db.String(100))
    biography = db.Column(db.String(100))
    avatar = db.Column(db.String(100))

    h_index = db.Column(db.String(10))
    g_index = db.Column(db.String(10))
    gender = db.Column(db.String(5))
    cite_num = db.Column(db.String(10))
    tags = db.Column(db.String(100))
    author_id = db.Column(db.Integer)

    def __str__(self):
        return '作者id<id:%s, 名字：%s>' % (self.id, self.name)

    def __init__(self, id=None, mid=None, name=None, name_zh=None, position=None,
                 phone=None, fax=None, email=None, department=None,
                 address=None, homepage=None, education=None, experience=None,
                 biography=None, avatar = "../static/avatar/files/init.png", h_index=None, g_index=None,
                 gender=None, cite_num=None, tags=None, author_id=None):
        self.id = id
        self.mid = mid
        self.name = name
        self.name_zh = name_zh
        self.position = position
        self.phone = phone
        self.fax = fax
        self.email = email
        self.department = department
        self.address = address
        self.homepage = homepage
        self.education = education
        self.experience = experience
        self.biography = biography
        self.avatar = avatar
        self.h_index = h_index
        self.g_index = g_index
        self.gender = gender
        self.cite_num = cite_num
        self.tags = tags
        self.author_id = author_id


class Expert_detail(db.Model):
    __bind_key__ = 'expert_total'
    __tablename__ = 'expert_detail_total'
    id = db.Column(db.String(45), primary_key=True)
    mid = db.Column(db.String(45))
    department = db.Column(db.String(100))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __str__(self):
        return '专家<id:%s, 名字：%s>' % (self.id, self.name)

    def __init__(self, mid=None, department=None, name=None, email=None):
        self.mid = mid
        self.department = department
        self.name = name
        self.email = email


class Paper_detail(db.Model):

    __bind_key__ = 'paper'
    __tablename__ = 'paper_total'

    id = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    title = db.Column(db.TEXT)
    authors = db.Column(db.TEXT)
    venue = db.Column(db.TEXT)
    year = db.Column(db.Integer)
    ref = db.Column(db.TEXT)
    abtract = db.Column(db.TEXT)

    def __str__(self):
        return '论文<id:%s, title：%s>' % (self.id, self.title)

    def __init__(self, title=None, authors=None, venue=None, year=None, ref=None, abtract=None):
        self.title = title
        self.authors = authors
        self.venue = venue
        self.year = year
        self.ref = ref
        self.abtract = abtract


class Upload_paper(db.Model):

    __bind_key__ = 'expert'
    __tablename__= 'upload_paper'
    user_email = db.Column(db.String(45))
    file_url = db.Column(db.String(45), primary_key=True)
    time = db.Column(db.DateTime)
    file_name = db.Column(db.String(45))

    def __init__(self, user_email=None, file_url=None, time=None, file_name=None):
        self.user_email = user_email
        self.file_url = file_url
        self.time = time
        self.file_name = file_name

    def __str__(self):
        return '上传论文<email:%s, file_url：%s>' % (self.user_email, self.file_url)

    def __repr__(self):
        return '<Upload_paper %r>' % self.user_email
