# coding=utf-8
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import json
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify, \
    render_template, current_app, session, logging, g
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class, DOCUMENTS
from flask_wtf import FlaskForm
from flask_mail import Message, Mail
from flask_pymongo import PyMongo

import re
import time
import math
import logging
import datetime
import MySQLdb
from PIL import Image
from token import generate_confirmation_token, confirm_token
from werkzeug.contrib.cache import SimpleCache
from decorators import check_confirmed

# from app.api.model import User, Lemma, Comment, db
from app.api.mysql_model import ASNUser, Expert_detail, Paper_detail, Expert_detail_total, Upload_paper, db
from app.api.construct_network_from_mongodb import ConstructCoauthorsTree, ConstructCitationTree
# from app.api.mongodb_model import mongo

# 缓存
cache = SimpleCache()



mysql_db = MySQLdb.connect("47.106.157.16", "root", "123456", "citation", charset='utf8')

photos = UploadSet('PHOTOS', IMAGES)
papers = UploadSet('PAPERS')

mongo = PyMongo()

api = Blueprint(
    'api',
    __name__,
)

login_manager = LoginManager()
login_manager.login_view = 'user.login'
login_manager.login_message = '请登录'
login_manager.session_protection = "strong"

# refresh login 配置
login_manager.refresh_view = ".login"
login_manager.needs_refresh_message = (u"请重新登录")
login_manager.needs_refresh_message_category = "info"


@login_manager.needs_refresh_handler
def refresh():
    flash('You should log in!')
    return logout()


@login_manager.user_loader
def load_user(email):
    # remember 默认为 False

    """
    login manager 要求实现
    :param email:
    :return:
    """
    # print "ASNUser load_user: ", ASNUser.query.get(email)
    print "db load_user: ", db.session.query(ASNUser).filter(ASNUser.email == email).first()
    return db.session.query(ASNUser).filter(ASNUser.email == email).first()


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logfile = './logs/app.log'
fh = logging.FileHandler(logfile, mode='a')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

mail = Mail()


def another_send_email(to, subject, template=None, **kwargs):
    # app = current_app._get_current_object()
    msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[to])
    # msg.body = render_template(template + '.txt', **kwargs)
    # msg.html = render_template(template + '.html', **kwargs)#将准备好的模板添加到msg对象上，字典传的参里包括token(即生成的一长串字符串)，链接的组装，页面的渲染在里面用jinja2语法完成
    msg.body = '<b>Hello Web</b>'
    # with app.app_context():
    mail.send(msg)  # 发射


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)


@api.route('/confirm/<string:token>')
@login_required
def confirm_email(token=None):
    print "token", token

    try:
        email = confirm_token(token)
        print "email", email
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')

    user = ASNUser.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        # db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('user.login'))


@api.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('user.home')
    else:
        flash('Please confirm your account!', 'warning')
        return render_template('unconfirmed.html')


@api.route('/resend')
@login_required
def resend_confirmation():
    sender_email = '709778550@qq.com'
    token = generate_confirmation_token(current_user.email)

    confirm_url = url_for('api.confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    # send_email(current_user.email, subject, html)
    send_email(sender_email, subject, html)

    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('user.login'))


