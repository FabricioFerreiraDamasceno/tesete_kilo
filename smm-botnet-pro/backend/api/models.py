from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BotAccount(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # In production, use encrypted field
    proxy = models.CharField(max_length=200, blank=True, null=True)
    followers_count = models.IntegerField(default=0)
    daily_follows = models.IntegerField(default=0)
    max_follows = models.IntegerField(default=150)  # per day
    health_score = models.FloatField(default=100.0)  # 0-100
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

class Order(models.Model):
    PRIORITY_CHOICES = [
        (0, 'Normal'),
        (1, 'High'),
        (2, 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_username = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    delivered = models.PositiveIntegerField(default=0)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price_paid = models.DecimalField(max_length=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} for {self.target_username}"

class FollowAction(models.Model):
    bot = models.ForeignKey(BotAccount, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    target_user = models.CharField(max_length=100)
    followed_at = models.DateTimeField(default=timezone.now)
    unfollowed = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"FollowAction {self.id} - {self.target_user}"

class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_length=10, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_length=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} balance: {self.balance}"

class ClientReputation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=100)  # 0-100
    total_orders = models.PositiveIntegerField(default=0)
    chargebacks = models.PositiveIntegerField(default=0)
    is_blacklisted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} reputation: {self.score}"