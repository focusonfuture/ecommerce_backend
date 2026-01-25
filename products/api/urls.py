from django.urls import path
from .views import *

urlpatterns = [
    path('categories/tree/', CategoryTreeAPIView.as_view(), name='category-tree'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<path:path>/', CategoryDetailAPIView.as_view(), name='category-detail'),


    path('brands/', BrandListAPIView.as_view(), name='brand-list'),
    path('brands/create/', BrandCreateAPIView.as_view(), name='brand-create'),
    path('brands/<slug:slug>/', BrandDetailAPIView.as_view(), name='brand-detail'),
    path('brands/<slug:slug>/update/', BrandUpdateAPIView.as_view(), name='brand-update'),
    path('brands/<slug:slug>/delete/', BrandDeleteAPIView.as_view(), name='brand-delete'),

    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/<slug:slug>/update/', ProductUpdateAPIView.as_view(), name='product-update'),
    path('products/<slug:slug>/delete/', ProductDeleteAPIView.as_view(), name='product-delete'),
]