@api.route('/regist', methods=['POST', 'GET'])
def registBussiness():
    """
    注册事务
    :return:
    """
    name = request.form.get('email')
    nowUser = ASNUser.query.filter_by(email=name).first()
    if not nowUser:
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        gender = request.form.get('gender')
        degree = request.form.get('degree')
        sex = ""
        if gender == "0":
            sex = "male"
        elif gender == "1":
            sex = "female"
        education = ""
        if degree == "0":
            education = "bechelor"
        elif degree == "1":
            education = "master"
        elif degree == "2":
            education = "Ph.D"

        # token = generate_confirmation_token()
        # send_email('709778550@qq.com', "hello", )

        # 发送验证邮件
        to_email = '709778550@qq.com'
        token = generate_confirmation_token(email)
        confirm_url = url_for('api.confirm_email', token=token, _external=True)
        print "confirm_url", confirm_url
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email('709778550@qq.com', subject, html)

        # 注册时添加到作者表中
        try:
            res = db.session.query(db.func.max(Expert_detail_total.author_id).label('max_id')).one()
            # max_id = db.session.query(db.func.max(Expert_detail_total)).scalar().author_id
            max_id = res.max_id
            print "max_id: ", max_id
            expert = Expert_detail_total(id=email, email=email, name=first_name + " " + last_name, gender=sex,
                                         education=education, author_id=max_id + 1)
            db.session.add(expert)
            db.session.commit()
        except Exception, e:
            error_msg = '添加到作者表时发生错误: ', e
            print error_msg
            logging.error(error_msg)

        # 注册到用户表
        try:
            user = ASNUser(email=email, password=password, first_name=first_name,
                           last_name=last_name, gender=gender, education=degree)
            db.session.add(user)
            db.session.commit()
        except Exception, e:
            error_msg = '添加到用户表时发生错误: ', e
            print error_msg
            logging.error(error_msg)

        # 注册时在mongodb初始化关注列表
        mongo_user = {"email": email, "follow": []}
        mongo.db.follow.insert_one(mongo_user)

        # login_user(user)
        flash('注册成功!请登录!')
        logging.info(email + ' successfully registed')
        return redirect(url_for('user.login'))
    else:
        flash('注册失败!帐号已存在,请重新注册!')
        return redirect(url_for('user.regist'))


@api.route('/login', methods=['POST'])
def loginBussiness():
    # if current_user.is_active():
    #     return redirect(url_for('user.home'))
    name = request.form.get('email')
    password = request.form.get('password')
    # nowUser = ASNUser.query.filter_by(email=name, password=password).first()
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == name, ASNUser.password == password).first()
    print nowUser
    if nowUser:
        login_user(nowUser)
        return redirect(url_for('user.home'))

    else:
        flash('登录失败，请检查账号和密码！')
        return redirect(url_for('user.login'))


@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.home'))


@api.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    db.session.commit()
    return jsonify(error=False)


@api.route('/ref_id')
@api.route('/ref_id/<string:paper_id>')
def ref_id(paper_id=None):
    """
    返回paper的id和paper引文的id
    :param paper_id:
    :return:
    """
    print "id", paper_id
    # data = {'id':paper_id, 'detail':'fxxx'}
    # mongo.db.C.insert_one(data)
    if paper_id is None:
        paper = mongo.db.Citation.find()
        return render_template('blank.html')
    else:
        paper = mongo.db.Citation.find_one({'paper_id': paper_id})
        if paper is not None:
            paper_detail = {
                "paper_id": paper["paper_id"],
                "ref_id": paper["ref_id"]
            }
            print paper_detail
            return render_template('blank.html', papers=[paper_detail])
            # return paper_detail
        else:
            return "no paper found!fxxx_ref_id"
            # return "insert!!"


@api.route('/expert_search')
@api.route('/expert_search/<string:expert_name>')
def search_expert(expert_name=None):
    """
    返回作者的搜索结果
    :param expert_name:
    :return:
    """
    page = 1
    pagesize = 20
    print "name", expert_name

    if expert_name is None:
        return render_template("asn_detail.html")
    else:
        # cursor = mysql_db.cursor()
        # sql = "select * from expert_user_detail where name like '%" + expert_name + "%'"
        # print "sql", sql
        # cursor.execute(sql)
        # results = cursor.fetchall()


        results = db.session.query(Expert_detail_total).filter(
            Expert_detail_total.name.like('%' + expert_name + '%')).order_by(Expert_detail_total.name).all()
        if results is not None:
            print "results", results
            for index, result in enumerate(results):
                print index, result
                # if result is not None:
                try:
                    print index, result.name
                except:
                    print index, "result is None"
                    # print result.name
            return render_template('asn_detail.html', experts=results)
        else:
            return "no expert found!fxxx_expert_detail"


