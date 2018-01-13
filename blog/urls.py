from django.urls import path
from .views import IndexView, SignoutView, BlogView, AvatarChangeView, ProfileView, PWDChangeView

app_name = 'blog'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    #path('<int:id>', BlogView.as_view(), name='blog'),
    path('signout/', SignoutView.as_view(), name='signout'),
    #path('profile/', ProfileView.as_view(), name='profile'),
    #path('profile/managePwd', PWDChangeView.as_view(), name='change_pwd'),
    #path('profile/manageAvatar', AvatarChangeView.as_view(), name='change_avatar'),
]