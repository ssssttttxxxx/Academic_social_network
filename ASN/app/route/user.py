# coding=utf-8
import sys

sys.path.append("..")
from flask import render_template, Blueprint, redirect, url_for, request, session, current_app, flash
from flask_login import login_required, current_user
# from api.model import User, Lemma, Comment, db
from app.api.mysql_model import ASNUser, Paper_detail, db
from app.api.decorators import check_confirmed


user = Blueprint(
    'user',
    __name__
)


@user.route('/home')
def home():
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    print "home current user:", nowUser
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}
    return render_template('home.html', Status=status)


@user.route('/login')
def login():
    return render_template('login.html')


@user.route('/regist')
def regist():
    return render_template('register.html')


@user.route('/add')
@login_required
def add():
    return render_template('add.html')


@user.route('/search', methods=['POST'])
def search():
    searchtext = request.form.get('searchtext')
    results = Expert_detail.query.filter(Expert_detail.name.like("%" + searchtext + "%")).all()
    if results:
        return render_template('result.html', results=results)
    else:
        flash('not found')
    return redirect(url_for('user.home'))


@user.route('/detail', methods=['POST'])
def detail():
    entirelytitle = request.form.get('linklist')
    fullcontent = Expert_detail.query.filter_by(title=entirelytitle)
    return render_template('detail.html', fullcontent=fullcontent)


@user.route('/modify')
@login_required
def modify():
    return render_template('modify.html')


@user.route('/upload', methods=['POST'])
def upload():
    pass


@user.route('/follow', methods=['POST'])
def follow():
    pass


@user.route('/private_profile', methods=['POST', 'GET'])
@login_required
# @check_confirmed
def private_profile():
    return render_template('private_profile.html')


@user.route('/search_results', methods=['GET'])
def search_results():
    searchContent = request.args.get('SearchContent')
    results = request.args.get('Results')
    print "user search", searchContent
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}

    return render_template('search_results.html', Status=status, SearchContent=searchContent, Results=results)
# @user.route('/confirm_url')
# def confirm():
#     pass


@user.route('/public_profile', methods=['GET'])
def public_profile():
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}

    return render_template('public_profile.html', Status=status)


@user.route('/paper_detail', methods=['GET'])
def get_paper():
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}

    return render_template('paper_detail.html', Status=status)