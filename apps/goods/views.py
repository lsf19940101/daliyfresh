from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache

from django.core.paginator import Paginator


class IndexView(View):

    def get(self, request):
        '''显示首页'''
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        # 获取首页商品的种类信息
        types = GoodsType.objects.all()

        if context is None:
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

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banner,
                       }
            # 设置缓存
            # key  value timeout
            cache.set('index_page_data', context, 3600)

        # 获取首页用户购物车中商品数目
        cart_count = 0
        user = request.user
        # 特别注意：之前的django版本中is_authenticated为方法，后面需要添加（），现在为属性，一定不能添加
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


class DetailView(View):
    def get(self, request, goods_id):
        # 判断sku_id是否存在
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse("goods:index"))
        # 全部商品分类
        types = GoodsType.objects.all()

        # 获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment="")

        # 获取同类商品的新品
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品信息
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取首页用户购物车中商品数目
        cart_count = 0
        user = request.user
        # 特别注意：之前的django版本中is_authenticated为方法，后面需要添加（），现在为属性，一定不能添加
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 用户历史记录
            history_key = 'history_%d' % user.id

            # 移除列表中的商品id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id 插入到列表的左侧
            conn.lpush(history_key, goods_id)
            # 只保存5条记录
            conn.ltrim(history_key, 0, 4)
            sku_ids = conn.lrange(history_key, 0, 4)

        context = {
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'same_spu_skus': same_spu_skus,
        }

        return render(request, 'detail.html', context)


class ListView(View):
    def get(self, request, type_id, page):
        # 数据校验
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse("goods:index"))

        # 商品分类信息
        types = GoodsType.objects.all()

        # 本分类的商品信息
        sort = request.GET.get("sort")

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('-price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 数据分页
        paginator = Paginator(skus, 1)

        # # 处理页码
        # try:
        #     page = int(page)
        # except:
        #     page = 1
        #
        # if page > paginator.num_pages:
        #     page = 1
        # # 提取对应页码的数据
        # skus_page = paginator.page(page)
        skus_page = paginator.get_page(page)

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

        # 获取同类商品的新品
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取首页用户购物车中商品数目
        cart_count = 0
        user = request.user
        # 特别注意：之前的django版本中is_authenticated为方法，后面需要添加（），现在为属性，一定不能添加
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context = {
            "types": types,
            'type': type,
            'skus_page':skus_page,
            'new_skus':new_skus,
            'cart_count':cart_count,
            'sort':sort,
            'pages':pages,
        }
        return render(request, 'list.html', context)
























