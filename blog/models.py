from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

import os, re
from PIL import Image


class CustomUser(AbstractUser):
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', default='default/default.jpg', max_length=100)

    def __str__(self):
        return self.username

    def avatarToThumbtail(self):
        fmt = re.split(r'\.', self.avatar.name)[-1]
        self.avatar.name = 'avatars/' + self.username + '.%s' % fmt
        size = (128, 128)
        im = Image.open(self.avatar.path)
        im.thumbnail(size)
        im.save(self.avatar.path)

    def delete(self, *args, **kwargs):
        path = self.avatar.path
        if path:
            os.remove(path)
        super(CustomUser, self).delete(*args, **kwargs)


class Topic(models.Model):
    Blog_Kind_Choices = [
        ('default', 'gray'),
        ('primary', 'dark blue'),
        ('success', 'green'),
        ('info', 'light blue'),
        ('warning', 'orange'),
        ('danger', 'red'),
    ]
    topic = models.CharField(max_length=20)
    kind = models.CharField(max_length=10, choices=Blog_Kind_Choices)

    class Meta:
        verbose_name = 'Topics'
        verbose_name_plural = verbose_name

    def __str__(self):
        return 'Topic of %s' % self.topic


class Picture(models.Model):
    image = models.ImageField(upload_to='pictures/', max_length=100)

    class Meta:
        verbose_name = 'Pictures'
        verbose_name_plural = verbose_name

    def __str__(self):
        return 'Picture of ' + self.image.name

    def save(self, *args, **kwargs):
        super(Picture, self).save(*args, **kwargs)
        size = (800, 800)
        im = Image.open(self.image.path)
        im.thumbnail(size)
        im.save(self.image.path)

    def delete(self, *args, **kwargs):
        path = self.image.path
        if path:
            os.remove(path)
        super(Picture, self).delete(*args, **kwargs)


class Blog(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    topics = models.ManyToManyField(Topic)
    picture = models.OneToOneField(Picture, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    summary = models.CharField(max_length=300)
    content = models.TextField()
    pub_date = models.DateTimeField('date published the blog')
    commentsNum = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Blogs'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Comment(models.Model):
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    content = models.TextField()
    pub_date = models.DateTimeField('date published the comment')
    floor = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Comments'
        verbose_name_plural = verbose_name

    def __str__(self):
        return 'Comment by ' + self.reviewer.username + ' in ' + self.blog.title

    def save(self, *args, **kwargs):
        self.blog.commentsNum += 1
        self.blog.save()
        self.floor = self.blog.commentsNum
        self.pub_date = timezone.now()
        super(Comment, self).save(*args, **kwargs)

