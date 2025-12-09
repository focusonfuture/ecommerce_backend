from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<path:category_path>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<path:category_path>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Brand URLs
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<slug:slug>/edit/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<slug:slug>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
]