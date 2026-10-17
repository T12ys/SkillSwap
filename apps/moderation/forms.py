from django import forms


class RejectForm(forms.Form):
    reason = forms.CharField(
        label='Reason for rejection',
        min_length=10,
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explain what the author should fix'}),
    )

