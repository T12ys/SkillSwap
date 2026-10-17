from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.accounts.mixins import AdminRequiredMixin
from apps.accounts.models import User
from apps.skills.models import OfferRevision, SkillOffer
from apps.utils import redirect_back

from .forms import RejectForm


class ModerationQueueView(AdminRequiredMixin, TemplateView):
    template_name = 'moderation/queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pending_offers = SkillOffer.objects.filter(status='pending')
        context['pending_offers'] = pending_offers.with_related().order_by('updated_at')

        pending_revisions = OfferRevision.objects.filter(status='pending')
        pending_revisions = pending_revisions.select_related('offer__author', 'category')
        context['pending_revisions'] = pending_revisions.order_by('updated_at')

        return context


class OfferModerateView(AdminRequiredMixin, DetailView):
    template_name = 'moderation/offer_review.html'
    context_object_name = 'offer'

    def get_queryset(self):
        return SkillOffer.objects.filter(status='pending').with_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'reject_form' not in context:
            context['reject_form'] = RejectForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        offer = self.object

        if request.POST.get('action') == 'approve':
            offer.approve()
            messages.success(request, 'Offer published.')
            return redirect('moderation:queue')

        reject_form = RejectForm(request.POST)
        if reject_form.is_valid():
            offer.reject(reject_form.cleaned_data['reason'])
            messages.success(request, 'Offer rejected. The author will see the reason.')
            return redirect('moderation:queue')

        context = self.get_context_data(reject_form=reject_form)
        return self.render_to_response(context)


class RevisionModerateView(AdminRequiredMixin, DetailView):
    template_name = 'moderation/revision_review.html'
    context_object_name = 'revision'

    def get_queryset(self):
        revisions = OfferRevision.objects.filter(status='pending')
        return revisions.select_related('offer__author', 'offer__category', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'reject_form' not in context:
            context['reject_form'] = RejectForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        revision = self.object

        if request.POST.get('action') == 'approve':
            revision.approve()
            messages.success(request, 'Changes approved and published.')
            return redirect('moderation:queue')

        reject_form = RejectForm(request.POST)
        if reject_form.is_valid():
            revision.reject(reject_form.cleaned_data['reason'])
            messages.success(request, 'Changes rejected. The author will see the reason.')
            return redirect('moderation:queue')

        context = self.get_context_data(reject_form=reject_form)
        return self.render_to_response(context)


class UserListView(AdminRequiredMixin, ListView):
    template_name = 'moderation/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        users = User.objects.annotate(
            offers_count=Count('offers', filter=Q(offers__status='published')),
        )
        users = users.order_by('-is_superuser', 'role', 'username')

        search = self.request.GET.get('q', '').strip()
        if search:
            users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))

        user_filter = self.request.GET.get('filter')
        if user_filter == 'admins':
            users = users.filter(Q(role='admin') | Q(is_superuser=True))
        elif user_filter == 'banned':
            users = users.filter(is_banned=True)

        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        me = self.request.user

        for target in context['users']:
            target.can_be_banned = me.can_ban(target)
            target.can_change_role = me.can_change_role(target)

        context['current_filter'] = self.request.GET.get('filter', '')
        context['query'] = self.request.GET.get('q', '')
        return context


class UserActionView(AdminRequiredMixin, View):
    def post(self, request, pk, action):
        target = get_object_or_404(User, pk=pk)
        me = request.user

        if action == 'ban':
            if not me.can_ban(target):
                raise PermissionDenied
            target.ban()
            messages.success(request, f'{target.username} is banned.')

        elif action == 'unban':
            if not me.can_ban(target):
                raise PermissionDenied
            target.unban()
            messages.success(request, f'{target.username} is unbanned.')

        elif action == 'make_admin':
            if not me.can_change_role(target):
                raise PermissionDenied
            if target.is_banned:
                messages.error(request, 'Unban the user before making them an admin.')
            else:
                target.set_role('admin')
                messages.success(request, f'{target.username} is now an admin.')

        elif action == 'remove_admin':
            if not me.can_change_role(target):
                raise PermissionDenied
            target.set_role('user')
            messages.success(request, f'{target.username} is no longer an admin.')

        else:
            raise PermissionDenied

        return redirect_back(request, 'moderation:users')

