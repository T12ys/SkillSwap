from django import forms

from .models import LessonRequest


class LessonRequestForm(forms.ModelForm):
    class Meta:
        model = LessonRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Introduce yourself, tell what you want to learn and when you are available',
            }),
        }
        labels = {'message': 'Message to the mentor'}

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student')
        self.offer = kwargs.pop('offer')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.offer.author == self.student:
            raise forms.ValidationError('You cannot request a lesson on your own offer.')

        already_requested = LessonRequest.objects.filter(
            offer=self.offer, student=self.student, status__in=['pending', 'accepted'],
        ).exists()
        if already_requested:
            raise forms.ValidationError('You already have an active request for this offer.')

        return cleaned_data

    def save(self, commit=True):
        lesson_request = super().save(commit=False)
        lesson_request.student = self.student
        lesson_request.offer = self.offer
        if commit:
            lesson_request.save()
        return lesson_request

