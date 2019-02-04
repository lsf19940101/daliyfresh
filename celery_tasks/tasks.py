# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 创建Celery类的实例化对象
app = Celery('celery_tasks.tasks', broker='redis://localhost')

# 定义任务函数
@app.task
def send_regiser_active_email(to_email, username, token):
    '''发送激活邮件'''
    active_url = "127.0.0.1:8000/user/active/{}".format(token)
    subject = "天天生鲜欢迎信息"
    message = '邮件正文'
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>{}, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="{}">{}</a>'.format(username, active_url,
                                                                                            active_url)
    send_mail(subject, message, sender, receiver, html_message=html_message)