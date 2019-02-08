from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection
from django.core.cache import cache


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
