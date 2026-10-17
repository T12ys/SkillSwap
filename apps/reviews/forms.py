from django import forms

from .models import Review

RATING_CHOICES = [
    (5, '★★★★★ Excellent'),
    (4, '★★★★ Good'),
    (3, '★★★ Okay'),
    (2, '★★ Poor'),
    (1, '★ Terrible'),
]


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={'required': 'Please choose a rating from 1 to 5.'},
    )

    class Meta:
        model = Review
        fields = ('rating', 'text')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'How was the lesson? What did you learn?'}),
        }
        labels = {'text': 'Review (optional)'}

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if text and len(text) < 10:
            raise forms.ValidationError('Review must be at least 10 characters long, or leave it empty.')
        return text

