from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.urls import reverse

rating = {
    "like": 1,
    "dislike": -1,
    "comment": 3,
    "correct": 5,
    "question": 2,
}

class ManagerQuestion(models.Manager):
    def new_questions(self):
        return self.order_by('-time_create')

    def best_questions(self):
        return self.order_by('-rating')

class ManagerAnswer(models.Manager):
    def best_answers(self, question_id):
        return self.filter(question=question_id).order_by('-rating', '-time_create')

class ManagerTopObjects(models.Manager):
    def popular_tags(self):
        return self.get_queryset().annotate(num_questions=Count('question')).order_by('-num_questions')[:20]

    def top_users(self):
        return self.get_queryset().order_by('-rating')[:10]

class Question(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField(max_length=1000)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    rating = models.IntegerField(null=True, default=0)
    tags = models.ManyToManyField("Tag", blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    objects = models.Manager()
    question_manager = ManagerQuestion()

    @property
    def count_likes(self):
        return self.likequestion_set.count()

    @property
    def count_dislikes(self):
        return self.dislikequestion_set.count()

    @property
    def count_comments(self):
        return self.answer_set.count()

    def count_rating(self, save=True):
        rating_like = rating['like'] * self.count_likes
        rating_dislike = rating['dislike'] * self.count_dislikes
        rating_comment = rating['comment'] * self.count_comments
        self.rating = rating_like + rating_dislike + rating_comment
        if save:
            self.save()
        return self.rating

    def get_absolute_url(self):
        return reverse('question', kwargs={'question_id': self.pk})

    def __str__(self):
        return self.title

class Answer(models.Model):
    text = models.TextField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    rating = models.IntegerField(null=True, default=0)
    objects = models.Manager()
    answer_manager = ManagerAnswer()

    @property
    def count_likes(self):
        return self.likeanswer_set.count()

    @property
    def count_dislikes(self):
        return self.dislikeanswer_set.count()

    @property
    def like_difference(self):
        return self.count_likes - self.count_dislikes

    def count_rating(self, save=True):
        correct = 0
        if self.is_correct:
            correct = 1
        self.rating = rating['like'] * self.count_likes + rating['dislike'] * self.count_dislikes + correct * rating['correct']
        if save:
            self.save()
        return self.rating

    def __str__(self):
        return self.text

class Tag(models.Model):
    title = models.CharField(max_length=30, unique=True)
    objects = models.Manager()
    popular_tags_manager = ManagerTopObjects()

    @property
    def count_questions(self):
        return self.question_set.count()

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_id': self.pk})

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, related_name='profile')
    name = models.TextField(max_length=150, default=None)
    avatar = models.ImageField(upload_to='avatars/')
    rating = models.IntegerField(null=True, default=0)
    objects = models.Manager()
    top_users_manager = ManagerTopObjects()

    @property
    def count_questions(self):
        return self.user.questions.count()

    @property
    def count_answers(self):
        return self.user.answers.count()

    @property
    def count_correct(self):
        return self.user.answers.filter(is_correct=True).count()

    def count_rating(self, save=True):
        rating_question = rating['question'] * self.count_questions
        rating_answer = rating['comment'] * self.count_answers
        rating_correct = rating['correct'] * self.count_correct
        self.rating = rating_question + rating_answer + rating_correct
        if save:
            self.save()
        return self.rating

    def __str__(self):
        return self.name

class AbstractReactionQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        managed = False
        abstract = True

class AbstractReactionAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    
    class Meta:
        managed = False
        abstract = True

class LikeQuestion(AbstractReactionQuestion):
    class Meta:
        unique_together = ["user", "question"]


class LikeAnswer(AbstractReactionAnswer):
    class Meta:
        unique_together = ["user", "answer"]


class DislikeQuestion(AbstractReactionQuestion):
    class Meta:
        unique_together = ["user", "question"]


class DislikeAnswer(AbstractReactionAnswer):
    class Meta:
        unique_together = ["user", "answer"]