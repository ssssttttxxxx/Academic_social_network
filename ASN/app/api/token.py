# coding=utf-8
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import URLSafeTimedSerializer


def another_generate_confirmation_token(self,expiration=3600):
    s = Serializer(current_app.config['SECRET_KEY'], expiration)
        #这个函数需要两个参数，一个密匙，从配置文件获取，一个时间，这里1小时
    return s.dumps({'confirm':self.id})


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email