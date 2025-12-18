# views.py (admin views for Category and Brand)

import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction,IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView,TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import *

logger = logging.getLogger(__name__)


# ==================================================
# SHARED HELPERS
# ==================================================
def staff_required(user):
    return user.is_staff


def has_products(obj):
    """Safe check for related products (future-proof)."""
    return hasattr(obj, "products") and obj.products.exists()


def toggle_field(obj, field):
    """Toggle boolean field safely."""
    setattr(obj, field, not getattr(obj, field))
    obj.save(update_fields=[field])


def get_post_id(request):
    """Safely fetch object id from POST."""
    obj_id = request.POST.get("id")
    if not obj_id:
        return None
    return obj_id


# ==================================================
# SHARED MIXIN
# ==================================================
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, _("You are not authorized to access this page."))
        return redirect(settings.LOGIN_URL)


# ==================================================
# SHARED FIELD DEFINITIONS
# ==================================================
CATEGORY_FIELDS = (
    "name", "parent", "image", "banner", "icon",
    "meta_title", "meta_description",
    "is_active", "show_in_menu", "sort_order",
)

BRAND_FIELDS = (
    "name", "description", "website_url", "logo",
    "country", "founded_year",
    "meta_title", "meta_description",
    "is_active", "is_featured", "priority",
)

PRODUCT_FIELDS = (
    "name", "category", "brand",
    "short_description", "description",
    "meta_title", "meta_description",
    "is_active", "is_featured",
    "related_products",
)



# ==================================================
# CATEGORY AJAX ACTIONS
# ==================================================
@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_category_status(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing category id")

    category = get_object_or_404(Category, id=obj_id)
    toggle_field(category, "is_active")
    return JsonResponse({"success": True, "is_active": category.is_active})


@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_category_menu(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing category id")

    category = get_object_or_404(Category, id=obj_id)
    toggle_field(category, "show_in_menu")
    return JsonResponse({"success": True, "show_in_menu": category.show_in_menu})


@login_required
@user_passes_test(staff_required)
@require_POST
def soft_delete_category(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing category id")

    category = get_object_or_404(Category, id=obj_id)

    if category.children.filter(is_active=True).exists():
        return JsonResponse({"success": False, "message": _("Category has subcategories")})

    if has_products(category):
        return JsonResponse({"success": False, "message": _("Products are linked")})

    category.is_active = False
    category.save(update_fields=["is_active"])
    return JsonResponse({"success": True})


# ==================================================
# BRAND AJAX ACTIONS
# ==================================================
@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_brand_status(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing brand id")

    brand = get_object_or_404(Brand, id=obj_id)
    toggle_field(brand, "is_active")
    return JsonResponse({"success": True, "is_active": brand.is_active})


@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_brand_featured(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing brand id")

    brand = get_object_or_404(Brand, id=obj_id)
    toggle_field(brand, "is_featured")
    return JsonResponse({"success": True, "is_featured": brand.is_featured})


@login_required
@user_passes_test(staff_required)
@require_POST
def soft_delete_brand(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing brand id")

    brand = get_object_or_404(Brand, id=obj_id)

    if has_products(brand):
        return JsonResponse({"success": False, "message": _("Products are linked")})

    brand.is_active = False
    brand.save(update_fields=["is_active"])
    return JsonResponse({"success": True})


# ==================================================
# CATEGORY VIEWS
# ==================================================
class CategoryListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Category
    template_name = "admin/categories/list.html"
    context_object_name = "categories"
    paginate_by = 50

    def get_queryset(self):
        qs = Category.objects.select_related("parent")

        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        is_active = self.request.GET.get("is_active")
        if is_active is None:
            qs = qs.filter(is_active=True)
        elif is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))

        show_in_menu = self.request.GET.get("show_in_menu")
        if show_in_menu in ("0", "1"):
            qs = qs.filter(show_in_menu=(show_in_menu == "1"))

        return qs.order_by("path")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "title": _("Categories"),
            "search_query": self.request.GET.get("search", ""),
            "filter_is_active": self.request.GET.get("is_active", ""),
            "filter_show_in_menu": self.request.GET.get("show_in_menu", ""),

            "total_count": Category.objects.count(),
            "active_count": Category.objects.filter(is_active=True).count(),
        })

        return context

class CategoryCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Category
    template_name = "admin/categories/form.html"
    success_url = reverse_lazy("dashboard:category_list")
    fields = CATEGORY_FIELDS

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Category created successfully."))
        logger.info("Category created: %s by %s", self.object, self.request.user)
        return response


class CategoryUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Category
    template_name = "admin/categories/form.html"
    success_url = reverse_lazy("dashboard:category_list")
    fields = CATEGORY_FIELDS

    def get_object(self, queryset=None):
        return get_object_or_404(Category, path=self.kwargs.get("category_path"))

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Category updated successfully."))
        logger.info("Category updated: %s by %s", self.object, self.request.user)
        return response


class CategoryDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("dashboard:category_list")

    def get_object(self, queryset=None):
        return get_object_or_404(Category, path=self.kwargs.get("category_path"))

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        category = self.get_object()

        if category.is_active:
            messages.error(request, _("Deactivate category before permanent deletion."))
            return redirect(self.success_url)

        if category.children.filter(is_active=True).exists() or has_products(category):
            messages.error(request, _("Cannot delete category with dependencies."))
            return redirect(self.success_url)

        logger.warning("Category permanently deleted: %s by %s", category, request.user)
        return super().delete(request, *args, **kwargs)


# ==================================================
# BRAND VIEWS
# ==================================================
class BrandListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Brand
    template_name = "admin/brands/list.html"
    context_object_name = "brands"
    paginate_by = 50

    def get_queryset(self):
        qs = Brand.objects.prefetch_related("products")

        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(country__icontains=search))

        is_active = self.request.GET.get("is_active")
        if is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))

        is_featured = self.request.GET.get("is_featured")
        if is_featured in ("0", "1"):
            qs = qs.filter(is_featured=(is_featured == "1"))

        return qs.order_by("-is_featured", "-priority", "name")


class BrandCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Brand
    template_name = "admin/brands/form.html"
    success_url = reverse_lazy("dashboard:brand_list")
    fields = BRAND_FIELDS

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Brand created successfully."))
        logger.info("Brand created: %s by %s", self.object, self.request.user)
        return response


class BrandUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Brand
    template_name = "admin/brands/form.html"
    success_url = reverse_lazy("dashboard:brand_list")
    fields = BRAND_FIELDS

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Brand updated successfully."))
        logger.info("Brand updated: %s by %s", self.object, self.request.user)
        return response


class BrandDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Brand
    success_url = reverse_lazy("dashboard:brand_list")

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        brand = self.get_object()

        if brand.is_active:
            messages.error(request, _("Deactivate brand before permanent deletion."))
            return redirect(self.success_url)

        if has_products(brand):
            messages.error(request, _("Cannot delete brand with linked products."))
            return redirect(self.success_url)

        logger.warning("Brand permanently deleted: %s by %s", brand, request.user)
        return super().delete(request, *args, **kwargs)



# ==================================================
# PRODUCT AJAX ACTIONS
# ==================================================@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_product_status(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing product id")

    product = get_object_or_404(Product, id=obj_id)
    toggle_field(product, "is_active")

    return JsonResponse({
        "success": True,
        "is_active": product.is_active
    })


@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_product_featured(request):
    obj_id = get_post_id(request)
    if not obj_id:
        return HttpResponseBadRequest("Missing product id")

    product = get_object_or_404(Product, id=obj_id)
    toggle_field(product, "is_featured")

    return JsonResponse({
        "success": True,
        "is_featured": product.is_featured
    })


# ==================================================
# PRODUCT LIST VIEW
# ==================================================
class ProductListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Product
    template_name = "admin/products/list.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            Product.objects
            .select_related("category", "brand")
            .prefetch_related("variants")
        )

        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(category__name__icontains=search) |
                Q(brand__name__icontains=search)
            )

        is_active = self.request.GET.get("is_active")
        if is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))

        is_featured = self.request.GET.get("is_featured")
        if is_featured in ("0", "1"):
            qs = qs.filter(is_featured=(is_featured == "1"))

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "title": _("Products"),
            "search_query": self.request.GET.get("search", ""),
            "filter_is_active": self.request.GET.get("is_active", ""),
            "filter_is_featured": self.request.GET.get("is_featured", ""),

            "total_count": Product.objects.count(),
            "active_count": Product.objects.filter(is_active=True).count(),
        })

        return context

