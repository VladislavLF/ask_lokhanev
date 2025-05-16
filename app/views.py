import json
import time
from django.db.models import Q, Value
from django.http import JsonResponse
import jwt
import requests
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from app.models import *
from ask_lokhanev.settings import CENTRIFUGO_WS_URL_PUBLISH_DATA, CENTRIFUGO_WS_URL, CENTRIFUGO_API_KEY, \
    CENTRIFUGO_SECRET_KEY
from users.forms import AnswerForm, QuestionForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Question, Answer, LikeQuestion, DislikeQuestion
from django.db.models import Value, When, Case, F

def get_centrifugo_data(user_id):
    user_id = 0 if user_id is None else user_id
    token = jwt.encode({"sub": str(user_id), "exp": int(time.time()) + 100 * 60}, CENTRIFUGO_SECRET_KEY,
                       algorithm="HS256")
    return {
        "user_token": token,
        "ws_url": CENTRIFUGO_WS_URL,
    }

def ws_add_answer(answer, question_id):
    data = json.dumps({
        "channel": f"{question_id}",
        "data": {
            "answer": {
                "id": f"{answer.id}",
                "text": f"{answer.text}",
                "user": f"{answer.user.username}",
                "avatar": f"{answer.user.profile.avatar.url}",
                "count_likes": f"{answer.count_likes}",
                "count_dislikes": f"{answer.count_dislikes}",
                "is_correct": f"{answer.is_correct}"
            }
        }

    })
    headers = {'X-API-Key': f'{CENTRIFUGO_API_KEY}', 'Content-type': 'application/json'}
    requests.post(f"{CENTRIFUGO_WS_URL_PUBLISH_DATA}", data=data, headers=headers)

def global_context():
    return {
        "menu": {
            "index": "Главная",
            "ask": "Задать вопрос",
            "hot": "Популярное",
        }
    }

def custom_404(request, exception):
    context = {
        "title": "Ошибка 404",
    }
    context.update(global_context())
    return render(request, '404.html', status=404, context=context)

def custom_403(request, exception):
    context = {
        "title": "Ошибка 403",
    }
    context.update(global_context())
    return render(request, '403.html', status=403, context=context)

