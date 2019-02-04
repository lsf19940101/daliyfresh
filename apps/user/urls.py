from django.contrib import admin
from django.urls import path, include
from user.views import RegisterView, ActiveView, LoginView, LogoutView, ActiveEmailView, UserInfoView, UserOrderView, UserAdressView
from django.contrib.auth.decorators import login_required


app_name = "user"

urlpatterns = [
    # path("register", views.register, name='register'),
    path('register', RegisterView.as_view(), name='register'),
    path('active/<str:token>', ActiveView.as_view(), name='active'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(),name='logout'),
    path('activeemail', ActiveEmailView.as_view(), name='activeemail'),
    # path('order', login_required(UserOrderView.as_view()), name="order"),
    # path('address', login_required(UserAdressView.as_view()), name="address"),
    # path('', login_required(UserInfoView.as_view()), name="user"),

    path('order', UserOrderView.as_view(), name="order"),
    path('address', UserAdressView.as_view(), name="address"),
    path('', UserInfoView.as_view(), name="user"),
]
