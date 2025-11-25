from rest_framework import serializers
from .models import Category, Brand


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'image', 'image_url', 'icon',
            'meta_title', 'meta_description', 'is_active', 'sort_order',
            'created_at', 'updated_at', 'product_count', 'full_path', 'children'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all().order_by('sort_order'), many=True).data
        return []

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class BrandSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'website_url',
            'logo', 'logo_url', 'is_active', 'is_featured',
            'meta_title', 'meta_description', 'created_at', 'updated_at', 'product_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None