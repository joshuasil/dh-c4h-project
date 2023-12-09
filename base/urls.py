from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('inbound_message', views.inbound_message, name="inbound_message"),
]
