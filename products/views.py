# views.py (admin views for Category and Brand)

import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Category, Brand

logger = logging.getLogger(__name__)


# ==================================================
# SHARED HELPERS
# ==================================================
def staff_required(user):
    return user.is_staff


def has_products(obj):
    """Safe check for related products (future-proof)."""
    return hasattr(obj, "product_set") and obj.product_set.exists()


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

    if category.children.exists():
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

        if category.children.exists() or has_products(category):
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
        qs = Brand.objects.all()

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
