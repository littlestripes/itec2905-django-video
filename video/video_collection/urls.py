from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add", views.add, name="add_video"),
    path("video_list", views.video_list, name="video_list"),
    path("video_detail/<int:video_pk>", views.video_detail, name="video_detail")
] + staticfiles_urlpatterns()
