"""
Serializers for the SMM BotNet API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    BotAccount, Order, FollowAction, 
    UserBalance, ClientReputation
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class BotAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotAccount
        fields = [
            'id', 'username', 'followers_count', 
            'daily_follows', 'max_follows', 'health_score', 
            'is_active', 'last_active'
        ]


class ClientReputationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientReputation
        fields = [
            'username', 'score', 'total_orders', 
            'completed_orders', 'chargebacks', 'is_blacklisted'
        ]


class UserBalanceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserBalance
        fields = ['id', 'user', 'balance', 'total_spent', 'last_updated']


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'target_username', 'quantity', 
            'delivered', 'priority', 'status', 'price_paid',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['user', 'delivered', 'status', 'price_paid', 
                           'created_at', 'updated_at', 'completed_at']


class FollowActionSerializer(serializers.ModelSerializer):
    bot = BotAccountSerializer(read_only=True)
    
    class Meta:
        model = FollowAction
        fields = [
            'id', 'bot', 'target_user', 'followed_at', 
            'unfollowed', 'success', 'error_message'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['target_username', 'quantity']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        if value > 10000:  # Reasonable limit
            raise serializers.ValidationError("Quantity too large")
        return value