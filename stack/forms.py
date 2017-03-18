from django.forms import ModelForm
from stack.models import Stack

class StackForm(ModelForm):
    class Meta:
        model = Stack
        fields = [ 'name']