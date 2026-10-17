from django.conf import settings
from django.core.files.storage import default_storage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.urls import reverse


class CategoryQuerySet(models.QuerySet):
    def with_offers_count(self):
        only_published = Q(offers__status='published')
        categories = self.annotate(offers_count=Count('offers', filter=only_published))
        return categories.order_by('name')


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('skills:category_detail', kwargs={'slug': self.slug})


# shared offer fields
class OfferContent(models.Model):
    CONTENT_FIELDS = ('title', 'category', 'description', 'image', 'level', 'format', 'duration')

    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    class Format(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'

    title = models.CharField(max_length=120)
    description = models.TextField()
    image = models.ImageField(upload_to='offers/', blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.ONLINE)
    duration = models.PositiveSmallIntegerField(
        'duration (minutes)',
        validators=[MinValueValidator(15), MaxValueValidator(480)],
    )

    class Meta:
        abstract = True

    @property
    def duration_display(self):
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0 and minutes > 0:
            return f'{hours} h {minutes} min'
        if hours > 0:
            return f'{hours} h'
        return f'{minutes} min'


class SkillOfferQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published')

    def pending(self):
        return self.filter(status='pending')

    def visible_to(self, user):
        if not user.is_authenticated:
            return self.filter(status='published')
        if user.is_admin:
            return self
        return self.filter(Q(status='published') | Q(author=user))

    def with_related(self):
        return self.select_related('author', 'category')

    # call order_by after it
    def with_rating(self):
        return self.annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews', distinct=True),
        )


class SkillOffer(OfferContent):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='offers')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SkillOfferQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', '-created_at'])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('skills:offer_detail', kwargs={'pk': self.pk})

    @property
    def is_published(self):
        return self.status == 'published'

    @property
    def can_submit(self):
        return self.status == 'draft' or self.status == 'rejected'

    @property
    def pending_revision(self):
        try:
            return self.revision
        except OfferRevision.DoesNotExist:
            return None

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return user == self.author or user.is_admin

    def approve(self):
        self.status = 'published'
        self.rejection_reason = ''
        self.save()

    def reject(self, reason):
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()


# pending changes of offer
class OfferRevision(OfferContent):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REJECTED = 'rejected', 'Rejected'

    offer = models.OneToOneField(SkillOffer, on_delete=models.CASCADE, related_name='revision')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='+')  # no reverse relation
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Changes to "{self.offer}"'

    @classmethod
    def from_offer(cls, offer):
        revision = cls()
        revision.offer = offer
        revision.title = offer.title
        revision.category = offer.category
        revision.description = offer.description
        revision.image = offer.image.name
        revision.level = offer.level
        revision.format = offer.format
        revision.duration = offer.duration
        return revision

    @property
    def is_pending(self):
        return self.status == 'pending'

    def changes(self):
        offer = self.offer
        rows = []

        if offer.title != self.title:
            rows.append({'name': 'title', 'label': 'Title', 'old': offer.title, 'new': self.title})

        if offer.category != self.category:
            rows.append({'name': 'category', 'label': 'Category',
                         'old': offer.category.name, 'new': self.category.name})

        if offer.description != self.description:
            rows.append({'name': 'description', 'label': 'Description',
                         'old': offer.description, 'new': self.description})

        if offer.image.name != self.image.name:
            old_url = ''
            new_url = ''
            if offer.image:
                old_url = offer.image.url
            if self.image:
                new_url = self.image.url
            rows.append({'name': 'image', 'label': 'Image', 'old': old_url, 'new': new_url})

        if offer.level != self.level:
            rows.append({'name': 'level', 'label': 'Level',
                         'old': offer.get_level_display(), 'new': self.get_level_display()})

        if offer.format != self.format:
            rows.append({'name': 'format', 'label': 'Format',
                         'old': offer.get_format_display(), 'new': self.get_format_display()})

        if offer.duration != self.duration:
            rows.append({'name': 'duration', 'label': 'Duration (minutes)',
                         'old': offer.duration_display, 'new': self.duration_display})

        return rows

    def approve(self):
        offer = self.offer
        old_image = offer.image.name

        offer.title = self.title
        offer.category = self.category
        offer.description = self.description
        offer.image = self.image.name
        offer.level = self.level
        offer.format = self.format
        offer.duration = self.duration
        offer.save()

        self.delete()

        if old_image and old_image != offer.image.name:
            default_storage.delete(old_image)

    def reject(self, reason):
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()

    def discard(self):
        revision_image = self.image.name
        live_image = self.offer.image.name
        self.delete()
        if revision_image and revision_image != live_image:
            default_storage.delete(revision_image)


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    offer = models.ForeignKey(SkillOffer, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'offer'], name='unique_favorite'),
        ]

    def __str__(self):
        return f'{self.user} likes {self.offer}'

