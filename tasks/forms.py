from django import forms
from .models import Task, Category
from django.utils import timezone

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'due_date', 'completed']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'completed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past!")
        return due_date
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty choice for category
        self.fields['category'].empty_label = "Select a category"