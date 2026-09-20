from django import forms

from config.mixins import StyledModelForm

from .models import Supplier


class SupplierForm(StyledModelForm):
    class Meta:
        model = Supplier
        fields = ['company_name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }
