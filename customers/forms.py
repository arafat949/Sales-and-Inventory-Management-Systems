from django import forms

from config.mixins import StyledModelForm

from .models import Customer


class CustomerForm(StyledModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'customer_type']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }
