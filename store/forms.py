from django import forms

from store.models import ReviewRating, ProductGallery


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']