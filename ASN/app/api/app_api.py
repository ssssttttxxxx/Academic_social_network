# coding=utf-8
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import json
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify, render_template, current_app
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class, DOCUMENTS
from flask_wtf import FlaskForm

import logging
import datetime
from PIL import Image

from app.api.model import User, Lemma, Comment, db
from app.api.mysql_model import ASNUser, Expert_detail, Paper_detail, Expert_detail_total, Upload_paper
from app.api.construct_network_from_mongodb import ConstructCoauthorsTree, ConstructCitationTree
from app.api.mongodb_model import mongo
# from app import photos, files

photos = UploadSet('PHOTOS', IMAGES)
papers = UploadSet('PAPERS')

api = Blueprint(
    'api',
    __name__,
)

login_manager = LoginManager()
login_manager.login_view = '.login'
login_manager.login_message = '请登录'


@login_manager.user_loader
def load_user(email):
    # print "ASNUser load_user: ", ASNUser.query.get(email)
    print "db load_user: ", db.session.query(ASNUser).filter(ASNUser.email==email).first()
    return db.session.query(ASNUser).filter(ASNUser.email==email).first()


@api.route('/regist', methods=['POST', 'GET'])
def registBussiness():
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

        # 注册时添加到作者表中
        try:
            res = db.session.query(db.func.max(Expert_detail_total.total_id).label('max_id')).one()
            # max_id = db.session.query(db.func.max(Expert_detail_total)).scalar().total_id
            max_id = res.max_id
            print "max_id: ", max_id
            expert = Expert_detail_total(id=max_id, email=email, name=first_name + " " + last_name, gender=sex,
                                         education=education, total_id=max_id + 1)
            db.session.add(expert)
            db.session.commit()
        except Exception, e:
            print '添加到作者表时发生错误: ', e

        # 注册到用户表
        try:
            user = ASNUser(email=email, password=password, first_name=first_name,
                           last_name=last_name, gender=gender, education=degree)
            db.session.add(user)
            db.session.commit()
        except Exception, e:
            print '添加到用户表时发生错误: ', e

        # 注册时在mongodb初始化关注列表
        mongo_user = {"email": email, "follow": []}
        mongo.db.follow.insert_one(mongo_user)

        # login_user(user)
        flash('注册成功!请登录!')
        return redirect(url_for('user.login'))
    else:
        flash('注册失败!帐号已存在,请重新注册!')
        return redirect(url_for('user.regist'))


@api.route('/login', methods=['POST'])
def loginBussiness():
    name = request.form.get('email')
    password = request.form.get('password')
    # nowUser = ASNUser.query.filter_by(email=name, password=password).first()
    nowUser = db.session.query(ASNUser).filter(ASNUser.email == name, ASNUser.password == password).first()
    print nowUser
    if nowUser:
        login_user(nowUser)
        return redirect(url_for('user.home'))
        # status = {"loginStatus": True,
        #           "logoutStatus": False}
        # return render_template("index.html", Status=status)
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
    print "name", expert_name
    if expert_name is None:
        return render_template("asn_detail.html")
    else:
        results = Expert_detail.query.filter(Expert_detail.name.like("%" + expert_name + "%")).all()
        if results is not None:
            return render_template('asn_detail.html', experts=results)
        else:
            return "no expert found!fxxx_expert_detail"


# 不启用
@api.route('/authors')
@api.route('/authors/<string:paper_id>')
def search_authors(paper_id=None):
    """
    返回论文id的所有作者
    :param paper_id:
    :return:
    """
    print "paper_id", paper_id
    if paper_id is None:
        return render_template("asn_authors.html")
    else:
        results = mongo.db.Co_authors.find_one({'paper_id': paper_id})
        if results is not None:
            paper_authors = {
                'paper_id': results['paper_id'],
                'co_authors': results['co_authors'],
            }
            print paper_authors
            return render_template("asn_authors.html", authors=paper_authors)
        else:
            return "no expert found!fxxx_authors"


