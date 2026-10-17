from apps.skills.models import OfferRevision, SkillOffer


def moderation(request):
    user = request.user
    if not user.is_authenticated or not user.is_admin:
        return {}

    new_offers = SkillOffer.objects.filter(status='pending').count()
    changed_offers = OfferRevision.objects.filter(status='pending').count()
    return {'moderation_count': new_offers + changed_offers}

