from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection


# Create your views here.


class CartAddView(View):
    # ajax 请求发送的请求在后端，不能显示在浏览器上
    def post(self, request):
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 先获取,存在，取值，不存在，为None
        cart_count = conn.hget(cart_key, sku_id)

        if cart_count:
            count += int(cart_count)

        # 校验库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key, sku_id, count)

        # 计算购物车商品的条目数
        total_count = conn.hlen(cart_key)

        return JsonResponse({'res': 5, 'total_count': total_count, 'errmsg': '添加成功'})


class CartInfoView(View):

    def get(self, request):
        user = request.user
        # 获取用户购物车中的数据

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        cart_dict = conn.hgetall(cart_key)

        skus = []
        total_count = 0
        total_price = 0

        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            amount = sku.price * int(count)

            # 动态增加属性
            sku.amount = amount
            sku.count = int(count)
            skus.append(sku)

            # 累加求总计
            total_count += sku.count
            total_price += amount

        context = {
            'total_price': total_price,
            'total_count': total_count,
            'skus': skus,
        }
        return render(request, 'cart.html', context)

# ajax post 请求
class CartUpdateView(View):

    def post(self, request):
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 校验库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '更新成功'})

# 删除购物车记录
# 采用ajax post请求
# 前端需要传递的参数:商品的id(sku_id)
# /cart/delete
class CartDeleteView(View):
    '''购物车记录删除'''
    def post(self, request):
        '''购物车记录删除'''
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据的校验
        if not sku_id:
            return JsonResponse({'res':1, 'errmsg':'无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res':2, 'errmsg':'商品不存在'})

        # 业务处理:删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':3, 'total_count':total_count, 'message':'删除成功'})
