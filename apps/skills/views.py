from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import NotBannedMixin
from apps.bookings.models import LessonRequest
from apps.utils import ReselectFileHintMixin, redirect_back

from .filters import OfferFilter
from .forms import OfferRevisionForm, SkillOfferForm
from .models import Category, Favorite, OfferRevision, SkillOffer

POPULAR_MIN_RATING = 4


class OfferDetailView(DetailView):
    template_name = 'skills/offer_detail.html'
    context_object_name = 'offer'

    def get_queryset(self):
        offers = SkillOffer.objects.with_related().with_rating().select_related('revision')
        return offers.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer = self.object
        user = self.request.user

        context['completed_lessons'] = offer.requests.filter(status='completed').count()
        context['reviews'] = offer.reviews.select_related('author')

        if user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(user=user, offer=offer).exists()

            if user != offer.author:
                my_requests = LessonRequest.objects.filter(offer=offer, student=user)
                context['active_request'] = my_requests.filter(status__in=['pending', 'accepted']).first()
                context['reviewable_request'] = my_requests.filter(
                    status='completed', review__isnull=True,
                ).first()

        return context


class OfferCreateView(NotBannedMixin, ReselectFileHintMixin, CreateView):
    form_class = SkillOfferForm
    template_name = 'skills/offer_form.html'

    def form_valid(self, form):
        offer = form.instance
        offer.author = self.request.user

        if self.request.POST.get('action') == 'submit':
            offer.status = 'pending'
            messages.success(self.request, 'Offer sent to moderation. It will appear after admin approval.')
        else:
            offer.status = 'draft'
            messages.success(self.request, 'Offer saved as draft.')

        return super().form_valid(form)


