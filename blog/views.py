# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, QueryDict
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from .forms import UserRegisterForm, BlogForm, CommentForm, PictureForm, UserAvatarForm
from .models import CustomUser, Blog, Comment, Picture, Topic

import os, time, re
from PIL import Image
from random import randint


'''Methods'''


def timeFilter(dt):
    delta = int(time.time() - dt.timestamp())
    if delta<60:
        return u'less than 1 minute'
    if delta<3600:
        return u'%s minutes age' % (delta // 60)
    if delta<86400:
        return u'%s hours ago' % (delta // 3600)
    if delta<604800:
        return u'%s days ago' % (delta // 86400)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

def getStyleList(int):
    list = [0] * int
    if int == 0:
        raise ValueError('Int cannot be 0')
    elif int == 10 :
        list[0], list[7:] = 'full', ['one-third', 'one-third', 'one-third']
        list[1:-3] = _randomPair(6)
    else:
        if int % 2 == 0 :
            list[0], list[-1] = 'full', 'full'
            list[1:-1] = _randomPair(int-2)
        else:
            list[0] = 'full'
            list[1:] = _randomPair(int-1)
    return list

def _randomPair(int):
    if int % 2 != 0 :
        raise ValueError('Int must be even')
    list=[]
    pair = {
        0:['one-half', 'one-half'],
        1:['one-third', 'two-third'],
        2:['two-third', 'one-third']
    }
    for x in [randint(0,2) for x in range(int//2)]: #本想用reduce，然而reduce不能返回list
        list += pair[x]
    return list


'''Templates'''


class IndexView(View):
    def get(self,request):
        pageNum = request.GET.get('page', 1)
        allBlogs = Blog.objects.order_by('-pub_date')
        paginator = Paginator(allBlogs, 10)
        page = paginator.get_page(pageNum)
        blogs = paginator.get_page(pageNum).object_list
        if not blogs:
            return HttpResponse()
        blogList = []
        a = 0
        styleList = getStyleList(len(blogs))
        for blog in blogs:
            blogList.append({
                'id': blog.id,
                'authorName': blog.author.username,
                'authorId': blog.author.id,
                'authorAvatar': blog.author.avatar.url,
                'title': blog.title,
                'summary': blog.summary,
                'picture': blog.picture.image.url,
                'pub_date': timeFilter(blog.pub_date),
                'style': styleList[a],
                'topicList': [(x.kind, x.topic)for x in blog.topics.all()],
            })
            a += 1
        latestBlogs = allBlogs[:3]
        for blog in latestBlogs:
            blog.pubDate = timeFilter(blog.pub_date)
        return render(request, 'blog/index.html', {
            'user': request.user,
            'blogList': blogList,
            'latestBlogs': latestBlogs,
            'page': page,
        })


class SignoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect('/blog/')


class ProfileView(View):
    def get(self, request):
        username = request.GET.get('username')
        user = get_object_or_404(CustomUser, username=username)
        canEdit = request.user.username == username
        return render(request, 'blog/profile.html', {
            'user': request.user,
            'can_edit' : canEdit
        })


class BlogView(View):
    def get(self, request, id):
        return render(request, 'blog/blog.html',{
            'blog_id' : id,
            'user': request.user
        })


class PWDChangeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'blog/manage_pwd.html', {
            'user': request.user
        })


class AvatarChangeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'blog/manage_avatar.html', {
            'user': request.user
        })


'''APIs'''


class APIAuthView(View):
    def get(self, request):
        logout(request)
        return HttpResponse()

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse()
        return JsonResponse({'result': '用户名或密码错误'})


class APIUsersView(View):
    def post(self, request):
        userForm = UserRegisterForm(request.POST)
        if userForm.is_valid():
            userData = userForm.cleaned_data
            user = CustomUser.objects.create_user(username=userData['username'], password=userData['password'])
            login(request, user)
            return HttpResponse()
        return JsonResponse(userForm.errors)


class APIUserByIdView(View):
    def get(self, request, id):
        user = get_object_or_404(CustomUser, id=id)
        resp = {
            'username' : user.username,
            'email' : user.email,
            'avatar' : user.avatar.url,
            'joinDate' : user.date_joined
        }
        return JsonResponse(resp)

    @method_decorator(login_required)
    def put(self, request, id):
        if request.user.id != id: #手动添加passes_test
            return JsonResponse({'error':'You cannot update others profile'})
        user = get_object_or_404(CustomUser, id=id)
        put = QueryDict(request.body, encoding=request.encoding)
        if 'username' in put:
            user.username = put.get('username')
            user.email = put.get('email')
        else:  #Changing password
            user.set_password(put.get('password'))
        user.save()
        return HttpResponse()

    def options(self, request, *args, **kwargs): #这里可能会有问题，说不定使用默认的options就可以？
        resp = JsonResponse({'result': 'success'})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = ', '.join(self._allowed_methods())
        resp['Content-Length'] = '0'
        return resp


class APIChangeAvatarView(LoginRequiredMixin, View):
    def post(self, request, id):
        user = get_object_or_404(CustomUser, id=id)
        avatarForm = UserAvatarForm(request.POST, request.FILES)
        if avatarForm.is_valid():
            os.remove(user.avatar.path)
            user.avatar = avatarForm.cleaned_data['avatar']
            user.save()
            user.avatarToThumbtail()
            return HttpResponse()
        return JsonResponse(avatarForm.errors)


class APIBlogsView(View):
    def get(self, request):
        page = request.GET.get('page',1)
        paginator = Paginator(Blog.objects.order_by('-pub_date'), 10)
        blogs = paginator.get_page(page).object_list
        if not blogs:
            return HttpResponse()
        id, author, title, summary, picture, pub_date, topic = [],[],[],[],[],[],[]
        styleList = getStyleList(blogs.__len__())
        for blog in blogs:
            id.append(blog.id)
            author.append(blog.author.username)
            title.append(blog.title)
            summary.append(blog.summary)
            picture.append(blog.picture.image.url)
            pub_date.append(timeFilter(blog.pub_date))
            topic.append([x.topic for x in blog.topic_set.all()])
        resp = {
            'idList': id,
            'authorList':author,
            'titleList':title,
            'summaryList':summary,
            'pictureList':picture,
            'pubDateList':pub_date,
            'topicList':topic,
            'styleList':styleList,
            'totalPage':str(paginator.num_pages),
            'currentPage':page,
        }
        return JsonResponse(resp)


class APIBlogByIdView(View):
    def get(self, request, id):
        blog = get_object_or_404(Blog, id=id)
        '''
        topicList = [x.topic for x in blog.topic_set.all()]
        resp = {
            'authorName':blog.author.username,
            'authorAvatar':blog.author.avatar.url,
            'title':blog.title,
            'summary':blog.summary,
            'content':blog.content,
            'pubDate':blog.pub_date,
            'topicList':topicList
        }
        return JsonResponse(resp)
        '''


class APICommentsView(View):
    def get(self,request, id):
        page = request.GET.get('page', 1)
        paginator = Paginator(Comment.objects.filter(blog_id=id), 10)
        comments = paginator.get_page(page)
        reviewer, content, pub_date = [],[],[]
        for comment in comments:
            reviewer.append(comment.reviewer.username)
            content.append(comment.content)
            pub_date.append(comment.pub_date)
        resp={
            'reviewerList':reviewer,
            'contentList':content,
            'pubDateList':pub_date,
            'totalPage': paginator.num_pages,
            'currentPage': page
        }
        return JsonResponse(resp)

    @method_decorator(login_required)
    def post(self, request, id):
        blog = get_object_or_404(Blog, id=id)
        commentForm = CommentForm(request.POST)
        if commentForm.is_valid():
            data = commentForm.cleaned_data
            comment = Comment(reviewer=request.user, blog=blog, content=data['content'])
            comment.save()
            return HttpResponse()
        return JsonResponse(commentForm.errors)



