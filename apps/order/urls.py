from django.contrib import admin
from django.urls import path, include
from order.views import OrderPlaceView, OrderCommitView

app_name = "order"

urlpatterns = [
    path('place', OrderPlaceView.as_view(), name="orderplace"),
    path('commit', OrderCommitView.as_view(), name="ordercommit")
]
