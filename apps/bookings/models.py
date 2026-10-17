from django.conf import settings
from django.db import models
from django.db.models import Q


class LessonRequestQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=['pending', 'accepted'])

    def incoming(self, user):
        return self.filter(offer__author=user)

    def outgoing(self, user):
        return self.filter(student=user)

    def with_related(self):
        return self.select_related('offer__author', 'offer__category', 'student')


class LessonRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    offer = models.ForeignKey('skills.SkillOffer', on_delete=models.CASCADE, related_name='requests')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_requests')
    message = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LessonRequestQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # one active request
            models.UniqueConstraint(
                fields=['offer', 'student'],
                condition=Q(status__in=['pending', 'accepted']),
                name='one_active_request_per_offer',
            ),
        ]

    def __str__(self):
        return f'{self.student} -> {self.offer} ({self.status})'

    def allowed_actions(self, user):
        is_mentor = user == self.offer.author
        is_student = user == self.student
        actions = []

        if is_mentor:
            if self.status == 'pending':
                actions.append('accept')
                actions.append('reject')
            if self.status == 'accepted':
                actions.append('complete')

        if is_student:
            if self.status == 'pending' or self.status == 'accepted':
                actions.append('cancel')

        return actions

    def perform(self, action, user):
        if action not in self.allowed_actions(user):
            return False

        if action == 'accept':
            self.status = 'accepted'
        elif action == 'reject':
            self.status = 'rejected'
        elif action == 'complete':
            self.status = 'completed'
        elif action == 'cancel':
            self.status = 'cancelled'

        self.save()
        return True

