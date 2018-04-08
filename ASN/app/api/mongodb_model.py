# coding=utf-8
from flask_pymongo import PyMongo
from flask import Flask, render_template

app = Flask(__name__)
# app.config.update(
#     MONGO_HOST='localhost',
#     MONGO_PORT=27017,
#     MONGO_USERNAME='',
#     MONGO_PASSWORD='',
#     MONGO_DBNAME='Paper'
# )

app.config['MONGO_HOST'] = '127.0.0.1'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'Paper'
# mongo = PyMongo(app, config_prefix='MONGO3')
mongo = PyMongo(app)


@app.route('/ref_id')
@app.route('/ref_id/<string:paper_id>')
def ref_id(paper_id=None):
    print "id",paper_id
    if paper_id is None:
        paper = mongo.db.Citation.find()
        return render_template('blank.html')
    else:
        paper = mongo.db.Citation.find_one({'paper_id': paper_id})
        if paper is not None:
            return render_template('blank.html', papers=[paper])
            # return paper_detail
        else:
            return "no paper found!"


if __name__ == "__main__":
    # paper_id = "00127ee2-cb05-48ce-bc49-9de556b93346"
    # result = mongo.db.Paper.find_one({'paper_id':paper_id})
    # print result
    app.run(debug=True, host='localhost')
