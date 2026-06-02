"""
Views for the SMM BotNet API.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Order, BotAccount, UserBalance, ClientReputation
from .serializers import (
    OrderSerializer, OrderCreateSerializer, BotAccountSerializer,
    UserBalanceSerializer, ClientReputationSerializer
)
from bots.tasks import process_pending_orders, monitor_bots_health


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        # In a real implementation, we would:
        # 1. Check user balance
        # 2. Calculate price
        # 3. Deduct from balance
        # 4. Set priority based on quantity/time
        # 5. Save order
        # For now, we'll simulate
        order = serializer.save(user=self.request.user)
        
        # Simulate price calculation ($0.01 per follow)
        order.price_paid = order.quantity * 0.01
        order.save()
        
        # Deduct from balance (simulation)
        try:
            balance = UserBalance.objects.get(user=self.request.user)
            if balance.balance >= order.price_paid:
                balance.balance -= order.price_paid
                balance.total_spent += order.price_paid
                balance.save()
                
                # Update client reputation
                reputation, _ = ClientReputation.objects.get_or_create(
                    username=self.request.user.username
                )
                reputation.total_orders += 1
                reputation.save()
                
                # Send to processing queue (in real app, use Celery)
                # process_pending_orders.delay()
            else:
                order.status = 'failed'
                order.save()
                raise ValueError("Insufficient balance")
        except UserBalance.DoesNotExist:
            order.status = 'failed'
            order.save()
            raise ValueError("User balance not found")


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_status(request, order_id):
    """Get detailed status of an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bot_list(request):
    """List available bots (read-only)"""
    bots = BotAccount.objects.filter(is_active=True)
    serializer = BotAccountSerializer(bots, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_balance(request):
    """Get user's current balance"""
    try:
        balance = UserBalance.objects.get(user=request.user)
        serializer = UserBalanceSerializer(balance)
        return Response(serializer.data)
    except UserBalance.DoesNotExist:
        # Create default balance for new user
        balance = UserBalance.objects.create(user=request.user, balance=100.00)
        serializer = UserBalanceSerializer(balance)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_analytics(request):
    """Get analytics for the client"""
    user = request.user
    
    # Order statistics
    orders = Order.objects.filter(user=user)
    stats = orders.aggregate(
        total_orders=Count('id'),
        completed_orders=Count('id', filter=models.Q(status='completed')),
        pending_orders=Count('id', filter=models.Q(status='pending')),
        total_spent=Sum('price_paid'),
        avg_order_size=Avg('quantity')
    )
    
    # Recent orders
    recent_orders = orders.order_by('-created_at')[:5]
    recent_serializer = OrderSerializer(recent_orders, many=True)
    
    # Client reputation
    try:
        reputation = ClientReputation.objects.get(username=user.username)
        reputation_serializer = ClientReputationSerializer(reputation)
    except ClientReputation.DoesNotExist:
        reputation_serializer = None
    
    return Response({
        'order_stats': stats,
        'recent_orders': recent_serializer.data,
        'reputation': reputation_serializer.data if reputation_serializer else None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_report(request):
    """Generate daily report for admin/monitoring"""
    # In a real app, this would be restricted to staff users
    today = timezone.now().date()
    
    orders_today = Order.objects.filter(
        created_at__date=today
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=models.Q(status='completed')),
        revenue=Sum('price_paid')
    )
    
    bots_stats = BotAccount.objects.aggregate(
        active_bots=Count('id', filter=models.Q(is_active=True)),
        avg_health=Avg('health_score')
    )
    
    return Response({
        'date': today.isoformat(),
        'orders': orders_today,
        'bots': bots_stats
    })


@api_view(['GET'])
def health_check(request):
    """Health monitoring endpoint"""
    try:
        # Check database
        BotAccount.objects.first()
        
        # Check Redis (simplified)
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)