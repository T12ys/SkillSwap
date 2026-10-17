from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView

from apps.accounts.mixins import NotBannedMixin
from apps.skills.models import SkillOffer
from apps.utils import redirect_back

from .forms import LessonRequestForm
from .models import LessonRequest


class RequestCreateView(NotBannedMixin, CreateView):
    form_class = LessonRequestForm
    template_name = 'bookings/request_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.offer = get_object_or_404(
            SkillOffer.objects.select_related('author'), pk=kwargs['pk'], status='published',
        )
        if request.user == self.offer.author:
            messages.error(request, 'You cannot request a lesson on your own offer.')
            return redirect(self.offer)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['student'] = self.request.user
        kwargs['offer'] = self.offer
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer'] = self.offer
        return context

    def form_valid(self, form):
        try:
            # catch db duplicate
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, 'You already have an active request for this offer.')
            return self.form_invalid(form)

        messages.success(self.request, 'Request sent! The mentor will accept or decline it.')
        return redirect('bookings:my_requests')


class MyRequestsView(LoginRequiredMixin, ListView):
    template_name = 'bookings/my_requests.html'
    context_object_name = 'lesson_requests'
    paginate_by = 15

    def get_box(self):
        if self.request.GET.get('box') == 'outgoing':
            return 'outgoing'
        return 'incoming'

    def get_current_status(self):
        status = self.request.GET.get('status', '')
        if status in LessonRequest.Status.values:
            return status
        return ''

    def get_requests_of_box(self):
        user = self.request.user
        if self.get_box() == 'outgoing':
            return LessonRequest.objects.filter(student=user)
        return LessonRequest.objects.filter(offer__author=user)

    def get_queryset(self):
        requests = self.get_requests_of_box()
        requests = requests.with_related().select_related('review')
        status = self.get_current_status()
        if status:
            requests = requests.filter(status=status)
        return requests

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        for lesson_request in context['lesson_requests']:
            lesson_request.actions = lesson_request.allowed_actions(user)

        all_requests = self.get_requests_of_box()
        status_tabs = [('', 'All', all_requests.count())]
        for value, label in LessonRequest.Status.choices:
            status_tabs.append((value, label, all_requests.filter(status=value).count()))

        context['status_tabs'] = status_tabs
        context['box'] = self.get_box()
        context['current_status'] = self.get_current_status()
        return context


class RequestActionView(LoginRequiredMixin, View):
    def post(self, request, pk, action):
        lesson_request = get_object_or_404(
            LessonRequest.objects.select_related('offer'),
            Q(student=request.user) | Q(offer__author=request.user),
            pk=pk,
        )

        if lesson_request.perform(action, request.user):
            if action == 'accept':
                messages.success(request, 'Request accepted. Contact the student to arrange the lesson.')
            elif action == 'reject':
                messages.success(request, 'Request rejected.')
            elif action == 'complete':
                messages.success(request, 'Lesson marked as completed.')
            elif action == 'cancel':
                messages.success(request, 'Request cancelled.')
        else:
            messages.error(request, 'This action is not available for the request.')

        return redirect_back(request, 'bookings:my_requests')