@api.route('/search', methods=['POST', 'GET'])
# @api.route('/paper/<string:search_content>/<int:page>')
def search():
    """
    根据请求的搜索类型返回paper或者author的搜索结果
    :return:
    """

    # if request.method == 'GET':
    #     print 'GET'
    #     searchtext = request.args.get('content', default='*', type=str).strip()
    # elif request.method == 'POST':
    #     print 'POST'
    #     searchtext = request.form.get('content', default='*', type=str).strip()
    #
    # page = request.args.get('page', default=1, type=int)
    # print "page", page
    # print "content", searchtext

    searchtext = request.args.get('content').strip()
    search_type = request.args.get('type')
    paper_page_num = int(request.args.get('p_page'))
    author_page_num = int(request.args.get('a_page'))

    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    print "home current user:", nowUser
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}

    item_number = 10

    papers_detail = {}
    authors_detail = {}
    paper_total_page = 1
    author_total_page = 1
    paper_cache = cache.get('paper')
    author_cache = cache.get('author')
    # print "paper_cache", paper_cache
    # print "author_cache", author_cache


    if search_type == 'paper' and author_cache is not None:
        print "have author cache"
        authors_detail=author_cache
    else:
        start_item_number = (author_page_num - 1) * item_number
        end_item_number = author_page_num * item_number

        # 使用mysql查询 not model
        author_results = db.session.query(Expert_detail_total).filter(
            Expert_detail_total.name.like('%' + searchtext + '%')).order_by(Expert_detail_total.name).slice(
            start_item_number, end_item_number).all()

        author_num = db.session.query(Expert_detail_total).filter(
            Expert_detail_total.name.like('%' + searchtext + '%')).count()
        print "author_num", author_num

        author_total_page = int(math.ceil(author_num / float(item_number)))
        if author_total_page == 0:
            author_total_page = 1

        # 使用mysql查询 model
        # author_results = Expert_detail.query.filter(Expert_detail.name.like("%" + searchtext + "%")).slice(start_item_number, item_number).all()

        # 使用mongodb查询
        # author_results = mongo.db.Co_authors_added_year_title_abstract.find({'title': re.compile(searchtext)}).skip(
        #     (page - 1) * item_number).sort('title', -1).limit(item_number)

        if author_results is not None:
            # 存放所有研究者信息的数组
            authors_detail = []
            for author in author_results:
                tags = author.tags
                if tags is None:
                    tags = ""
                tags = re.split(r'[\[\];,]', str(tags))
                tags_str = ""
                for i, tag in enumerate(tags):
                    if i == len(tags):
                        tags_str = tags_str + tag
                    else:
                        tags_str = tags_str + tag + ', '
                while '' in tags:
                    tags.remove('')
                author_detail = {
                    "id": author.id,
                    "position": author.position,
                    "mid": author.mid,
                    "name": author.name,
                    "name_zh": author.name_zh,
                    "phone": author.phone,
                    "fax": author.fax,
                    "email": author.email,
                    "department": author.department,
                    "address": author.address,
                    "homepage": author.homepage,
                    "education": author.education,
                    "experience": author.experience,
                    "biography": author.biography,
                    "avatar": author.avatar,
                    "h_index": author.h_index,
                    "g_index": author.g_index,
                    "gender": author.gender,
                    "cite_num": author.cite_num,
                    "tags": tags_str,
                    "author_id": author.author_id,
                }
                authors_detail.append(author_detail)
                # json_authors_detail = json.dumps({"authors_detail": authors_detail})



    if search_type == 'author' and paper_cache is not None:
        print "have paper cache"
        papers_detail = paper_cache
    else:
        start_item_number = (paper_page_num - 1) * item_number
        end_item_number = paper_page_num * item_number

        # 使用mysql查询 model
        # paper_results = Paper_detail.query.filter(Paper_detail.title.like("%" + searchtext + "%")).slice(start_item_number, item_number).all()

        # 使用mongodb查询
        paper_num = mongo.db.Co_authors_added_year_title_abstract.find({'title': re.compile(searchtext)}).count()
        print "paper num", paper_num

        paper_total_page = int(math.ceil(paper_num / float(item_number)))
        if paper_total_page == 0:
            paper_total_page = 1
        print "paper page total", paper_total_page

        paper_results = mongo.db.Co_authors_added_year_title_abstract.find({'title': re.compile(searchtext)}).skip(
            start_item_number).sort('title', -1).limit(item_number)

        if paper_results is not None:
            # 存放所有paper信息的数据
            papers_detail = []
            for paper in paper_results:
                paper_detail = {
                    "id": paper["paper_id"],
                    "title": paper["title"],
                    "authors": paper["co_authors"],
                    # "venue": paper["venue"],
                    "year": paper["year"],
                    # "ref": paper["ref_id"],
                    "abstract": paper["abstract"],
                }
                papers_detail.append(paper_detail)

    cache.set('paper', papers_detail)
    cache.set('author', authors_detail)

    pages = {
        'PaperCurrentPage': paper_page_num,
        'TotalPaperPage': paper_total_page,
        'AuthorCurrentPage': author_page_num,
        'TotalAuthorPage': author_total_page,
    }

    results = {
        'result': 'success',
        'paper': papers_detail,
        'author': authors_detail,
        'pages': pages,
    }

    print "return"
    results = json.dumps(results)
    return render_template(
        'search_results.html',
        Status=status, SearchContent=searchtext,
        Results=results, SearchType=search_type,
    )


    # return redirect(url_for('user.search_results', SearchContent=searchtext, Results=results), code=302, Response=None)