# 不启用
@api.route('/paper')
@api.route('/paper/<string:paper_name>')
def search_paper(paper_name=None):
    """
    返回论文搜索结果
    :param paper_name:
    :return:
    """
    print "paper_name", paper_name
    if paper_name is None:
        return render_template("asn_search_papers.html")
    else:
        # print "before query"
        Paper_detail.query.limit(10)
        results = Paper_detail.query.filter(Paper_detail.title.like("%" + paper_name + "%")).slice(0, 10).all()
        # resultss = db.session.query(Paper_detail.title).filter(Paper_detail.title.like("%" + paper_name + "%")).first()
        # resultsss = Paper_detail.query.limit(10).all()
        # print "after query"
        paper_search_results = []
        for result in results:
            paper_search_results.append(result["title"])
        if results is not None:
            print "resultss: ", results
            return render_template("search_papers.html", papers=paper_search_results)
        else:
            return "no paper found!paper_search"


@api.route('/search', methods=['POST', 'GET'])
def searchBussiness():
    """
    根据请求的搜索类型返回paper或者author的搜索结果
    :return:
    """
    item_number = 10
    searchtext = request.form.get('searchtext')  # 搜索字段需要存入页面之中，否则难以获取0
    search_type = request.form.get('searchType')
    page_number = request.form.get('page')  # 用户点击搜索时page_number为1
    start_item_number = (page_number - 1) * item_number

    if search_type == "authors":
        author_results = Expert_detail.query.filter(
            Expert_detail.name.like("%" + searchtext + "%")).slice(start_item_number, item_number).all()
        if author_results is not None:
            # 存放所有研究者信息的数组
            authors_detail = []
            for author in author_results:
                author_detail = {
                    "id": author["id"],
                    "mid": author["mid"],
                    "department": author["department"],
                    "name": author["name"],
                    "email": author["email"],
                }
                authors_detail.append(author_detail)
            json_authors_detail = json.dumps({"authors_detail": authors_detail})
            return json_authors_detail
            # return render_template("AuthorSearchResults.html", json_authors_detail)
        else:
            return json.dumps({"error": "can not found the author"})

    elif search_type == "papers":
        paper_results = Paper_detail.query.filter(
            Paper_detail.title.like("%" + searchtext + "%")).slice(start_item_number, item_number).all()
        if paper_results is not None:
            # 存放所有paper信息的数据
            papers_detail = []
            for paper in paper_results:
                paper_detail = {
                    "id": paper["id"],
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "venue": paper["venue"],
                    "year": paper["year"],
                    "ref": paper["ref"],
                    "abtract": paper["abtract"],
                }
                papers_detail.append(paper_detail)
            json_paper_detail = json.dumps({"papers_detail": papers_detail})
            return json_paper_detail
            # return render_template("PaperSearchResults.html", json_authors_detail)

        else:
            return json.dumps({"error": "can not found the author"})


@api.route('/expert_network', methods=['GET'])
# @api.route('/expert_network/<string:expert_name>')
def expert_network():
    """
     返回作者的社交网络
    :param expert_name:
    :return:
    """
    # expert_id = request.form.get('expert_id')
    # expert_name = request.form.get('expert_name')
    # year = request.form.get('year')
    datas = []
    expert_name = request.args.get('name')
    print "expert_name", expert_name
    years = [2008, 2009, 2010]
    for year in years:
        coauthor_network = ConstructCoauthorsTree(expert_name, year)
        coauthor_network.construct()

        coauthor_nodes = coauthor_network.all_nodes()
        nodes = []
        for node in coauthor_nodes:
            node_item = {
                "name": str(node),
                "value": 10
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


@api.route('/paper_network', methods=['GET'])
@api.route('/paper_network/<string:paper_id>')
def paper_network(paper_id=None):
    """
    返回paper的引文网络
    :param paper_id:
    :return:
    """
    # paper_id = request.form.get('paper_id')

    print "paper_id"
    paper_network = ConstructCitationTree(paper_id)
    paper_network.construct()
    paper_network_edges = paper_network.edges()
    # return paper_network_edges
    return render_template('test_output.html', edges_list=paper_network_edges)


@api.route('/author_paper', methods=['GET'])
@api.route('/author_paper/<string:author_name>')
def author_paper():
    """
    返回作者的所有论文
    :param author_name:
    :return:
    """
    author_name = request.args.get('name')
    print "author name: ", author_name
    results = mongo.db.Co_authors_added_year_title_abstract.find({'co_authors': author_name})
    papers = []
    for result in results:
        id = result['paper_id']
        title = result['title']
        co_authors = result['co_authors']
        year = result['year']
        abstract = result['abstract']
        paper = {
            "id": id,
            "title": title,
            "co_authors": co_authors,
            "year": year,
            "abstract": abstract,
        }
        papers.append(paper)
        print papers
    return render_template("blank.html", papers=papers)
    # return json.dumps(papers)


@api.route('/author_detail', methods=['GET'])
@api.route('/author_detail/<string:author_name>')
def author_detail(author_name=None):
    """
    返回作者的详细信息
    :param author_name:
    :return:
    """
    print "author_name: ", author_name
    author_detail = Expert_detail_total.query.filter_by(name=author_name).first()
    return render_template('asn_detail.html', author=author_detail)


@api.route('/insert_new_item', methods=['POST'])
def insert_new_item():
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
                               h_index, g_index, gender, cite_num, tags)

    try:
        db.session.add(item)
        db.session.commit()
        return json.dumps({"result": "insertion successd"})

    except:
        return json.dumps({"result": "insertion failed"})


