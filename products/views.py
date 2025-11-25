# products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import Category, Brand
from .serializers import CategorySerializer, BrandSerializer


# ==================== CATEGORY CRUD ====================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]  # Only admin can modify

    def get_queryset(self):
        """Public: only active, Admin: all"""
        if self.request.user.is_staff:
            return Category.objects.all()
        return Category.objects.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.products.exists():
            return Response(
                {"error": "Cannot delete category with products. Deactivate instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Custom actions
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Full nested category tree"""
        roots = Category.objects.filter(parent__isnull=True).order_by('sort_order')
        serializer = self.get_serializer(roots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def root(self, request):
        """Only root categories"""
        roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by('sort_order')
        serializer = self.get_serializer(roots, many=True)
        return Response(serializer.data)


# ==================== BRAND CRUD ====================
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Brand.objects.all()
        return Brand.objects.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.products.exists():
            return Response(
                {"error": "Cannot delete brand with products. Use is_active=False instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Optional: Simple APIViews if you don't want ViewSet
from rest_framework.views import APIView

class CategoryTreeView(APIView):
    def get(self, request):
        roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by('sort_order')
        serializer = CategorySerializer(roots, many=True)
        return Response(serializer.data)

class CategoryRootListView(APIView):
    def get(self, request):
        roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by('sort_order')
        serializer = CategorySerializer(roots, many=True)
        return Response(serializer.data)