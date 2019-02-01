from django.contrib import admin
from django.urls import path, include
from apps.goods import views

app_name = "goods"

urlpatterns = [
   path("", views.index, name="index")
]
