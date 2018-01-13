from django.forms import ModelForm

from .models import CustomUser, Blog, Comment, Picture


class UserRegisterForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']


class UserAvatarForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['avatar']


class BlogForm(ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'summary', 'content']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']


class PictureForm(ModelForm):
    class Meta:
        model = Picture
        fields = ['image']