from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, UpdateView

from apps.bookings.models import LessonRequest

from .forms import ReviewForm
from .models import Review


def offer_reviews_url(offer):
    return offer.get_absolute_url() + '#reviews'


class ReviewCreateView(LoginRequiredMixin, CreateView):
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.lesson_request = get_object_or_404(
            LessonRequest.objects.select_related('offer'),
            pk=kwargs['pk'], student=request.user, status='completed',
        )

        existing_review = Review.objects.filter(lesson_request=self.lesson_request).first()
        if existing_review:
            return redirect('reviews:edit', pk=existing_review.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer'] = self.lesson_request.offer
        return context

    def form_valid(self, form):
        review = form.instance
        review.lesson_request = self.lesson_request
        review.offer = self.lesson_request.offer
        review.author = self.request.user

        try:
            # catch db duplicate
            with transaction.atomic():
                review.save()
        except IntegrityError:
            messages.error(self.request, 'You have already reviewed this lesson.')
            return redirect(self.lesson_request.offer)

        messages.success(self.request, 'Thank you for your review!')
        return redirect(offer_reviews_url(review.offer))


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'

    def get_queryset(self):
        return Review.objects.filter(author=self.request.user).select_related('offer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer'] = self.object.offer
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Review updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return offer_reviews_url(self.object.offer)


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'reviews/review_confirm_delete.html'
    context_object_name = 'review'

    def get_queryset(self):
        reviews = Review.objects.select_related('offer', 'author')
        if self.request.user.is_admin:
            return reviews
        return reviews.filter(author=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Review deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return offer_reviews_url(self.object.offer)