# ==================================================
# PRODUCT CREATE VIEW
# ==================================================
class ProductCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Product
    template_name = "admin/products/form.html"
    success_url = reverse_lazy("dashboard:product_list")
    fields = PRODUCT_FIELDS

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Product created successfully."))
        logger.info(
            "Product created: %s (ID=%s) by %s",
            self.object, self.object.id, self.request.user
        )
        return response

# ==================================================
# PRODUCT UPDATE VIEW
# ==================================================
class ProductUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Product
    template_name = "admin/products/form.html"
    success_url = reverse_lazy("dashboard:product_list")
    fields = PRODUCT_FIELDS
    slug_field = "slug"
    slug_url_kwarg = "slug"

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Product updated successfully."))
        logger.info(
            "Product updated: %s (ID=%s) by %s",
            self.object, self.object.id, self.request.user
        )
        return response

# ==================================================
# PRODUCT DELETE VIEW (HARD DELETE)
# ==================================================
class ProductDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("dashboard:product_list")
    slug_field = "slug"
    slug_url_kwarg = "slug"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        product = self.get_object()

        if product.is_active:
            messages.error(
                request,
                _("Deactivate product before permanent deletion.")
            )
            return redirect(self.success_url)

        if product.variants.filter(is_active=True).exists():
            messages.error(
                request,
                _("Cannot delete product with active variants.")
            )
            return redirect(self.success_url)

        logger.warning(
            "Product permanently deleted: %s (ID=%s) by %s",
            product, product.id, request.user
        )
        return super().delete(request, *args, **kwargs)


# ==================================================
# VariantAttribute Views
# ==================================================
class VariantAttributeListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = VariantAttribute
    template_name = "admin/variant_attributes/index.html"
    context_object_name = "attributes"
    paginate_by = 20

    def get_queryset(self):
        qs = VariantAttribute.objects.prefetch_related("values")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        is_active = self.request.GET.get("is_active")
        if is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))

        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "search_query": self.request.GET.get("search", ""),
            "filter_is_active": self.request.GET.get("is_active", ""),
            "total_count": VariantAttribute.objects.count(),
            "active_count": VariantAttribute.objects.filter(is_active=True).count(),
        })
        return context

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def create_variant_attribute(request):
    name = request.POST.get("name", "").strip()

    if not name:
        return JsonResponse({
            "success": False,
            "message": _("Attribute name is required.")
        }, status=400)

    if VariantAttribute.objects.filter(name__iexact=name).exists():
        return JsonResponse({
            "success": False,
            "message": _("Attribute already exists.")
        }, status=409)

    try:
        VariantAttribute.objects.create(name=name)
    except IntegrityError:
        return JsonResponse({
            "success": False,
            "message": _("Unable to create attribute.")
        }, status=500)

    return JsonResponse({"success": True})


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def toggle_variant_attribute_status(request):
    attr_id = request.POST.get("id")

    if not attr_id:
        return JsonResponse({"success": False, "message": "Missing id"}, status=400)

    attribute = get_object_or_404(VariantAttribute, id=attr_id)

    attribute.is_active = not attribute.is_active
    attribute.save(update_fields=["is_active"])

    return JsonResponse({
        "success": True,
        "is_active": attribute.is_active
    })


class VariantAttributeManageValuesView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "admin/variant_attributes/manage_values.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        attribute = get_object_or_404(VariantAttribute, pk=self.kwargs["pk"])

        context.update({
            "attribute": attribute,
            "values": attribute.values.all().order_by("value"),
            "total_values": attribute.values.count(),
        })
        return context


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def add_variant_attribute_value(request, pk):
    attribute = get_object_or_404(VariantAttribute, pk=pk)

    value = request.POST.get("value", "").strip()
    hex_code = request.POST.get("hex_code", "").strip()

    if not value:
        return JsonResponse({
            "success": False,
            "message": _("Value is required.")
        }, status=400)

    if attribute.values.filter(value__iexact=value).exists():
        return JsonResponse({
            "success": False,
            "message": _("This value already exists.")
        }, status=409)

    try:
        VariantAttributeValue.objects.create(
            attribute=attribute,
            value=value,
            hex_code=hex_code
        )
    except IntegrityError:
        return JsonResponse({
            "success": False,
            "message": _("Unable to save value.")
        }, status=500)

    return JsonResponse({"success": True})


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def delete_variant_attribute_value(request):
    value_id = request.POST.get("id")

    if not value_id:
        return JsonResponse({"success": False, "message": "Missing id"}, status=400)

    value = get_object_or_404(VariantAttributeValue, id=value_id)

    value.delete()

    return JsonResponse({"success": True})



