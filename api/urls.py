from django.urls import path

from blog.views import APIAuthView, APIUsersView, APIUserByIdView, APIChangeAvatarView, APIBlogsView, APIBlogByIdView, APICommentsView

app_name = 'api'
urlpatterns = [
    path('authenticate/', APIAuthView.as_view(), name='APIAuth'),
    path('users/', APIUsersView.as_view(), name='APIUsers'),
    path('users/<int:id>/', APIUserByIdView.as_view(), name='APIUserById'),
    path('users/<int:id>/avatar/', APIChangeAvatarView.as_view(), name='APIChangeAvatar'),
    path('blogs/', APIBlogsView.as_view(), name='APIBlogs'),
    path('blogs/<int:id>/', APIBlogByIdView.as_view(), name='APIBlogById'),
    path('blogs/<int:id>/comments/', APICommentsView.as_view(), name='APIComments'),
]