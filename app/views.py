from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from app.models import *
from users.forms import AnswerForm, QuestionForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Question, Answer, LikeQuestion, DislikeQuestion

def global_context():
    return {
        "popular_tags": Tag.popular_tags_manager.popular_tags(),
        "top_users": Profile.top_users_manager.top_users(),
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
        "dislikes_answer": dislikes_answer
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