# ==================================================
# PRODUCT VARIANT AJAX ACTIONS
# ==================================================
@login_required
@user_passes_test(staff_required)
@require_POST
def toggle_variant_status(request):
    """
    Toggle ProductVariant active/inactive state.
    """
    variant_id = request.POST.get("id")

    if not variant_id:
        return JsonResponse(
            {"success": False, "message": _("Missing variant id")},
            status=400
        )

    variant = get_object_or_404(ProductVariant, id=variant_id)

    variant.is_active = not variant.is_active
    variant.save(update_fields=["is_active"])

    return JsonResponse({
        "success": True,
        "is_active": variant.is_active
    })

# ==================================================
# PRODUCT VARIANT LIST VIEW
# ==================================================
class ProductVariantListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    List all variants for a given product.
    """
    model = ProductVariant
    template_name = "admin/product_variants/list.html"
    context_object_name = "variants"
    paginate_by = 30

    def get_queryset(self):
        self.product = get_object_or_404(
            Product,
            slug=self.kwargs["slug"]
        )

        qs = (
            ProductVariant.objects
            .filter(product=self.product)
            .order_by("-created_at")
        )

        is_active = self.request.GET.get("is_active")
        if is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "product": self.product,
            "filter_is_active": self.request.GET.get("is_active", ""),
            "total_count": self.product.variants.count(),
            "active_count": self.product.variants.filter(is_active=True).count(),
        })
        return context


# ==================================================
# PRODUCT VARIANT CREATE VIEW
# ==================================================
class ProductVariantCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Create a new variant under a product.
    """
    model = ProductVariant
    template_name = "admin/product_variants/form.html"
    fields = (
        "sku", "price", "sale_price", "stock",
        "weight_kg", "length_cm", "width_cm", "height_cm",
        "cost_price", "tax_class", "is_active",
    )

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        return context

    def form_valid(self, form):
        form.instance.product = self.product
        messages.success(self.request, _("Variant created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "dashboard:product_variant_list",
            kwargs={"slug": self.product.slug}
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.product = self.product

        try:
            form.instance.full_clean()
            response = super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        except IntegrityError:
            form.add_error("sku", _("SKU must be unique."))
            return self.form_invalid(form)

        messages.success(self.request, _("Variant created successfully."))
        logger.info(
            "Variant created: %s for product %s by %s",
            self.object.sku,
            self.product,
            self.request.user
        )
        return response


# ==================================================
# PRODUCT VARIANT UPDATE VIEW
# ==================================================
class ProductVariantUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    Update an existing product variant.
    """
    model = ProductVariant
    template_name = "admin/product_variants/form.html"
    fields = (
        "sku", "price", "sale_price", "stock",
        "weight_kg", "length_cm", "width_cm", "height_cm",
        "cost_price", "tax_class", "is_active",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.object.product
        return context

    def get_success_url(self):
        return reverse_lazy(
            "dashboard:product_variant_list",
            kwargs={"slug": self.object.product.slug}
        )

    @transaction.atomic
    def form_valid(self, form):
        try:
            form.instance.full_clean()
            response = super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        except IntegrityError:
            form.add_error("sku", _("SKU must be unique."))
            return self.form_invalid(form)

        messages.success(self.request, _("Variant updated successfully."))
        logger.info(
            "Variant updated: %s (ID=%s) by %s",
            self.object.sku,
            self.object.id,
            self.request.user
        )
        return response



# ==================================================
# PRODUCT VARIANT DELETE VIEW
# ==================================================
class ProductVariantDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    Permanently delete a product variant.
    Allowed only if variant is inactive.
    """
    model = ProductVariant

    def get_success_url(self):
        return reverse_lazy(
            "dashboard:product_variant_list",
            kwargs={"slug": self.object.product.slug}
        )

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        variant = self.get_object()

        if variant.is_active:
            messages.error(
                request,
                _("Deactivate variant before deletion.")
            )
            return redirect(self.get_success_url())

        logger.warning(
            "Variant permanently deleted: %s (ID=%s) by %s",
            variant.sku,
            variant.id,
            request.user
        )

        return super().delete(request, *args, **kwargs)


