from rest_framework import serializers
from products.models import *


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing categories
    """

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'path',
            'icon',
            'image',
            'is_active',
            'show_in_menu',
        ]


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Recursive serializer for category tree (menu / sidebar)
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'path',
            'icon',
            'image',
            'children',
        ]

    def get_children(self, obj):
        children = obj.get_children().filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data


class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Full category detail serializer (SEO + banners)
    """
    parent = serializers.StringRelatedField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'path',
            'parent',
            'image',
            'banner',
            'icon',
            'meta_title',
            'meta_description',
            'is_active',
            'show_in_menu',
            'created_at',
            'updated_at',
        ]


class BrandListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing brands
    """

    class Meta:
        model = Brand
        fields = [
            'id',
            'name',
            'slug',
            'logo',
            'is_featured',
            'priority',
        ]


class BrandDetailSerializer(serializers.ModelSerializer):
    """
    Full brand details (SEO + metadata)
    """

    class Meta:
        model = Brand
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'website_url',
            'logo',
            'country',
            'founded_year',
            'meta_title',
            'meta_description',
            'is_active',
            'is_featured',
            'priority',
            'created_at',
        ]
        read_only_fields = ['slug', 'created_at']


class BrandCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for create & update operations
    """

    class Meta:
        model = Brand
        fields = [
            'name',
            'description',
            'website_url',
            'logo',
            'country',
            'founded_year',
            'meta_title',
            'meta_description',
            'is_active',
            'is_featured',
            'priority',
        ]



class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for product listing
    """
    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'brand',
            'is_featured',
            'average_rating',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full product details (SEO + relationships)
    """
    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    related_products = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='slug'
    )
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'brand',
            'short_description',
            'description',
            'meta_title',
            'meta_description',
            'is_active',
            'is_featured',
            'related_products',
            'average_rating',
            'created_at',
        ]
        read_only_fields = ['slug', 'created_at', 'average_rating']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating & updating products (Admin only)
    """

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'brand',
            'short_description',
            'description',
            'meta_title',
            'meta_description',
            'is_active',
            'is_featured',
            'related_products',
        ]