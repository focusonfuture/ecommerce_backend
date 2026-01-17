from django.contrib import admin
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Category, Brand


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'is_active', 'sort_order', 'product_count')
    list_display_links = ('indented_title',)
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ('is_active', 'sort_order')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_featured', 'product_count', 'created_at')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')