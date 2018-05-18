# coding=utf-8
from app import app
from gevent import monkey
from gevent.pywsgi import WSGIServer

if __name__ == '__main__':
    # app.run(debug=True, host='localhost')
    # app.run(host='localhost', threaded=True)

    # http_server = WSGIServer(('localhost', 5000), app)
    # http_server.serve_forever()
    app.run()