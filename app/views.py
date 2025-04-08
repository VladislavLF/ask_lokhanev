from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from app.models import *

def global_context(request):
    return {
        "popular_tags": Tag.popular.all(),
        "top_users": Profile.top.all(),
        "menu": {
            "index": "Главная",
            "ask": "Задать вопрос",
            "hot": "Популярное",
        },
        "is_auth": request.user.is_authenticated,
        "user_image": request.user.profile.avatar.url if request.user.is_authenticated else "default.jpg",
    }

def paginate(objects_list, request, per_page=20):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj

def index(request):
    questions = Question.new.all()
    context = {
        "title": "Главная",
        'page_obj': paginate(questions, request),
        "questions": questions,
    }
    context.update(global_context(request))
    return render(request, 'index.html', context=context)

def hot(request):
    questions = Question.best.all()
    context = {
        "tag_name": "Популярное",
        "title": "Популярное",
        'page_obj': paginate(questions, request),
        "questions": questions,
    }
    context.update(global_context(request))
    return render(request, 'tag.html', context=context)

def tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    questions = Question.objects.filter(tag=tag)
    context = {
        "tag_name": tag.title,
        "title": "Поиск по тегу",
        'page_obj': paginate(questions, request),
        "questions": questions,
    }
    context.update(global_context(request))
    return render(request, 'tag.html', context=context)

def question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    context = {
        "title": "Вопрос",
        "question": question,
        "comments": Answer.objects.filter(question=question),
    }
    context.update(global_context(request))
    return render(request, 'question.html', context=context)

def login(request):
    context = {
        "title": "Войти",
    }
    context.update(global_context(request))
    return render(request, 'login.html', context=context)

def signup(request):
    context = {
        "title": "Регистрация",
    }
    context.update(global_context(request))
    return render(request, 'signup.html', context=context)

def ask(request):
    context = {
        "title": "Задать вопрос",
    }
    context.update(global_context(request))
    return render(request, 'ask.html', context=context)

def settings(request):
    context = {
        "title": "Профиль",
    }
    context.update(global_context(request))
    return render(request, 'settings.html', context=context)