@api.route('/modify_user', methods=['POST'])
@login_required
def modify_user():
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
        result = ASNUser.query.filter(ASNUser.email == current_user.get_id()).first()
        another_result = db.session.query(ASNUser).filter(ASNUser.email == current_user.get_id()).first()
        # print "first_name", request.form['firstName']
        if first_name is not None:
            print "firstName", first_name
            print "lastName", last_name
            print "gender", gender
            print "degree", degree
            print "department", department
            print "address", address
            print "phone", phone
            result_user = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()
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

        result_expert = db.session.query(Expert_detail_total).filter(Expert_detail_total.email == current_email).first()
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
    # 注册
    # photos = UploadSet('PHOTOS', IMAGES)
    # configure_uploads(current_app, photos)
    # patch_request_class(current_app)

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
                    print "无法更新头像"
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
        db.session.commit()
        return json.dumps({'result': 'success'})
    except:
        return json.dumps({'result': 'fail'})

@api.route('/del_tag', methods=['POST'])
@login_required
def del_tag():
    current_email = current_user.get_id()
    area_index = request.form.get('index')
    result = db.session.query(ASNUser).filter(ASNUser.email == current_email).first()
    area_list = result.focus_area.split(',')
    # area_list.remove(area_text)
    del area_list[int(area_index)]
    area_str = ""
    for index, area in enumerate(area_list):
        if index == len(area_list)-1:
            area_str = area_str + area
        else:
            area_str = area_str + area + ','

    result.focus_area = area_str
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
        # try:
        email = current_user.get_id()
        file = request.files['uploadPaper']
        print "paper name",file.filename

        filename = papers.save(file, name=file.filename)
        file_url = papers.url(filename)

        # file_url = current_app.config['UPLOADED_PAPERS_URL']+file.filename
        # file.save(current_app.config['UPLOADED_PAPERS_DEST']+file.filename)

        print "paper url", file_url
        upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            upload_record = Upload_paper(user_email=email, file_url=file_url, time=upload_time)
            db.session.add(upload_record)
            db.session.commit()
        except:
            print "error: ", 'may be duplicate name of paper or connection timeout'
            return json.dumps({'result': 'fail', 'msg': 'duplicate name of paper'})
        return json.dumps({'result': 'success', 'name': file.filename, 'time': upload_time})
        # except Exception, e:
        #     print "error: ",e
        #     return json.dumps({'result': 'fail', 'msg': 'Error occurred'})
    else:
        print "no uploadPaper part"
        return json.dumps({'result': 'fail', 'msg': 'No file part'})


@api.route('/delete_paper', methods=['POST'])
@login_required
def delete_paper():
    email = current_user.get_id()
    try:
        result = db.session.query(Upload_paper).filter(Upload_paper.user_email == email).first()
        url = result.avatar.split('..')
        delete_url = './app' + url[1]
        os.remove(delete_url)
        return json.dumps({'result': 'success'})
    except Exception, e:
        return json.dumps({'result': 'fail'})