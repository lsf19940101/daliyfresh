from django.contrib import admin
from django.urls import path, include
from cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = "cart"

urlpatterns = [
    path('add', CartAddView.as_view(), name='cartadd'),
    path('update', CartUpdateView.as_view(), name='cartupdate'),
    path('delete', CartDeleteView.as_view(), name='cart_delete'),
    path('', CartInfoView.as_view(), name='cartshow'),
]
