# urls.py (dashboard / admin app)

from django.urls import path

from .views import *
from . import views

app_name = "dashboard"

urlpatterns = [

    # =========================
    # CATEGORY URLS
    # =========================
    path(
        "categories/",
        CategoryListView.as_view(),
        name="category_list",
    ),

    path(
        "categories/create/",
        CategoryCreateView.as_view(),
        name="category_create",
    ),

    # Use <path:category_path> to support nested paths
    # Example: electronics/mobile/android
    path(
        "categories/<path:category_path>/edit/",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),

    path(
        "categories/<path:category_path>/delete/",
        CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path("categories/toggle-status/", views.toggle_category_status, name="category_toggle_status"),
    path("categories/toggle-menu/", views.toggle_category_menu, name="category_toggle_menu"),
    path("categories/soft-delete/", views.soft_delete_category, name="category_soft_delete"),


    # =========================
    # BRAND URLS
    # =========================
    path(
        "brands/",
        BrandListView.as_view(),
        name="brand_list",
    ),

    path(
        "brands/create/",
        BrandCreateView.as_view(),
        name="brand_create",
    ),

    path(
        "brands/<int:pk>/edit/",
        BrandUpdateView.as_view(),
        name="brand_update",
    ),

    path(
        "brands/<int:pk>/delete/",
        BrandDeleteView.as_view(),
        name="brand_delete",
    ),
    path("brand/toggle-status/", views.toggle_brand_status, name="brand_toggle_status"),
    path("brand/toggle-menu/", views.toggle_brand_featured, name="brand_toggle_featured"),
]
