"""
URL configuration for the API app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/status/', views.order_status, name='order-status'),
    path('bots/', views.bot_list, name='bot-list'),
    path('balance/', views.user_balance, name='user-balance'),
    path('analytics/client/', views.client_analytics, name='client-analytics'),
    path('analytics/daily-report/', views.daily_report, name='daily-report'),
    path('monitoring/health/', views.health_check, name='health-check'),
]