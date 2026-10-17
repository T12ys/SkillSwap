from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.bookings.models import LessonRequest
from apps.reviews.models import Review
from apps.utils import ReselectFileHintMixin

from .forms import ProfileForm, RegisterForm
from .models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome to SkillSwap, {user.username}!')
        return redirect('accounts:profile', username=user.username)


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class ProfileView(DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'  # user is taken
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        me = self.request.user
        profile_user = self.object

        if me.is_authenticated:
            profile_user.can_be_banned = me.can_ban(profile_user)
            profile_user.can_change_role = me.can_change_role(profile_user)

        offers = profile_user.offers.published().select_related('category').with_rating()
        context['offers'] = offers.order_by('-created_at')

        context['completed_lessons'] = LessonRequest.objects.filter(
            offer__author=profile_user, status='completed',
        ).count()

        reviews = Review.objects.filter(offer__author=profile_user)
        context['rating'] = reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        context['reviews'] = reviews.select_related('author', 'offer')[:20]

        return context


class ProfileEditView(LoginRequiredMixin, ReselectFileHintMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accounts:profile', kwargs={'username': self.object.username})


class MentorListView(ListView):
    template_name = 'accounts/mentor_list.html'
    context_object_name = 'mentors'
    paginate_by = 12

    def get_queryset(self):
        only_published = Q(offers__status='published')

        mentors = User.objects.annotate(
            offers_count=Count('offers', filter=only_published, distinct=True),
            avg_rating=Avg('offers__reviews__rating', filter=only_published),
            reviews_count=Count('offers__reviews', filter=only_published, distinct=True),
        )
        mentors = mentors.filter(offers_count__gt=0)
        mentors = mentors.order_by('-offers_count', 'username')

        search = self.request.GET.get('q', '').strip()
        if search:
            mentors = mentors.filter(username__icontains=search)
        return mentors

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

