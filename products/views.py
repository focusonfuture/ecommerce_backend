# views.py (e.g., in categories app or core app)
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _

from .models import Category, Brand

logger = logging.getLogger(__name__)


# ========================
#     CATEGORY VIEWS
# ========================

class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Category
    template_name = 'admin/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return Category.objects.all().select_related('parent').order_by('path')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Categories")
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Category
    fields = [
        'name', 'parent', 'image', 'banner', 'icon',
        'meta_title', 'meta_description', 'is_active',
        'show_in_menu', 'sort_order'
    ]
    template_name = 'admin/categories/form.html'
    success_url = reverse_lazy('dashboard:category_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, _(f"Category '{form.instance.name}' created successfully."))
        logger.info(f"Category created by {self.request.user}: {form.instance}")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Create New Category")
        return context


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    fields = [
        'name', 'parent', 'image', 'banner', 'icon',
        'meta_title', 'meta_description', 'is_active',
        'show_in_menu', 'sort_order'
    ]
    template_name = 'admin/categories/form.html'
    success_url = reverse_lazy('dashboard:category_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_object(self, queryset=None):
        return get_object_or_404(Category, path=self.kwargs['category_path'])

    def form_valid(self, form):
        messages.success(self.request, _(f"Category '{form.instance.name}' updated successfully."))
        logger.info(f"Category updated by {self.request.user}: {form.instance}")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Edit Category")
        return context


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'admin/categories/confirm_delete.html'
    success_url = reverse_lazy('dashboard:category_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_object(self, queryset=None):
        return get_object_or_404(Category, path=self.kwargs['category_path'])

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        if category.children.exists() or category.product_set.exists():
            messages.error(request, _(
                "Cannot delete category '{name}' because it has subcategories or products."
            ).format(name=category.name))
            return redirect('dashboard:category_list')

        success_message = _(f"Category '{category.name}' deleted successfully.")
        response = super().delete(request, *args, **kwargs)
        messages.success(request, success_message)
        logger.warning(f"Category deleted by {request.user}: {category}")
        return response


# ========================
#      BRAND VIEWS
# ========================

class BrandListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Brand
    template_name = 'admin/brands/list.html'
    context_object_name = 'brands'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return Brand.objects.all().order_by('-is_featured', '-priority', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Brands")
        return context


class BrandCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Brand
    fields = [
        'name', 'description', 'website_url', 'logo',
        'country', 'founded_year', 'meta_title',
        'meta_description', 'is_active', 'is_featured', 'priority'
    ]
    template_name = 'admin/brands/form.html'
    success_url = reverse_lazy('dashboard:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, _(f"Brand '{form.instance.name}' created successfully."))
        logger.info(f"Brand created by {self.request.user}: {form.instance}")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Create New Brand")
        return context


class BrandUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Brand
    fields = [
        'name', 'description', 'website_url', 'logo',
        'country', 'founded_year', 'meta_title',
        'meta_description', 'is_active', 'is_featured', 'priority'
    ]
    template_name = 'admin/brands/form.html'
    success_url = reverse_lazy('dashboard:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, _(f"Brand '{form.instance.name}' updated successfully."))
        logger.info(f"Brand updated by {self.request.user}: {form.instance}")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Edit Brand")
        return context


class BrandDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Brand
    template_name = 'admin/brands/confirm_delete.html'
    success_url = reverse_lazy('dashboard:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        brand = self.get_object()
        if brand.product_set.exists():
            messages.error(request, _(
                "Cannot delete brand '{name}' because it has associated products."
            ).format(name=brand.name))
            return redirect('dashboard:brand_list')

        success_message = _(f"Brand '{brand.name}' deleted successfully.")
        response = super().delete(request, *args, **kwargs)
        messages.success(request, success_message)
        logger.warning(f"Brand deleted by {request.user}: {brand}")
        return response