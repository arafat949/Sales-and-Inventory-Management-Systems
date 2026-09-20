from django.conf import settings
from django.db import models


class Forecast(models.Model):
    class Period(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        MONTHLY = 'MONTHLY', 'Monthly'

    period_type = models.CharField(max_length=10, choices=Period.choices, default=Period.MONTHLY)
    forecast_date = models.DateField(help_text='The future period being forecast')
    estimated_revenue = models.DecimalField(max_digits=14, decimal_places=2)
    model_used = models.CharField(max_length=100, default='Linear Regression')
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='forecasts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Forecast for {self.forecast_date} - {self.estimated_revenue}"
