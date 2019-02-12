import re

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse

from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django.views import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings

from celery_tasks.tasks import send_regiser_active_email
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

from django_redis import get_redis_connection


class RegisterView(View):
    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):
        '''处理注册'''

        # 提取数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 数据校验
        if not all([username, pwd, cpwd, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if pwd != cpwd:
            return render(request, 'register.html', {'errmsg': '密码不一致'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})

        if allow != "on":
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否存在
        # try:
        #     User.objects.get(username=username)
        # except User.DoesNotExist:
        ret_list = User.objects.filter(Q(username=username) | Q(email=email))
        if len(ret_list) == 0:
            # 业务处理：用户注册
            user = User.objects.create_user(username, email, pwd)
            user.is_active = 0
            user.save()

            # 发送激活邮件，包含链接:127.0.0.1:8000/user/active/user_id
            # 发送链接中包含的用户信息，需要进行加密

            # 加密用户信息，生成token
            info = {'confirm': user.id}
            serializer = Serializer(settings.SECRET_KEY, 3600)
            token = serializer.dumps(info).decode()

            # 发送邮件
            send_regiser_active_email.delay(email, username, token)
            # 返回应答，跳转首页
            return redirect(reverse("goods:index"))
        else:
            return render(request, 'register.html', {'errmsg': '用户名或邮箱已注册'})


class ActiveView(View):
    '''用户激活'''

    def get(self, request, token):
        # 进行解密， 获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 获取用户id
            info = serializer.loads(token)
            user_id = info.get("confirm")
            # 获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录界面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            return redirect(reverse("user:activeemail"))


class ActiveEmailView(View):

    def get(self, request):

        return render(request, 'active.html', {'errmsg': ''})

    def post(self, request):
        # 提取邮箱地址
        email = request.POST.get("email")

        # 判断是否合法
        if not all([email]):
            return render(request, 'active.html', {'errmsg': '邮箱为空'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'active.html', {'errmsg': '邮箱格式错误'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'active.html', {'errmsg': '邮箱未注册'})

        # 加密用户信息，生成token
        info = {'confirm': user.id}
        serializer = Serializer(settings.SECRET_KEY, 3600)
        token = serializer.dumps(info).decode()
        # 发送邮件
        send_regiser_active_email.delay(email, user.username, token)
        # 跳转到登录页面
        return redirect(reverse("user:login"))


class LoginView(View):
    def get(self, request):
        '''显示登陆页面'''
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登录校验'''

        username = request.POST.get("username")
        pwd = request.POST.get("pwd")

        if not all([username, pwd]):
            return render(request, 'login.html', {'errmsg': '参数不完整'})
        print(username, pwd)
        # user = authenticate(username=username, password=pwd)  # 当账户没有激活时，查询不到
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'login.html', {'errmsg': '用户未注册'})

        if check_password(pwd, user.password):
            if user.is_active:
                next_url = request.GET.get('next', reverse('goods:index'))
                login(request, user)
                response = redirect(next_url)

                # 判断是否需要记住用户名
                remeber = request.POST.get('remeber')

                if remeber == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:

                return redirect(reverse("user:activeemail"))
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):

    def get(self, request):
        logout(request)

        return redirect(reverse("goods:index"))


# 登录验证：若使用的是视图函数，则使用登录装饰器，
# 使用的是类视图，则继承LoginRequiredMixin
class UserInfoView(LoginRequiredMixin, View):

    # request.user
    # 如果用户未登录->AnonymousUser类的一个实例
    # 如果用户登录->User类的一个实例
    # request.user.is_authenticated()
    # 除了你给模板文件传递的模板变量之外,django框架会把request.user也传给模板文件
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)

        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)

        goods_li = []
        for sku_id in sku_ids:
            goods_li.append(GoodsSKU.objects.get(id=sku_id))
        print(goods_li)
        context = {
            'page': 'user',
            'address': address,
            'goods_li':goods_li,
        }

        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):

    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

            # 数据分页
            paginator = Paginator(orders, 1)

            # # 处理页码
            order_page = paginator.get_page(page)

            # todo: 进行页码的控制，页面上最多显示5个页码
            # 1.总页数小于5页，页面上显示所有页码
            # 2.如果当前页是前3页，显示1-5页
            # 3.如果当前页是后3页，显示后5页
            # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
            num_pages = paginator.num_pages
            if num_pages < 5:
                pages = range(1, num_pages + 1)
            elif page <= 3:
                pages = range(1, 6)
            elif num_pages - page <= 2:
                pages = range(num_pages - 4, num_pages + 1)
            else:
                pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


class UserAdressView(LoginRequiredMixin, View):

    def get(self, request):

        # 当前用户
        user = request.user

        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 提取参数
        receiver = request.POST.get("receiver")
        addr = request.POST.get("addr")
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get("phone")
        # 校验参数
        if not all([receiver, addr, zip_code]):
            return render(request, 'user_center_site.html', {'errmsg':"参数不完整"})

        if not re.match(r'^1[34578]\d{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':"手机号格式错误"})

        # 当前用户
        user = request.user

        if Address.objects.get_default_address(user):
            is_default = False
        else:
            is_default = True


        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        return redirect(reverse("user:address"))
