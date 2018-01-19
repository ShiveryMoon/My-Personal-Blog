# -*- coding: utf-8 -*-
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, QueryDict, HttpResponseNotFound
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from .forms import UserRegisterForm, BlogForm, CommentForm, PictureForm, UserAvatarForm
from .models import CustomUser, Blog, Comment, Picture, Topic

import os, time, re
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

def getBlogList(blogs, api=False):
    blogList = []
    if api:
        for blog in blogs:
            blogList.append({
                'id': blog.id,
                'authorName': blog.author.username,
                'authorId': blog.author.id,
                'authorAvatar': blog.author.avatar.url,
                'title': blog.title,
                'summary': blog.summary,
                'picture': blog.picture.image.url,
                'pub_date': blog.pub_date,
                'commentsNum': blog.commentsNum,
                'topicList': [x.topic for x in blog.topics.all()],
            })
    else:
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
                'topicList': [(x.kind, x.topic) for x in blog.topics.all()],
            })
            a += 1
    return blogList

def analysisPut(rawPut):
    dict = {}
    for item in rawPut:
        list = re.split(r'[\r\n]+', item)
        dict[list[0].strip('"')] = list[1]
    return dict


'''Templates'''


class IndexView(View):
    def get(self,request):
        pageNum = int(request.GET.get('page', 1))
        allBlogs = Blog.objects.order_by('-pub_date')
        paginator = Paginator(allBlogs, 10)
        page = paginator.get_page(pageNum)
        blogs = page.object_list
        blogList = getBlogList(blogs)
        latestBlogs = allBlogs[:3]
        for blog in latestBlogs:
            blog.pubDate = timeFilter(blog.pub_date)
        return render(request, 'blog/index.html', {
            'user': request.user,
            'blogList': blogList,
            'latestBlogs': latestBlogs,
            'page': page,
        })


class CategoryView(View):
    def get(self, request, category):
        pageNum = int(request.GET.get('page', 1))
        allBlogs = Blog.objects.filter(topics__topic=category).order_by('-pub_date')
        paginator = Paginator(allBlogs, 10)
        page = paginator.get_page(pageNum)
        blogs = page.object_list
        if not blogs:
            return HttpResponseNotFound()
        blogList = getBlogList(blogs)
        latestBlogs = allBlogs[:3]
        for blog in latestBlogs:
            blog.pubDate = timeFilter(blog.pub_date)
        return render(request, 'blog/category.html', {
            'user': request.user,
            'blogList': blogList,
            'latestBlogs': latestBlogs,
            'page': page,
            'category': category
        })


class BlogView(View):
    def get(self, request, id):
        blog = get_object_or_404(Blog, id=id)
        pageNum = int(request.GET.get('page', 1))
        paginator = Paginator(blog.comment_set.all(), 6)
        page = paginator.get_page(pageNum)
        comments = page.object_list
        for comment in comments:
            comment.pubDate = timeFilter(comment.pub_date)
        blog.pubDate = timeFilter(blog.pub_date)
        blog.topicList = [(x.kind, x.topic) for x in blog.topics.all()]
        latestBlogs = Blog.objects.order_by('-pub_date')[:3]
        for lblog in latestBlogs:
            lblog.pubDate = timeFilter(blog.pub_date)
        return render(request, 'blog/blog.html',{
            'user': request.user,
            'blog': blog,
            'latestBlogs': latestBlogs,
            'comments': comments,
            'page': page
        })


class SignoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('blog:index'))


class ProfileView(View):
    def get(self, request):
        id = int(request.GET.get('id', 1))
        pos = request.GET.get('pos', 'intro')
        user = get_object_or_404(CustomUser, id=id)
        return render(request, 'blog/profile.html', {
            'user': request.user,
            'inquireUsername': user.username,
            'profileId': id,
            'can_edit': request.user.id == id,#这是防止修改他人资料的两级保险的第一级
            'is_admin': user.is_superuser,
            'pos': pos
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
            'username': user.username,
            'desc': user.description,
            'location': user.location,
            'email': user.email,
            'avatar': user.avatar.url,
            'joinDate': re.split(r'\s+', user.date_joined.__str__())[0]
        }
        return JsonResponse(resp)

    @method_decorator(login_required)
    def put(self, request, id):
        if request.user.id != id: #这种属于手动添加passes_test， 第二级保险
            return JsonResponse({'error':'You cannot update others profile'})
        user = get_object_or_404(CustomUser, id=id)
        rawPut = QueryDict(request.body, encoding=request.encoding)
        put = analysisPut(rawPut.getlist(' name', None))
        if 'password' in put: #Changing password
            user2 = authenticate(request, username=request.user.username, password=put.get('oldPassword', None))
            if user2 is not None:
                user.set_password(put.get('password'))
            else:
                return JsonResponse({'error': 'old password is wrong'})
        else:
            user.description = put.get('desc', user.description)
            user.email = put.get('email', user.email)
            user.location = put.get('location', user.location)
        user.save()
        return JsonResponse({'result':'Update user object successfully'})

    def options(self, request, *args, **kwargs): #这里可能会有问题，说不定使用默认的options就可以？
        resp = JsonResponse({'result': 'success'})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = ', '.join(self._allowed_methods())
        resp['Content-Length'] = '0'
        return resp


class APIChangeAvatarView(LoginRequiredMixin, View):
    def post(self, request, id):
        if request.user.id != id:
            return JsonResponse({'error':'You cannot update others profile'})
        user = get_object_or_404(CustomUser, id=id)
        avatarForm = UserAvatarForm(request.POST, request.FILES)
        if avatarForm.is_valid():
            if 'default/default.jpg' not in user.avatar.path:
                os.remove(user.avatar.path)
            user.avatar = avatarForm.cleaned_data['avatar']
            fmt = re.split(r'\.', user.avatar.name)[-1]
            user.avatar.name = user.username + '.%s' % fmt
            user.save()
            user.avatarToThumbtail()
            return HttpResponse()
        return JsonResponse(avatarForm.errors)


class APIBlogsView(View):
    def get(self, request):
        pageNum = int(request.GET.get('page',1))
        paginator = Paginator(Blog.objects.order_by('-pub_date'), 10)
        page = paginator.get_page(pageNum)
        blogs = page.object_list
        blogList = getBlogList(blogs, api=True)
        resp = {
            'blogList': blogList,
            'currentPage': page.number,
            'has_previous': page.has_previous(),
            'has_next': page.has_next(),
        }
        return JsonResponse(resp)


class APIBlogByIdView(View):
    def get(self, request, id):
        blog = get_object_or_404(Blog, id=id)
        topicList = [x.topic for x in blog.topics.all()]
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



class APICommentsView(View):
    def get(self,request, id):
        blogTitle = Blog.objects.get(id=id).title
        comments = Comment.objects.filter(blog_id=id)
        commentList = []
        for comment in comments:
            commentList.append({
                'user': comment.reviewer.username,
                'content': comment.content,
                'pubDate': comment.pub_date,
                'floor': comment.floor
            })
        resp={
            'blogTitle': blogTitle,
            'commentList': commentList
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



