from django import forms

from config.mixins import StyledModelForm

from .models import Expense


class ExpenseForm(StyledModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'description', 'expense_date']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 0:
            raise forms.ValidationError('Amount cannot be negative.')
        return amount