@api.route('/search_result', methods=['GET', 'POST'])
def search_result():
    if request.method == 'GET':
        print 'GET'
        searchtext = request.args.get('content', default='*', type=str).strip()
        search_type = request.args.get('type', default='paper', type=str)
        paper_page_num = request.args.get('p_page', default=1, type=int)
        author_page_num = request.args.get('a_page', default=1, type=int)


    elif request.method == 'POST':
        print 'POST'
        searchtext = request.form.get('content', default='*', type=str).strip()
        search_type = request.form.get('type', default='paper', type=str)
        paper_page_num = request.form.get('p_page', default=1, type=int)
        author_page_num = request.form.get('a_page', default=1, type=int)

    print "p_page", paper_page_num
    print "a_page", author_page_num
    print "content", searchtext
    print "type", search_type

    return redirect(
        url_for('api.search',type=search_type, content=searchtext, p_page=paper_page_num, a_page=author_page_num))

@api.route('/to_public_profile', methods=['GET'])
def to_public_profile():
    id = request.args.get('id')
    return redirect(url_for('api.public_profile', ID=id))

@api.route('/public_profile', methods=['GET'])
def public_profile():
    id = request.args.get('ID')
    print 'id', id

    result = db.session.query(Expert_detail_total).filter(Expert_detail_total.id == id).first()
    tags = result.tags
    if tags is None:
        tags = ""
    tags = re.split(r'[\[\];,]', str(tags))
    while '' in tags:
        tags.remove('')
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}

    author_name = result.name
    print "author_name",author_name
    print "查询论文"
    paper_result = mongo.db.Paper_of_author.find_one({'author_name':author_name})
    print "end"
    paper_detail_list = []

    if paper_result is not None:
        papers = paper_result['papers']
        for paper in papers:
            paper_detail = {
                'id':paper['paper_id'],
                'year':paper['year'],
                'title':paper['title'],
                # 'venue':paper['venue']
            }
            paper_detail_list.append(paper_detail)

    author_detail = {
        "id": result.id,
        "position": result.position,
        "mid": result.mid,
        "name": result.name,
        "name_zh": result.name_zh,
        "phone": result.phone,
        "fax": result.fax,
        "email": result.email,
        "department": result.department,
        "address": result.address,
        "homepage": result.homepage,
        "education": result.education,
        "experience": result.experience,
        "biography": result.biography,
        "avatar": result.avatar,
        "h_index": result.h_index,
        "g_index": result.g_index,
        "gender": result.gender,
        "cite_num": result.cite_num,
        "tags": tags,
        "author_id": result.author_id,
        "paper_list": paper_detail_list
    }



    author_detail_json = json.dumps(author_detail)
    return render_template('public_profile.html', Status=status, authorDetail=author_detail_json)


@api.route('get_paper', methods=['GET'])
def get_paper():
    # author_id = request.args.get('authorID')
    author_name = request.args.get('authorName')
    result = mongo.db.Paper_of_author.find_one({'author_name': author_name})
    papers = result['papers']
    items = []

    for paper in papers:
        paper_id = paper['paper_id']
        paper_detail = mongo.db.Citation_total.find_one({'paper_id': paper_id})
        paper_keywords = []
        papers_kv = mongo.db.paper_keywords.find_one({'paper_id': paper_id})['keyword_and_val']
        for paper_kv in papers_kv:
            paper_keywords.append(paper_kv['keyword'])
        item = {
            'id':paper_detail['paper_id'],
            'title':paper_detail['title'],
            'co_authors':paper_detail['co_authors'],
            'year':paper_detail['year'],
            'abstract':paper_detail['abstract'],
            'venue':paper_detail['venue'],
            'ref_id':paper_detail['ref_id'],
            'keywords':paper_keywords,
        }

        items.append(item)

@api.route('/to_paper_detail', methods=['GET'])
def to_paper_detail():
    paper_id = request.args.get('id')
    print "paper_id", paper_id
    return redirect(url_for('api.paper_detail', paperID=paper_id))


@api.route('/paper_detail', methods=['GET'])
def paper_detail():
    paper_id = request.args.get('paperID')
    print "paper id", paper_id

    nowUser = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
    if not nowUser:
        print "not current user"
        status = {"loginStatus": False}
    else:
        print "with current user"
        status = {"loginStatus": True}
    paper = mongo.db.Citation_total.find_one({'paper_id': paper_id})
    paper_keywords = []
    papers_kv = mongo.db.paper_keywords.find_one({'paper_id': paper_id})['keyword_and_val']
    for paper_kv in papers_kv:
        paper_keywords.append(paper_kv['keyword'])
    paper_detail = {
        'id': paper['paper_id'],
        'title': paper['title'],
        'co_authors': paper['co_authors'],
        'abstract':paper['abstract'],
        'venue': paper['venue'],
        'year': paper['year'],
        'ref_id': paper['ref_id'],
        'keywords': paper_keywords,
    }
    paper_detail_json = json.dumps(paper_detail)
    return render_template('paper_detail.html', paperDetail=paper_detail_json, Status=status)



@api.route('/expert_network', methods=['POST'])
def expert_network():
    """
     返回作者的社交网络
    :param expert_name:
    :return:
    """
    # expert_id = request.form.get('expert_id')
    # expert_name = request.form.get('expert_name')
    # year = request.form.get('year')
    # min_year = 1954
    min_year = 2013
    max_year = 2017
    years = []
    datas = []
    expert_name = request.form.get('name')
    print "expert_name", expert_name

    for year in range(min_year, max_year):
        years.append(year)
    # years = [2008, 2009, 2010]
    for year in years:
        coauthor_network = ConstructCoauthorsTree(expert_name, year)
        coauthor_network.construct()

        # 网络中只有作者自己，则进行下一年的关系网络构建
        if coauthor_network.nodes_num() == 1:
            print year, 'break'
            continue

        coauthor_nodes = coauthor_network.all_nodes()
        nodes = []
        for node in coauthor_nodes:
            node_item = {
                "name": str(node),
                "value": 10,
            }

            nodes.append(node_item)

        coauthor_network_edges = coauthor_network.all_edges()
        edges = []
        for source, target, value in coauthor_network_edges:
            edges_item = {
                "source": source,
                "target": target,
                "values": value,
            }
            edges.append(edges_item)
        gra_data = {"year": year, "nodes": nodes, "links": edges}
        datas.append(gra_data)

    json_data = json.dumps(datas)
    # print json_data
    return json_data

    # return render_template('old_tem/test_output.html', edges_list=coauthor_network_edges)


@api.route('/paper_network', methods=['POST'])
def paper_network():
    """
    返回paper的引文网络
    :param paper_id:
    :return:
    """
    paper_id = request.form.get('paperID')
    years = [2008, 2009, 2010]
    nodes = []
    edges = []
    print "paper_id", paper_id
    paper_network = ConstructCitationTree(paper_id)
    paper_network.construct()
    paper_network_edges = paper_network.edges()
    paper_network_nodes = paper_network.all_nodes()

    for pi, t, y in paper_network_nodes:
        # node_detail = {
        #     'node':[
        #         {'name': 'ii',
        #          'id': '1'},
        #         {
        #
        #         }
        #     ]
        # }

        node_item = {
            "name": pi,
            "attributes": {"title": pi, "year": y,},
            "value": 10,
            # "itemStyle":{
            #     "color": '#FF3030'
            # }
        }
        nodes.append(node_item)

    for source, target in paper_network_edges:
        edges_item = {
            "source": source,
            "target": target,
            "values": 2,
            # "lineStyle":{
            #     "color":'#000000'
            # }
        }
        edges.append(edges_item)
    return json.dumps({"nodes": nodes, "links": edges})



@api.route('/insert_new_item', methods=['POST'])
def insert_new_item():
    """

    :return:
    """
    info = request.args.get('mydata')
    id = 1
    mid = ""
    name = info["name"]
    name_zh = info["name_zh"]
    department = info["department"]
    tags = info["tags"]
    gender = info["gender"]
    phone = info["phone"]
    email = info["email"]
    position = info["position"]
    biography = info["biography"]
    experience = info["experience"]
    fax = info["fax"]
    education = info["education"]
    address = info["address"]
    homepage = info["homepage"]
    h_index = 0.00
    g_index = 0.00
    cite_num = 0
    avatar = ""

    item = Expert_detail_total(id, mid, name, name_zh, position,
                               phone, fax, email, department, address,
                               homepage, education, experience, biography, avatar,
                               h_index, g_index, gender, cite_num, tags, )

    try:
        db.session.add(item)
        db.session.commit()
        return json.dumps({"result": "insertion successd"})

    except:
        return json.dumps({"result": "insertion failed"})


@api.route('/modify_user', methods=['POST'])
@login_required
def modify_user():
    """
    修改用户个人信息
    :return:
    """
    try:
        current_email = current_user.get_id()

        if request.method == 'GET':
            print 'GET'
            # new_info = request.args.get("new_info")
            first_name = request.args.get("firstName")
            last_name = request.args.get("lastName")
            gender = request.args.get("genderSelected")
            degree = request.args.get("degreeSelected")
            department = request.args.get("department")
            address = request.args.get("address")
            phone = request.args.get("telephone")
        elif request.method == 'POST':
            print 'POST'
            first_name = request.form.get("firstName")
            last_name = request.form.get("lastName")
            gender = request.form.get("genderSelected")
            degree = request.form.get("degreeSelected")
            department = request.form.get("department")
            address = request.form.get("address")
            phone = request.form.get("telephone")

        # result = ASNUser.query.filter(ASNUser.email == current_user.get_id()).first()
        # another_result = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
        # print "first_name", request.form['firstName']
        if first_name is not None:
            print "firstName", first_name
            print "lastName", last_name
            print "gender", gender
            print "degree", degree
            print "department", department
            print "address", address
            print "phone", phone
            try:
                result_user = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()
            except Exception, e:
                print "modify_user：mysql 查询用户表出错"
                print "error: ", e
                logging.error(e)
                return json.dumps({'result': 'fail', 'msg': 'can not query mysql'})
        else:
            print "firstName", first_name
            print "lastName", last_name
            print "gender", gender
            print "degree", degree
            print "department", department
            print "address", address
            print "phone", phone
            return json.dumps({'result': 'fail'})
        result_user.first_name = first_name
        result_user.last_name = last_name
        result_user.gender = gender
        result_user.education = degree
        result_user.department = department
        result_user.address = address
        result_user.phone = phone

        try:
            result_expert = db.session.query(Expert_detail_total).filter(
                Expert_detail_total.email == current_email).first()
        except Exception, e:
            print "modify_user：mysql 查询作者表出错"
            print "error: ", e
            logging.error(e)
            return json.dumps({'result': 'fail', 'msg': 'can not query mysql'})

        result_expert.name = first_name + " " + last_name
        sex = ""
        if gender == "0":
            sex = "male"
        elif gender == "1":
            sex = "female"
        result_expert.gender = sex
        education = ""
        if degree == "0":
            education = "bechelor"
        elif degree == "1":
            education = "master"
        elif degree == "2":
            education = "Ph.D"
        result_expert.education = education
        result_expert.department = department
        result_expert.address = address
        result_expert.phone = phone
        data = {
            "newFirstName": first_name,
            "newLastName": last_name,
            "newGender": gender,
            "newDegree": degree,
            "newDepartment": department,
            "newAddress": address,
            "newTelephone": phone,
        }
        db.session.commit()
        return json.dumps({'result': 'success', 'newData': data})

    except Exception, e:
        print "error: ", e
        return json.dumps({'result': 'fail'})


