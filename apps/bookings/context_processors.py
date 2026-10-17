from .models import LessonRequest


def requests(request):
    if not request.user.is_authenticated:
        return {}

    count = LessonRequest.objects.filter(offer__author=request.user, status='pending').count()
    return {'incoming_requests_count': count}

