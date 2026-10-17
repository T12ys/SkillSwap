from django import forms

from apps.utils import delete_replaced_file, validate_image_size

from .models import OfferRevision, SkillOffer

OFFER_FIELDS = ['title', 'category', 'description', 'image', 'level', 'format', 'duration']

OFFER_WIDGETS = {
    'title': forms.TextInput(attrs={'placeholder': 'e.g. Python for absolute beginners'}),
    'description': forms.Textarea(attrs={
        'rows': 6, 'placeholder': 'What will the student learn? What do they need to know beforehand?',
    }),
    'image': forms.FileInput(attrs={'accept': 'image/*'}),
    'duration': forms.NumberInput(attrs={'min': 15, 'max': 480, 'step': 15}),
}

OFFER_HELP_TEXTS = {
    'duration': 'Length of one lesson, from 15 to 480 minutes.',
}


class OfferContentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Select a category'
        self.old_image_name = self.instance.image.name

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) < 30:
            raise forms.ValidationError('Description must be at least 30 characters long.')
        return description

    def clean_image(self):
        image = self.cleaned_data.get('image')
        return validate_image_size(image, max_mb=5)


class SkillOfferForm(OfferContentForm):
    class Meta:
        model = SkillOffer
        fields = OFFER_FIELDS
        widgets = OFFER_WIDGETS
        help_texts = OFFER_HELP_TEXTS

    def save(self, commit=True):
        offer = super().save(commit=commit)
        if commit:
            # revision may use it
            used_by_revision = OfferRevision.objects.filter(image=self.old_image_name).exists()
            if not used_by_revision:
                delete_replaced_file(self.old_image_name, offer.image.name)
        return offer


class OfferRevisionForm(OfferContentForm):
    class Meta:
        model = OfferRevision
        fields = OFFER_FIELDS
        widgets = OFFER_WIDGETS
        help_texts = OFFER_HELP_TEXTS

    def save(self, commit=True):
        revision = super().save(commit=commit)
        if commit:
            # keep live offer image
            is_live_offer_image = self.old_image_name == revision.offer.image.name
            if not is_live_offer_image:
                delete_replaced_file(self.old_image_name, revision.image.name)
        return revision

