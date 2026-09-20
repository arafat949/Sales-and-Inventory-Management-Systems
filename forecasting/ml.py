"""
Simple, explainable sales forecasting pipeline (spec section 20):

    Historical sales data -> Data cleaning -> Feature preparation
    -> Train ML model -> Prediction -> Visualization

We aggregate completed sales revenue by calendar month and fit a Linear
Regression model against a sequential month index. This is intentionally
simple (as instructed) rather than a full time-series model — good enough
to show a trend and defend in an internship viva.
"""
import numpy as np
import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from sales.models import Sale

MODEL_NAME = 'Linear Regression'
MIN_MONTHS_REQUIRED = 3


def _load_monthly_revenue():
    """Historical sales data, aggregated by month (spec: 'Aggregate sales by day or month')."""
    qs = (
        Sale.objects.filter(status='COMPLETED')
        .annotate(month=TruncMonth('sale_date'))
        .values('month')
        .annotate(revenue=Sum('total'))
        .order_by('month')
    )
    df = pd.DataFrame(list(qs))
    if df.empty:
        return df

    df['month'] = pd.to_datetime(df['month'])
    # Data cleaning: coerce to numeric and fill any gaps with 0
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0.0)
    return df.reset_index(drop=True)


def forecast_sales(periods=3):
    """
    Returns None if there isn't enough historical data to forecast responsibly,
    otherwise a dict with historical points, forecast points, and model metadata.
    """
    from sklearn.linear_model import LinearRegression

    df = _load_monthly_revenue()
    if len(df) < MIN_MONTHS_REQUIRED:
        return None

    # Feature preparation: sequential month index as the single predictor
    df['month_index'] = np.arange(len(df))
    X = df[['month_index']].values
    y = df['revenue'].values

    model = LinearRegression()
    model.fit(X, y)
    r2_score = model.score(X, y)

    future_index = np.arange(len(df), len(df) + periods).reshape(-1, 1)
    predictions = model.predict(future_index)
    predictions = np.maximum(predictions, 0)  # revenue can't be negative

    last_month = df['month'].max()
    future_months = [last_month + pd.DateOffset(months=i) for i in range(1, periods + 1)]

    return {
        'historical': [
            {'month': row['month'], 'revenue': float(row['revenue'])}
            for _, row in df.iterrows()
        ],
        'forecast': [
            {'month': m, 'revenue': round(float(p), 2)}
            for m, p in zip(future_months, predictions)
        ],
        'model_name': MODEL_NAME,
        'coefficient': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'r2_score': round(float(r2_score), 3),
        'months_used': len(df),
    }