def search_questions(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    words = query.split()
    exact_phrase = query.replace('"', '')

    questions = Question.objects.annotate(
        exact_title_match=Case(
            When(title__icontains=exact_phrase, then=Value(30)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        exact_text_match=Case(
            When(text__icontains=exact_phrase, then=Value(20)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        all_words_title=Case(
            When(title__iregex=r'\b' + r'\b.*\b'.join(words) + r'\b', then=Value(25)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        all_words_text=Case(
            When(text__iregex=r'\b' + r'\b.*\b'.join(words) + r'\b', then=Value(15)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        word_distance=Case(
            When(text__iregex=r'\b' + r'\b.{1,20}\b'.join(words) + r'\b', then=Value(10)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        relevance=F('exact_title_match') + F('exact_text_match') +
                  F('all_words_title') + F('all_words_text') + F('word_distance')
    ).filter(
        Q(title__icontains=exact_phrase) |
        Q(text__icontains=exact_phrase) |
        Q(title__iregex=r'\b' + r'\b'.join(words) + r'\b') |
        Q(text__iregex=r'\b' + r'\b'.join(words) + r'\b')
    ).order_by('-relevance')[:10]

    results = [{
        'title': q.title,
        'text': (q.text[:100] + '...') if len(q.text) > 100 else q.text,
        'url': q.get_absolute_url(),
        'score': q.relevance
    } for q in questions]

    return JsonResponse({'results': results})


def search_page(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return render(request, 'search.html', {
            'title': 'Поиск',
            'query': query,
            'empty_query': True
        })

    exact_phrase = query.replace('"', '')
    words = exact_phrase.split()

    questions = Question.objects.annotate(
        exact_title_match=Case(
            When(title__icontains=exact_phrase, then=Value(1)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        exact_text_match=Case(
            When(text__icontains=exact_phrase, then=Value(1)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        all_words_match=Case(
            When(title__iregex=r'\b' + r'\b.*\b'.join(words) + r'\b', then=Value(1)),
            default=Value(0),
            output_field=models.IntegerField()
        ),
        relevance=F('exact_title_match') * 3 +
                  F('exact_text_match') * 2 +
                  F('all_words_match') * 1
    ).filter(
        Q(title__icontains=exact_phrase) |
        Q(text__icontains=exact_phrase) |
        Q(title__iregex=r'\b' + r'\b'.join(words) + r'\b') |
        Q(text__iregex=r'\b' + r'\b'.join(words) + r'\b')
    ).order_by('-relevance', '-rating')

    likes, dislikes = [], []
    if request.user.is_authenticated:
        likes = list(LikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        dislikes = list(DislikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))

    context = {
        "title": f'Поиск: {query}',
        'page_obj': paginate(questions, request),
        "questions": questions,
        "likes": likes,
        "dislikes": dislikes,
        "query": query
    }
    context.update(global_context())
    return render(request, 'search.html', context=context)

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
    questions = Question.question_manager.new_questions()
    likes, dislikes = [], []
    if request.user.is_authenticated:
        likes = list(LikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        dislikes = list(DislikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
    context = {
        "title": "Главная",
        'page_obj': paginate(questions, request),
        "questions": questions,
        "likes": likes,
        "dislikes": dislikes
    }
    context.update(global_context())
    return render(request, 'index.html', context=context)

def hot(request):
    questions = Question.question_manager.best_questions()
    likes, dislikes = [], []
    if request.user.is_authenticated:
        likes = list(LikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        dislikes = list(DislikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
    context = {
        "tag_name": "Популярное",
        "title": "Популярное",
        'page_obj': paginate(questions, request),
        "questions": questions,
        "likes": likes,
        "dislikes": dislikes
    }
    context.update(global_context())
    return render(request, 'tag.html', context=context)

def tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    questions = Question.objects.filter(tags=tag).order_by('-rating')
    likes, dislikes = [], []
    if request.user.is_authenticated:
        likes = list(LikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        dislikes = list(DislikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
    context = {
        "tag_name": tag.title,
        "title": "Поиск по тегу",
        'page_obj': paginate(questions, request),
        "questions": questions,
        "likes": likes,
        "dislikes": dislikes
    }
    context.update(global_context())
    return render(request, 'tag.html', context=context)

def question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    comments = Answer.answer_manager.best_answers(question_id=question_id)
    likes_question, dislikes_question, likes_answer, dislikes_answer = [], [], [], []
    if request.user.is_authenticated:
        likes_question = list(LikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        dislikes_question = list(DislikeQuestion.objects.filter(user=request.user).values_list('question', flat=True))
        likes_answer = list(LikeAnswer.objects.filter(user=request.user).values_list('answer', flat=True))
        dislikes_answer = list(DislikeAnswer.objects.filter(user=request.user).values_list('answer', flat=True))

    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            new_answer = form.save(commit=False)
            new_answer.question = question
            new_answer.user = request.user
            new_answer.save()
            question.count_rating()
            ws_add_answer(new_answer, question_id)
            return redirect(question.get_absolute_url() + f"#comment-{new_answer.pk}")
    else:
        form = AnswerForm()

    context = {
        "title": "Вопрос",
        "question": question,
        "comments": comments,
        "form": form,
        "likes_question": likes_question,
        "dislikes_question": dislikes_question,
        "likes_answer": likes_answer,
        "dislikes_answer": dislikes_answer,
        'centrifugo': get_centrifugo_data(request.user.id)
    }
    context.update(global_context())
    return render(request, 'question.html', context=context)

def ask(request):
    if not(request.user.is_authenticated):
        return custom_403(request, exception=403)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.save()
            tags = form.cleaned_data['tags']
            for tag_title in tags:
                tag_obj, created = Tag.objects.get_or_create(title=tag_title)
                question.tags.add(tag_obj)
            return redirect(question.get_absolute_url())
    else:
        form = QuestionForm()
    context = {
        "title": "Задать вопрос",
        "form": form,
    }
    context.update(global_context())
    return render(request, 'ask.html', context=context)


@require_POST
@login_required
def rate_object(request):
    object_id = request.POST.get('id')
    action = request.POST.get('action')
    object_type = request.POST.get('type')

    if object_type not in ['question', 'answer']:
        return JsonResponse({'error': 'Неверный тип объекта'}, status=400)

    if action not in ['like', 'dislike']:
        return JsonResponse({'error': 'Неверное действие'}, status=400)

    if object_type == 'question':
        Model = Question
        LikeModel = LikeQuestion
        DislikeModel = DislikeQuestion
        lookup = {'question_id': object_id, 'user': request.user}
    else:
        Model = Answer
        LikeModel = LikeAnswer
        DislikeModel = DislikeAnswer
        lookup = {'answer_id': object_id, 'user': request.user}

    try:
        obj = Model.objects.get(pk=object_id)
    except Model.DoesNotExist:
        return JsonResponse({'error': f'{object_type.capitalize()} не найден'}, status=404)

    if action == 'like':
        if LikeModel.objects.filter(**lookup).exists():
            LikeModel.objects.filter(**lookup).delete()
        else:
            LikeModel.objects.create(**lookup)
            DislikeModel.objects.filter(**lookup).delete()
    elif action == 'dislike':
        if DislikeModel.objects.filter(**lookup).exists():
            DislikeModel.objects.filter(**lookup).delete()
        else:
            DislikeModel.objects.create(**lookup)
            LikeModel.objects.filter(**lookup).delete()

    rating = obj.count_rating()

    return JsonResponse({
        'count_likes': obj.count_likes,
        'count_dislikes': obj.count_dislikes,
        'rating': rating
    })


@require_POST
@login_required
def toggle_correct_answer(request):
    question_id = request.POST.get('question_id')
    answer_id = request.POST.get('answer_id')
    mark = request.POST.get('mark') == 'true'

    try:
        question = Question.objects.get(pk=question_id)
        answer = Answer.objects.get(pk=answer_id, question=question)
    except (Question.DoesNotExist, Answer.DoesNotExist):
        return JsonResponse({'error': 'Вопрос или ответ не найдены'}, status=404)

    if question.user != request.user:
        return JsonResponse({'error': 'Только автор вопроса может изменить правильность ответа'}, status=403)

    answer.is_correct = mark
    answer.save()

    answer.user.profile.count_rating()
    answer.count_rating()

    return JsonResponse({'is_correct': mark})