from rest_framework import serializers
from .models import BotAccount, Order, FollowAction, UserBalance, ClientReputation
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class BotAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotAccount
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user', 'delivered', 'status', 'created_at', 'completed_at']

class FollowActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowAction
        fields = '__all__'
        read_only_fields = ['bot', 'order', 'followed_at']

class UserBalanceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserBalance
        fields = '__all__'

class ClientReputationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = ClientReputation
        fields = '__all__'