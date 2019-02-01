import re
from django.shortcuts import render, redirect
from django.urls import reverse
from user.models import User


# Create your views here.
# /user/register
def register(request):
    '''显示注册页面'''
    if request.method == "GET":
        return render(request, 'register.html')
    else:
        '''处理注册'''
        # 提取数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        eamil = request.POST.get('email')
        allow = request.POST.get('allow')
        # 数据校验
        if not all([username, pwd, cpwd, eamil]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if pwd != cpwd:
            return render(request, 'register.html', {'errmsg': '密码不一致'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', eamil):
            return render(request, 'register.html', {'errmsg': '邮箱格式不一致'})

        if allow != "on":
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否存在
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            # 业务处理：用户注册
            user = User.objects.create_user(username, eamil, pwd)
            user.is_active = 0
            user.save()

            # 返回应答，跳转首页
            return redirect(reverse("goods:index"))
        else:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