@api.route('/follow', methods=['POST'])
@login_required
def follow():
    current_email = current_user.get_id()
    follow_email = request.args.get("email")
    result = mongo.db.follow.find_one({"email": current_email})
    follow_list = result["follow"]
    if follow_email not in follow_list:
        follow_list.append(follow_email)

    update_item = {"email": current_email, "follow": follow_list}
    result = mongo.db.users.replace_one({'email': current_email}, update_item)
    return json.dumps({"result": "successed"})


@api.route('/modify_password', methods=['POST'])
@login_required
def modify_password():
    """
    修改密码
    :return:
    """
    old_password = request.form.get('oldPassword')
    new_password = request.form.get('newPassword')
    current_email = current_user.get_id()
    result = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()

    if old_password == result.password:
        print "procceed modification"
        result.password = new_password
        db.session.commit()
        return json.dumps({'result': 'success'})
    else:
        return json.dumps({'result': 'fail'})


@api.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """
    上传头像
    :return:
    """

    if request.method == 'POST':
        # check if the post request has the file part
        if 'avatar' not in request.files:
            print 'No file part'
            return json.dumps({'result': "failed", 'filename': '', 'msg': 'No avatar part'})
        file = request.files['avatar']
        # if user does not select file, browser also submit a empty part without filename
        if file.filename == '':
            print 'No selected file'
            return json.dumps({'result': "failed", 'filename': '', 'msg': 'No selected file'})
        else:
            try:
                # 存储
                filename = photos.save(file)
                avatar_url = photos.url(filename)
                print '%s avatar_url is %s' % (filename, avatar_url)

                email = current_user.get_id()

                download_url = current_app.config['UPLOADED_PHOTOS_DEST'] + filename
                print '%s download_url is %s', (filename, download_url)

                # update数据库
                try:
                    delete_avatar()
                    result_user = db.session.query(ASNUser).filter(ASNUser.email == email).first()
                    result_user.avatar = avatar_url

                    result_expert = db.session.query(Expert_detail_total).filter(
                        Expert_detail_total.email == email).first()
                    result_expert.avatar = avatar_url

                    db.session.commit()
                except Exception, e:
                    print "无法更新头像", e
                    return json.dumps({'result': "failed", 'filename': '', 'msg': 'Error occurred'})

                # 图片压缩
                im = Image.open(download_url)
                im_resize = im.resize((256, 256))
                im_resize.save(download_url)

                # 返回结果
                return json.dumps({'result': "successed", 'filename': filename, 'msg': avatar_url})
            except Exception as e:
                print 'upload file exception: %s' % e
                return json.dumps({'result': "failed", 'filename': '', 'msg': 'Error occurred'})
    else:
        return json.dumps({'result': "failed", 'filename': '', 'msg': 'Method not allowed'})


def delete_avatar():
    """
    删除原先头像
    :return:
    """
    email = current_user.get_id()
    try:
        result_user = db.session.query(ASNUser).filter(ASNUser.email == email).first()
        if result_user.avatar == "../static/avatar/init.png":
            print "原头像为初始头像"
        else:
            url = result_user.avatar.split('..')
            delete_url = "./app" + url[1]
            os.remove(delete_url)
    except:
        print "无法删除原头像"


