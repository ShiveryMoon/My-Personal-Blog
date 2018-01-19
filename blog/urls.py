from django.urls import path
from .views import IndexView, CategoryView, SignoutView, BlogView, ProfileView

'''path()的顺序绝对不能变！'''
app_name = 'blog'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('signout/', SignoutView.as_view(), name='signout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('<int:id>/', BlogView.as_view(), name='blog'),
    path('<str:category>/', CategoryView.as_view(), name='category'),
]
