# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)  # Clean URLs without trailing slash
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'brands', views.BrandViewSet, basename='brand')

urlpatterns = [
    path('', include(router.urls)),

    # Extra useful endpoints
    path('categories/tree', views.CategoryTreeView.as_view(), name='category-tree'),
    path('categories/root', views.CategoryRootListView.as_view(), name='category-root'),
]