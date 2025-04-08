from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.urls import reverse

# Вопросы в "Популярное" (сортировка по лайкам)
class BestQuestionsModel(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            current_rating=Count('questionlike', filter=models.Q(questionlike__is_like=True)) -
                         Count('questionlike', filter=models.Q(questionlike__is_like=False))
        ).order_by('-current_rating')

# Вопросы в "Новые вопросы" (сортировка по времени создания)
class NewQuestionsModel(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('-time_create')

# 20 популярных тегов (сортировка по количеству вопросов)
class PopularTags(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            question_count=Count('question')
        ).order_by('-question_count')[:20]

# Топ-10 пользователей (сортировка по количеству ответов на вопросы)
class TopUsers(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            answer_count=Count('answer')
        ).order_by('-answer_count')[:10]

class Question(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField(max_length=1000)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    tag = models.ManyToManyField("Tag")
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)

    objects = models.Manager()
    best = BestQuestionsModel()
    new = NewQuestionsModel()

    # Количество ответов на вопрос
    @property
    def count_of_comments(self):
        return self.answer_set.count()

    # Рейтинг у вопроса
    def get_likes(self):
        likes = self.questionlike_set.filter(is_like=True).count()
        dislikes = self.questionlike_set.filter(is_like=False).count()
        return likes - dislikes

    def get_absolute_url(self):
        return reverse('question', kwargs={'question_id': self.id})

    def __str__(self):
        return self.title

class Answer(models.Model):
    text = models.TextField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)

    # Рейтинг ответа на вопрос
    @property
    def get_likes(self):
        likes = self.answerlike_set.filter(is_like=True).count()
        dislikes = self.answerlike_set.filter(is_like=False).count()
        return likes - dislikes

class Tag(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    objects = models.Manager()
    popular = PopularTags()

    # Количество вопросов у тега
    @property
    def get_count_questions(self):
        return self.question_set.count()

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_slug': self.slug})

    def __str__(self):
        return self.title

class Profile(models.Model):
    login = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    email = models.EmailField()
    avatar = models.ImageField()

    objects = models.Manager()
    top = TopUsers()

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    # Количество комментариев пользователя
    @property
    def get_count_comments(self):
        return self.answer_set.count()

    def __str__(self):
        return self.username

class QuestionLike(models.Model):
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)

    class Meta:
        unique_together = ['profile', 'question']

class AnswerLike(models.Model):
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    answer = models.ForeignKey("Answer", on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)

    class Meta:
        unique_together = ['profile', 'answer']