@api.route('/add_tag', methods=['POST'])
@login_required
def add_tag():
    """
    添加tag
    :return:
    """
    try:
        current_email = current_user.get_id()
        area_text = request.form.get('text')
        print "tag", area_text

        result = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()
        print result.focus_area
        area_list = result.focus_area

        if area_list == "":
            area_list = area_text
        else:
            area_list = area_list + "," + area_text

        area_str = area_list
        print "area str", area_str
        result.focus_area = area_str

        result_author = db.session.query(Expert_detail_total).filter(Expert_detail_total.id == current_email).first()
        result_author.tags = area_str

        db.session.commit()
        return json.dumps({'result': 'success'})
    except:
        return json.dumps({'result': 'fail'})


@api.route('/del_tag', methods=['POST'])
@login_required
def del_tag():
    """
    删除tag
    :return:
    """
    current_email = current_user.get_id()
    area_index = request.form.get('index')
    result = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()
    area_list = result.focus_area.split(',')

    # area_list.remove(area_text)
    del area_list[int(area_index)]
    area_str = ""
    for index, area in enumerate(area_list):
        if index == len(area_list) - 1:
            area_str = area_str + area
        else:
            area_str = area_str + area + ','
    result.focus_area = area_str

    result_author = db.session.query(Expert_detail_total).filter(Expert_detail_total.id == current_email).first()
    result_author.tags = area_str

    db.session.commit()
    return json.dumps({'result': 'success'})


@api.route('/upload_paper', methods=['POST'])
@login_required
def upload_paper():
    """
    上传论文
    :return:
    """

    # 注册配置

    print "开始上传"
    # files = UploadSet('FILES')
    # configure_uploads(current_app, files)
    # patch_request_class(current_app)

    # print "request.files", request.files
    if request.method == 'POST' and 'uploadPaper' in request.files:
        try:
            email = current_user.get_id()
            file = request.files['uploadPaper']
            print "paper name", file.filename

            filename = papers.save(file, name=file.filename)
            file_url = papers.url(filename)

            # file_url = current_app.config['UPLOADED_PAPERS_URL']+file.filename
            # file.save(current_app.config['UPLOADED_PAPERS_DEST']+file.filename)

            print "paper url", file_url
            upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print upload_time
            try:
                upload_record = Upload_paper(user_email=email, file_url=file_url, time=upload_time,
                                             file_name=file.filename)
                db.session.add(upload_record)
                db.session.commit()
            except:
                db.session.rollback()
                print "error: ", 'may be duplicate name of paper or connection timeout'
                return json.dumps({'result': 'fail', 'msg': 'duplicate name of paper'})
            return json.dumps({'result': 'success', 'name': file.filename, 'time': upload_time})
        except Exception, e:
            print "error: ", e
            return json.dumps({'result': 'fail', 'msg': 'Error occurred'})
    else:
        print "no uploadPaper part"
        return json.dumps({'result': 'fail', 'msg': 'No file part'})


@api.route('/delete_paper', methods=['POST'])
@login_required
def delete_paper():
    """
    删除上传论文
    :return:
    """
    email = current_user.get_id()
    try:
        result = db.session.query(Upload_paper).filter(Upload_paper.user_email == email).first()
        url = result.file_url.split('..')
        delete_url = './app' + url[1]
        os.remove(delete_url)
        return json.dumps({'result': 'success'})
    except Exception, e:
        return json.dumps({'result': 'fail'})


@api.route('/get_upload_paper', methods=['POST'])
@login_required
def get_upload_paper():
    """
    得到用户所有上传论文
    :return:
    """
    email = request.form.get('userID')
    # email = current_user.get_id()
    print 'email', email
    files = []
    try:
        results = db.session.query(Upload_paper).order_by(Upload_paper.time.desc()). \
            filter(Upload_paper.user_email == email).all()

        for result in results:
            upload_dt = result.time.strftime("%Y-%m-%d %H:%M:%S").split(' ')

            upload_date = upload_dt[0]
            upload_time = upload_dt[1]
            file = {
                'fileName': result.file_name,
                'fileURL': result.file_url,
                'time': upload_time,
                'date': upload_date,
            }
            files.append(file)
        print "success"
        return json.dumps({'result': 'success', 'paperItem': files})
    except Exception, e:
        return json.dumps({'result': 'fail', 'msg': 'database query fail'})


