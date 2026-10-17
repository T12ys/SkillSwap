from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Review(models.Model):
    # one review per lesson
    lesson_request = models.OneToOneField(
        'bookings.LessonRequest', on_delete=models.CASCADE, related_name='review',
    )
    offer = models.ForeignKey('skills.SkillOffer', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_written')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name='rating_between_1_and_5'),
        ]

    def __str__(self):
        return f'{self.author} -> {self.offer}: {self.rating}'
