from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.bookings.models import LessonRequest
from apps.reviews.models import Review
from apps.skills.models import Category, Favorite, SkillOffer

PASSWORD = 'demo12345'

USERS = [
    # username, bio, role
    ('anna', 'Python developer, 6 years in backend. I like explaining things simply.', 'user'),
    ('max', 'Guitar teacher and musician. Rock, blues and a bit of jazz.', 'user'),
    ('kate', 'UI/UX designer. Figma, design systems and portfolio reviews.', 'user'),
    ('mike', 'Marketing specialist. Helped small brands grow on social media.', 'user'),
    ('john', 'Student. Want to learn programming and music.', 'user'),
    ('lena', 'Marketing manager who wants to learn design.', 'user'),
    ('moderator', 'Site moderator.', 'admin'),
]

OFFERS = [
    # author, title, category, level, format, duration, status, description
    ('anna', 'Python for absolute beginners', 'programming', 'beginner', 'online', 60, 'published',
     'Variables, loops, functions and your first small program. No experience needed.'),
    ('anna', 'Django: build your first website', 'programming', 'intermediate', 'online', 90, 'published',
     'Models, views and templates. By the end of the lesson you will have a working site.'),
    ('anna', 'Algorithms interview preparation', 'programming', 'advanced', 'online', 120, 'pending',
     'Typical interview tasks, complexity analysis and how to explain your solution.'),
    ('max', 'Guitar chords for beginners', 'music', 'beginner', 'offline', 60, 'published',
     'First chords, strumming patterns and a simple song by the end of the lesson.'),
    ('max', 'Blues improvisation', 'music', 'advanced', 'offline', 90, 'published',
     'Pentatonic scale, bends and phrasing. Bring your own guitar.'),
    ('kate', 'Figma basics', 'design', 'beginner', 'online', 60, 'published',
     'Frames, components and auto layout. We will design a simple mobile screen together.'),
    ('kate', 'Portfolio review for designers', 'design', 'intermediate', 'online', 45, 'published',
     'I will look at your portfolio and give honest feedback on what to improve.'),
    ('kate', 'Photography composition', 'photography', 'beginner', 'offline', 90, 'draft',
     'Rule of thirds, leading lines and light. A walk with a camera around the city.'),
    ('mike', 'Social media marketing 101', 'marketing', 'beginner', 'online', 60, 'published',
     'How to plan content, measure results and grow an audience from zero.'),
]

REQUESTS = [
    # student, offer title, status, rating, review text
    ('john', 'Python for absolute beginners', 'completed', 5, 'Very clear explanations, I wrote my first script!'),
    ('lena', 'Python for absolute beginners', 'completed', 4, 'Good lesson, a bit fast at the end.'),
    ('john', 'Guitar chords for beginners', 'completed', 5, 'Max is a great teacher, I can play my first song.'),
    ('lena', 'Figma basics', 'completed', 4, 'Useful and practical.'),
    ('john', 'Blues improvisation', 'completed', 3, 'Too hard for me for now, but interesting.'),
    ('john', 'Django: build your first website', 'accepted', None, ''),
    ('lena', 'Portfolio review for designers', 'pending', None, ''),
    ('kate', 'Social media marketing 101', 'pending', None, ''),
    ('max', 'Python for absolute beginners', 'rejected', None, ''),
]

FAVORITES = [
    ('john', 'Django: build your first website'),
    ('john', 'Figma basics'),
    ('lena', 'Social media marketing 101'),
]


class Command(BaseCommand):
    help = 'Fill the database with demo users, offers, requests and reviews'

    def handle(self, *args, **options):
        # delete old demo data to run again
        usernames = []
        for username, bio, role in USERS:
            usernames.append(username)
        User.objects.filter(username__in=usernames).delete()

        users = {}
        for username, bio, role in USERS:
            user = User.objects.create_user(
                username=username, email=f'{username}@example.com', password=PASSWORD, bio=bio, role=role,
            )
            users[username] = user

        offers = {}
        for author, title, category, level, format, duration, status, description in OFFERS:
            offer = SkillOffer.objects.create(
                author=users[author],
                title=title,
                category=Category.objects.get(slug=category),
                level=level,
                format=format,
                duration=duration,
                status=status,
                description=description,
            )
            offers[title] = offer

        for student, title, status, rating, text in REQUESTS:
            lesson = LessonRequest.objects.create(
                offer=offers[title],
                student=users[student],
                status=status,
                message='Hi! I would like to take this lesson.',
            )
            if rating:
                Review.objects.create(
                    lesson_request=lesson, offer=offers[title], author=users[student], rating=rating, text=text,
                )

        for username, title in FAVORITES:
            Favorite.objects.create(user=users[username], offer=offers[title])

        self.stdout.write(self.style.SUCCESS(
            f'Demo data created. Users: {", ".join(usernames)}. Password: {PASSWORD}'
        ))
