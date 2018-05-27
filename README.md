# Academic_social_network

#安装python所需模块

pip install -r requirements.txt

#安装uwsgi

pip install uwsgi

#安装nginx

yum install nginx

#修改nginx配置文件

cd etc/nginx

vi nginx.conf

#修改如下

server {
        listen       80 default_server;
        server_name  110.64.66.221;
        # root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        location / {
                include uwsgi_params;
                uwsgi_pass 0.0.0.0:5001;
                uwsgi_read_timeout 300;
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }

#保存

#运行uwsgi

uwsgi config.init

#运行nginx

systemctl start nginx