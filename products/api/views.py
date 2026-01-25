from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions


from products.models import *
from .serializers import *


class CategoryListAPIView(ListAPIView):
    """
    Flat list of all active categories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategoryListSerializer
    permission_classes = [AllowAny]


class CategoryTreeAPIView(ListAPIView):
    """
    Nested category tree (used for menus)
    """
    serializer_class = CategoryTreeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('sort_order')


class CategoryDetailAPIView(RetrieveAPIView):
    """
    Retrieve category by full path
    Example: electronics/mobiles/smartphones
    """
    serializer_class = CategoryDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'path'

    def get_object(self):
        path = self.kwargs.get('path')
        return get_object_or_404(Category, path=path, is_active=True)




class BrandListAPIView(generics.ListAPIView):
    """
    GET: List all active brands
    """
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandListSerializer
    permission_classes = [permissions.AllowAny]


class BrandDetailAPIView(generics.RetrieveAPIView):
    """
    GET: Retrieve brand details by slug
    """
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class BrandCreateAPIView(generics.CreateAPIView):
    """
    POST: Create new brand (Admin only)
    """
    queryset = Brand.objects.all()
    serializer_class = BrandCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]


class BrandUpdateAPIView(generics.UpdateAPIView):
    """
    PUT/PATCH: Update brand (Admin only)
    """
    queryset = Brand.objects.all()
    serializer_class = BrandCreateUpdateSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]


class BrandDeleteAPIView(generics.DestroyAPIView):
    """
    DELETE: Delete brand (Admin only)
    """
    queryset = Brand.objects.all()
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]


class ProductListAPIView(generics.ListAPIView):
    """
    GET: List all active products
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]


class ProductDetailAPIView(generics.RetrieveAPIView):
    """
    GET: Retrieve product details by slug
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class ProductCreateAPIView(generics.CreateAPIView):
    """
    POST: Create new product (Admin only)
    """
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductUpdateAPIView(generics.UpdateAPIView):
    """
    PUT/PATCH: Update product (Admin only)
    """
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]


class ProductDeleteAPIView(generics.DestroyAPIView):
    """
    DELETE: Delete product (Admin only)
    """
    queryset = Product.objects.all()
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]