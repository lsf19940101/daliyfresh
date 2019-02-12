from django.contrib import admin
from django.urls import path, include
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView

app_name = "order"

urlpatterns = [
    path('place', OrderPlaceView.as_view(), name="orderplace"),
    path('commit', OrderCommitView.as_view(), name="ordercommit"),
    path('pay', OrderPayView.as_view(), name='pay'),
    path('check', CheckPayView.as_view(), name='check'),

]
