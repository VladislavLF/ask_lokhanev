import random
import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Question, Answer, Tag, Profile, LikeQuestion, DislikeQuestion, LikeAnswer, DislikeAnswer
from faker import Faker
from tqdm import tqdm

fake = Faker()

rating_weights = {
    "like": 1,
    "dislike": -1,
    "comment": 3,
    "correct": 5,
    "question": 2,
}

class Command(BaseCommand):
    help = 'Fill the database with test data'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def handle(self, *args, **options):
        ratio = options['ratio']
        num_users = ratio
        num_tags = ratio
        num_questions = ratio * 10
        num_answers = ratio * 100
        num_reactions = ratio * 200

        def log(section):
            self.stdout.write(self.style.NOTICE(f"\n--- {section} ---"))

        start_all = time.time()

        log("Creating users")
        t = time.time()
        users = [User(username=f"user_{i}") for i in tqdm(range(num_users), desc="Users")]
        User.objects.bulk_create(users, batch_size=10000)
        users = list(User.objects.all())
        print(f"> Users created in {time.time() - t:.2f}s")

        log("Creating profiles")
        t = time.time()
        profiles = [Profile(user=u, name=fake.name(), avatar='avatars/default.png') for u in tqdm(users, desc="Profiles")]
        Profile.objects.bulk_create(profiles, batch_size=10000)
        print(f"> Profiles created in {time.time() - t:.2f}s")

        log("Creating tags")
        t = time.time()
        tags = [Tag(title=f"tag_{i}") for i in tqdm(range(num_tags), desc="Tags")]
        Tag.objects.bulk_create(tags, batch_size=10000)
        tags = list(Tag.objects.all())
        print(f"> Tags created in {time.time() - t:.2f}s")

        log("Creating questions")
        t = time.time()
        questions = []
        for _ in tqdm(range(num_questions), desc="Questions"):
            q = Question(
                title=fake.sentence(nb_words=6),
                text=fake.text(max_nb_chars=800),
                user=random.choice(users),
                rating=0
            )
            questions.append(q)
        Question.objects.bulk_create(questions, batch_size=10000)
        questions = list(Question.objects.all())
        print(f"> Questions created in {time.time() - t:.2f}s")

        log("Assigning tags to questions")
        t = time.time()
        through_model = Question.tags.through
        tag_links = []
        for q in tqdm(questions, desc="Tag Links"):
            for tag in random.sample(tags, random.randint(1, 3)):
                tag_links.append(through_model(question_id=q.id, tag_id=tag.id))
        through_model.objects.bulk_create(tag_links, batch_size=10000)
        print(f"> Tags assigned in {time.time() - t:.2f}s")

        log("Creating answers")
        t = time.time()
        answers = []
        for _ in tqdm(range(num_answers), desc="Answers"):
            is_correct = random.random() < 0.1
            likes = random.randint(0, 5)
            dislikes = random.randint(0, 3)
            answer_rating = (
                rating_weights["like"] * likes +
                rating_weights["dislike"] * dislikes +
                (rating_weights["correct"] if is_correct else 0)
            )
            answers.append(Answer(
                text=fake.text(max_nb_chars=800),
                user=random.choice(users),
                question=random.choice(questions),
                is_correct=is_correct,
                rating=answer_rating
            ))
        Answer.objects.bulk_create(answers, batch_size=10000)
        answers = list(Answer.objects.all())
        print(f"> Answers created in {time.time() - t:.2f}s")

        log("Updating question ratings")
        t = time.time()
        question_answers = {q.id: 0 for q in questions}
        for a in answers:
            question_answers[a.question_id] += 1

        for q in tqdm(questions, desc="Question ratings"):
            likes = random.randint(0, 10)
            dislikes = random.randint(0, 5)
            comment_count = question_answers.get(q.id, 0)
            q.rating = (
                rating_weights["like"] * likes +
                rating_weights["dislike"] * dislikes +
                rating_weights["comment"] * comment_count
            )
        Question.objects.bulk_update(questions, ['rating'])
        print(f"> Questions updated in {time.time() - t:.2f}s")

        log("Updating profile ratings")
        t = time.time()
        profiles = list(Profile.objects.select_related('user').all())
        for p in tqdm(profiles, desc="Profile ratings"):
            uq = p.user.questions.count()
            ua = p.user.answers.count()
            uc = p.user.answers.filter(is_correct=True).count()
            p.rating = (
                rating_weights["question"] * uq +
                rating_weights["comment"] * ua +
                rating_weights["correct"] * uc
            )
        Profile.objects.bulk_update(profiles, ['rating'])
        print(f"> Profiles updated in {time.time() - t:.2f}s")

        log("Creating reactions")
        t = time.time()
        like_q, dislike_q, like_a, dislike_a = [], [], [], []
        for _ in tqdm(range(num_reactions), desc="Reactions"):
            user = random.choice(users)
            if random.random() < 0.5:
                q = random.choice(questions)
                if random.random() < 0.5:
                    like_q.append(LikeQuestion(user=user, question=q))
                else:
                    dislike_q.append(DislikeQuestion(user=user, question=q))
            else:
                a = random.choice(answers)
                if random.random() < 0.5:
                    like_a.append(LikeAnswer(user=user, answer=a))
                else:
                    dislike_a.append(DislikeAnswer(user=user, answer=a))

        LikeQuestion.objects.bulk_create(like_q, ignore_conflicts=True, batch_size=10000)
        DislikeQuestion.objects.bulk_create(dislike_q, ignore_conflicts=True, batch_size=10000)
        LikeAnswer.objects.bulk_create(like_a, ignore_conflicts=True, batch_size=10000)
        DislikeAnswer.objects.bulk_create(dislike_a, ignore_conflicts=True, batch_size=10000)
        print(f"> Reactions created in {time.time() - t:.2f}s")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Done in {time.time() - start_all:.2f}s"))
