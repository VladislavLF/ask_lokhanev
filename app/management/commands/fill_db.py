import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify
from faker import Faker
from tqdm import tqdm

from app.models import (
    Profile, Question, Answer, Tag,
    QuestionLike, AnswerLike
)

fake = Faker()

class Command(BaseCommand):
    help = 'Fill database with test data'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def handle(self, *args, **kwargs):
        ratio = kwargs['ratio']
        num_profiles = ratio
        num_questions = ratio * 10
        num_answers = ratio * 100
        num_tags = ratio
        num_likes = ratio * 200

        self.stdout.write(self.style.SUCCESS(f"Starting fill_db with ratio={ratio}"))

        self.create_profiles(num_profiles)
        profiles = list(Profile.objects.all())

        self.create_tags(num_tags)
        tags = list(Tag.objects.all())

        questions = self.create_questions(num_questions, profiles)
        self.assign_tags_to_questions(questions, tags)

        answers = self.create_answers(num_answers, profiles, questions)
        self.create_question_likes(num_likes, profiles, questions)
        self.create_answer_likes(num_likes, profiles, answers)

        self.stdout.write(self.style.SUCCESS("Finished fill_db"))

    def create_profiles(self, count):
        batch = 1000
        for i in tqdm(range(0, count, batch), desc='Creating profiles'):
            users = []
            profiles = []
            for _ in range(min(batch, count - i)):
                username = fake.user_name() + str(random.randint(1000, 9999))
                user = User(username=username, email=fake.email())
                users.append(user)
            User.objects.bulk_create(users, batch_size=batch)

            users = User.objects.all()[i:i+batch]
            for user in users:
                profiles.append(Profile(
                    login=user.username,
                    password='password123',
                    username=fake.name(),
                    email=user.email,
                    avatar='default.jpg',
                    user=user
                ))
            Profile.objects.bulk_create(profiles, batch_size=batch)

    def create_tags(self, count):
        batch = 1000
        tags = []
        for _ in tqdm(range(count), desc='Creating tags'):
            word = fake.word() + str(random.randint(0, 9999))
            tags.append(Tag(title=word, slug=slugify(word)))
        Tag.objects.bulk_create(tags, batch_size=batch)

    def create_questions(self, count, profiles):
        batch = 1000
        questions = []
        for i in tqdm(range(0, count, batch), desc='Creating questions'):
            for _ in range(min(batch, count - i)):
                questions.append(Question(
                    title=fake.sentence(nb_words=6),
                    text=fake.text(max_nb_chars=400),
                    profile=random.choice(profiles)
                ))
            Question.objects.bulk_create(questions[i:i+batch], batch_size=batch)
        return list(Question.objects.all())

    def assign_tags_to_questions(self, questions, tags):
        for question in tqdm(questions, desc="Assigning tags"):
            question.tag.set(random.sample(tags, k=random.randint(1, 3)))

    def create_answers(self, count, profiles, questions):
        batch = 1000
        answers = []
        for i in tqdm(range(0, count, batch), desc='Creating answers'):
            for _ in range(min(batch, count - i)):
                answers.append(Answer(
                    text=fake.text(max_nb_chars=300),
                    is_correct=random.choice([True, False]),
                    question=random.choice(questions),
                    profile=random.choice(profiles)
                ))
            Answer.objects.bulk_create(answers[i:i+batch], batch_size=batch)
        return list(Answer.objects.all())

    def create_question_likes(self, count, profiles, questions):
        likes = []
        seen = set()
        for _ in tqdm(range(count), desc='Creating question likes'):
            p = random.choice(profiles)
            q = random.choice(questions)
            key = (p.id, q.id)
            if key in seen:
                continue
            seen.add(key)
            likes.append(QuestionLike(
                profile=p,
                question=q,
                is_like=bool(random.getrandbits(1))
            ))
        QuestionLike.objects.bulk_create(likes, batch_size=1000)

    def create_answer_likes(self, count, profiles, answers):
        likes = []
        seen = set()
        for _ in tqdm(range(count), desc='Creating answer likes'):
            p = random.choice(profiles)
            a = random.choice(answers)
            key = (p.id, a.id)
            if key in seen:
                continue
            seen.add(key)
            likes.append(AnswerLike(
                profile=p,
                answer=a,
                is_like=bool(random.getrandbits(1))
            ))
        AnswerLike.objects.bulk_create(likes, batch_size=1000)
