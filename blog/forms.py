from django import forms
from .models import Comment
from taggit.models import Tag


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

class SearchForm(forms.Form):
    query = forms.CharField()


class TagSelectionForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )