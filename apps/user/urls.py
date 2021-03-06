from django.contrib import admin
from django.urls import path, include
from user.views import RegisterView, ActiveView, LoginView, LogoutView, ActiveEmailView, UserInfoView, UserOrderView, UserAdressView


app_name = "user"

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('active/<str:token>', ActiveView.as_view(), name='active'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(),name='logout'),
    path('activeemail', ActiveEmailView.as_view(), name='activeemail'),

    path('order/<int:page>', UserOrderView.as_view(), name="order"),
    path('address', UserAdressView.as_view(), name="address"),
    path('', UserInfoView.as_view(), name="user"),
]
