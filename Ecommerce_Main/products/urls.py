from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [

    # ==================================================
    # CATEGORY URLS
    # ==================================================
    path(
        "categories/",
        views.CategoryListView.as_view(),
        name="category_list"
    ),

    path(
        "categories/create/",
        views.CategoryCreateView.as_view(),
        name="category_create"
    ),

    path(
        "categories/<path:category_path>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_edit"
    ),

    path(
        "categories/<path:category_path>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete"
    ),

    # ---- CATEGORY AJAX ----
    path(
        "categories/toggle-status/",
        views.toggle_category_status,
        name="category_toggle_status"
    ),

    path(
        "categories/toggle-menu/",
        views.toggle_category_menu,
        name="category_toggle_menu"
    ),

    path(
        "categories/soft-delete/",
        views.soft_delete_category,
        name="category_soft_delete"
    ),


    # ==================================================
    # BRAND URLS
    # ==================================================
    path(
        "brands/",
        views.BrandListView.as_view(),
        name="brand_list"
    ),

    path(
        "brands/create/",
        views.BrandCreateView.as_view(),
        name="brand_create"
    ),

    path(
        "brands/<int:pk>/edit/",
        views.BrandUpdateView.as_view(),
        name="brand_edit"
    ),

    path(
        "brands/<int:pk>/delete/",
        views.BrandDeleteView.as_view(),
        name="brand_delete"
    ),

    # ---- BRAND AJAX ----
    path(
        "brands/toggle-status/",
        views.toggle_brand_status,
        name="brand_toggle_status"
    ),

    path(
        "brands/toggle-featured/",
        views.toggle_brand_featured,
        name="brand_toggle_featured"
    ),

    path(
        "brands/soft-delete/",
        views.soft_delete_brand,
        name="brand_soft_delete"
    ),


    # ==================================================
    # PRODUCT URLS
    # ==================================================
    path(
        "products/",
        views.ProductListView.as_view(),
        name="product_list"
    ),

    path(
        "products/create/",
        views.ProductCreateView.as_view(),
        name="product_create"
    ),

    path(
        "products/<slug:slug>/edit/",
        views.ProductUpdateView.as_view(),
        name="product_edit"
    ),

    path(
        "products/<slug:slug>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete"
    ),

    # ---- PRODUCT AJAX ----
    path(
        "products/toggle-status/",
        views.toggle_product_status,
        name="product_toggle_status"
    ),

    path(
        "products/toggle-featured/",
        views.toggle_product_featured,
        name="product_toggle_featured"
    ),
    # ================================
    # VARIANT ATTRIBUTE 
    # ================================

    path(
        "variant-attributes/",
        views.VariantAttributeListView.as_view(),
        name="variant_attribute_index"
    ),

    path(
        "variant-attributes/create/",
        views.create_variant_attribute,
        name="variant_attribute_create"
    ),

    path(
        "variant-attributes/toggle/",
        views.toggle_variant_attribute_status,
        name="variant_attribute_toggle"
    ),

    path(
        "variant-attributes/<int:pk>/values/",
        views.VariantAttributeManageValuesView.as_view(),
        name="variant_attribute_values"
    ),

    path(
        "variant-attributes/<int:pk>/values/add/",
        views.add_variant_attribute_value,
        name="variant_value_add"
    ),

    path(
        "variant-attributes/values/delete/",
        views.delete_variant_attribute_value,
        name="variant_value_delete"
    ),
    # ==================================================
    # PRODUCT VARIANTS
    # ==================================================

    # List variants of a product
    path(
        "products/<slug:slug>/variants/",
        views.ProductVariantListView.as_view(),
        name="product_variant_list"
    ),

    # Create variant for a product
    path(
        "products/<slug:slug>/variants/create/",
        views.ProductVariantCreateView.as_view(),
        name="product_variant_create"
    ),

    # Update variant
    path(
        "variants/<int:pk>/edit/",
        views.ProductVariantUpdateView.as_view(),
        name="product_variant_update"
    ),

    # Delete variant (hard delete, inactive only)
    path(
        "variants/<int:pk>/delete/",
        views.ProductVariantDeleteView.as_view(),
        name="product_variant_delete"
    ),

    # Toggle variant active/inactive (AJAX)
    path(
        "variants/toggle-status/",
        views.toggle_variant_status,
        name="product_variant_toggle_status"
    ),
]
