# 使用celery
from celery import Celery
from django.conf import settings

from django.core.mail import send_mail
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django.template import loader
import os


# 在任务处理者一端加这几句
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()
# 创建Celery类的实例化对象
app = Celery('celery_tasks.tasks', broker='redis://localhost')

# 定义任务函数
@app.task
def send_regiser_active_email(to_email, username, token):
    '''发送激活邮件'''
    active_url = "{}/user/active/{}".format(settings.HOST_URL ,token)
    subject = "天天生鲜欢迎信息"
    message = '邮件正文'
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>{}, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="{}">{}</a>'.format(username, active_url,
                                                                                            active_url)
    send_mail(subject, message, sender, receiver, html_message=html_message)

@app.task
def generate_static_index_html():
    """产生静态页面"""
    # 获取首页商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页的轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    # type_goods_bannner = IndexTypeGoodsBanner.objects.all()
    for type in types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态添加属性
        type.image_banners = image_banners
        type.title_banners = title_banners



    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banner': promotion_banner,
    }

    # 使用模板
    # 1.加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)
    # 3.生成对应的静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    with open(save_path, 'w') as f:
        f.write(static_index_html)