class OfferUpdateView(NotBannedMixin, ReselectFileHintMixin, UpdateView):
    model = SkillOffer
    form_class = SkillOfferForm
    template_name = 'skills/offer_form.html'
    context_object_name = 'offer'

    def dispatch(self, request, *args, **kwargs):
        offer = get_object_or_404(SkillOffer, pk=kwargs['pk'])
        user = request.user
        # published edits need moderation
        if offer.is_published and user == offer.author and not user.is_admin:
            return redirect('skills:offer_revise', pk=offer.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        offer = super().get_object(queryset)
        if not offer.can_edit(self.request.user):
            raise PermissionDenied('You can only edit your own offers.')
        return offer

    def form_valid(self, form):
        offer = form.instance
        is_author = offer.author == self.request.user
        action = self.request.POST.get('action')

        if offer.is_published:
            messages.success(self.request, 'Offer updated.')
        elif is_author and action == 'submit':
            offer.status = 'pending'
            messages.success(self.request, 'Offer sent to moderation.')
        elif is_author and action == 'draft':
            offer.status = 'draft'
            messages.success(self.request, 'Offer saved as draft.')
        else:
            messages.success(self.request, 'Offer updated.')

        return super().form_valid(form)


class OfferDeleteView(LoginRequiredMixin, DeleteView):
    model = SkillOffer
    template_name = 'skills/offer_confirm_delete.html'
    context_object_name = 'offer'

    def get_object(self, queryset=None):
        offer = super().get_object(queryset)
        if not offer.can_edit(self.request.user):
            raise PermissionDenied('You can only delete your own offers.')
        return offer

    def form_valid(self, form):
        offer = self.object

        images_to_delete = []
        if offer.image:
            images_to_delete.append(offer.image.name)
        revision = offer.pending_revision
        if revision and revision.image and revision.image.name != offer.image.name:
            images_to_delete.append(revision.image.name)

        offer.delete()

        for image_name in images_to_delete:
            default_storage.delete(image_name)

        messages.success(self.request, 'Offer deleted.')
        return redirect('skills:my_offers')


class OfferSubmitView(NotBannedMixin, View):
    def post(self, request, pk):
        offer = get_object_or_404(SkillOffer, pk=pk, author=request.user)
        if offer.can_submit:
            offer.status = 'pending'
            offer.save()
            messages.success(request, 'Offer sent to moderation.')
        else:
            messages.error(request, 'This offer cannot be sent to moderation.')
        return redirect(offer)


class OfferReviseView(NotBannedMixin, ReselectFileHintMixin, UpdateView):
    form_class = OfferRevisionForm
    template_name = 'skills/offer_form.html'

    def get_object(self, queryset=None):
        offer = get_object_or_404(
            SkillOffer, pk=self.kwargs['pk'], author=self.request.user, status='published',
        )
        revision = offer.pending_revision
        if revision is None:
            revision = OfferRevision.from_offer(offer)
        return revision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer'] = self.object.offer
        context['is_revision'] = True
        return context

    def form_valid(self, form):
        revision = form.instance
        revision.status = 'pending'
        revision.rejection_reason = ''
        messages.success(
            self.request,
            'Changes sent to moderation. The current version stays visible until they are approved.',
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.offer.get_absolute_url()


class OfferRevisionDiscardView(LoginRequiredMixin, View):
    def post(self, request, pk):
        revision = get_object_or_404(OfferRevision, offer__pk=pk, offer__author=request.user)
        offer = revision.offer
        revision.discard()
        messages.success(request, 'Changes discarded.')
        return redirect(offer)


class MyOffersView(LoginRequiredMixin, ListView):
    template_name = 'skills/my_offers.html'
    context_object_name = 'offers'
    paginate_by = 12

    def get_current_status(self):
        status = self.request.GET.get('status', '')
        if status in SkillOffer.Status.values:
            return status
        return ''

    def get_queryset(self):
        offers = SkillOffer.objects.filter(author=self.request.user)
        offers = offers.select_related('category', 'revision').with_rating().order_by('-created_at')
        status = self.get_current_status()
        if status:
            offers = offers.filter(status=status)
        return offers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        my_offers = SkillOffer.objects.filter(author=self.request.user)

        tabs = [('', 'All', my_offers.count())]
        for value, label in SkillOffer.Status.choices:
            tabs.append((value, label, my_offers.filter(status=value).count()))

        context['tabs'] = tabs
        context['current_status'] = self.get_current_status()
        return context


class FavoriteToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        favorite = Favorite.objects.filter(user=request.user, offer_id=pk).first()
        if favorite:
            favorite.delete()
            messages.success(request, 'Removed from favorites.')
        else:
            offer = get_object_or_404(SkillOffer, pk=pk, status='published')
            Favorite.objects.get_or_create(user=request.user, offer=offer)  # safe on double click
            messages.success(request, 'Added to favorites.')
        return redirect_back(request, reverse('skills:offer_detail', args=[pk]))


class FavoritesView(LoginRequiredMixin, ListView):
    template_name = 'skills/favorites.html'
    context_object_name = 'offers'
    paginate_by = 12

    def get_queryset(self):
        offers = SkillOffer.objects.published().filter(favorited_by__user=self.request.user)
        offers = offers.with_related().with_rating()
        return offers.order_by('-favorited_by__created_at')


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offers = SkillOffer.objects.published().with_related().with_rating()

        context['latest_offers'] = offers.order_by('-created_at')[:6]

        popular = offers.filter(avg_rating__gte=POPULAR_MIN_RATING)
        context['popular_offers'] = popular.order_by('-avg_rating', '-reviews_count')[:3]

        context['categories'] = Category.objects.with_offers_count()
        return context


class OfferBrowseView(ListView):
    template_name = 'skills/offer_list.html'
    context_object_name = 'offers'
    paginate_by = 12

    title = 'Explore'
    subtitle = 'All published skill offers, newest first.'
    default_sort = 'newest'
    hidden_filters = []

    def get_base_queryset(self):
        return SkillOffer.objects.published().with_related().with_rating()

    def get_queryset(self):
        params = self.request.GET.copy()
        if 'sort' not in params:
            params['sort'] = self.default_sort

        self.filterset = OfferFilter(params, queryset=self.get_base_queryset())
        for filter_name in self.hidden_filters:
            del self.filterset.filters[filter_name]

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filterset.form
        context['title'] = self.title
        context['subtitle'] = self.subtitle
        return context


class ExploreView(OfferBrowseView):
    pass


class PopularView(OfferBrowseView):
    title = 'Popular'
    subtitle = 'Offers rated 4+ stars by students.'
    default_sort = 'rating'
    hidden_filters = ['min_rating']

    def get_base_queryset(self):
        offers = super().get_base_queryset()
        return offers.filter(avg_rating__gte=POPULAR_MIN_RATING)


class CategoryListView(ListView):
    template_name = 'skills/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.with_offers_count()


class CategoryDetailView(OfferBrowseView):
    hidden_filters = ['category']

    def get(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=kwargs['slug'])
        self.title = self.category.name
        self.subtitle = f'Skill offers in the {self.category.name} category.'
        return super().get(request, *args, **kwargs)

    def get_base_queryset(self):
        offers = super().get_base_queryset()
        return offers.filter(category=self.category)

