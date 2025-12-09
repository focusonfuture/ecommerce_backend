# models.py
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.utils.html import mark_safe
from mptt.models import MPTTModel, TreeForeignKey
from cloudinary.models import CloudinaryField

# Configure logger
logger = logging.getLogger(__name__)


class Category(MPTTModel):
    """
    Hierarchical product category using MPTT for unlimited depth.
    Examples:
        - Electronics > Mobile Phones > Android > Samsung
        - Fashion > Women > Dresses > Summer Collection

    Features:
        - Full URL path (e.g., /shop/electronics/mobile/android)
        - Menu visibility control
        - Banner & icon support
        - SEO optimized
        - Unique names per parent
    """
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        db_index=True,
        help_text=_("Auto-generated from name. Used in URLs.")
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Category")
    )

    # Images
    image = CloudinaryField(
        'image',
        folder='ecommerce/categories/',
        blank=True,
        null=True,
        transformation={'quality': 'auto', 'fetch_format': 'auto', 'width': 600},
    )

    banner = CloudinaryField(
        'banner',
        folder='ecommerce/categories/banners/',
        blank=True,
        null=True,
        transformation={'quality': 'auto', 'fetch_format': 'auto'},
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("FontAwesome 6 class, e.g., 'fas fa-mobile-alt', 'fas fa-tshirt'"),
        verbose_name=_("Icon Class")
    )

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name=_("Meta Title"))
    meta_description = models.TextField(blank=True, verbose_name=_("Meta Description"))

    # Display & Navigation
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    show_in_menu = models.BooleanField(
        default=True,
        verbose_name=_("Show in Main Menu"),
        help_text=_("Uncheck to hide from navigation (still accessible via URL)")
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort Order"))

    # Auto-managed fields
    path = models.CharField(
        max_length=1000,
        unique=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text=_("Full URL path: electronics/mobile/android")
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['path']),
            models.Index(fields=['is_active']),
            models.Index(fields=['show_in_menu']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                name='unique_category_name_per_parent'
            )
        ]

    def __str__(self):
        return self.get_full_path()

    def save(self, *args, **kwargs):
        # Generate slug if not exists
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Category.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        # Build hierarchical path
        if self.parent:
            self.path = f"{self.parent.path}/{self.slug}".lstrip('/')
        else:
            self.path = self.slug

        # Ensure path is unique
        if Category.objects.filter(path=self.path).exclude(pk=self.pk).exists():
            original_path = self.path
            counter = 1
            while Category.objects.filter(path=self.path).exclude(pk=self.pk).exists():
                self.path = f"{original_path}-{counter}"
                counter += 1

        super().save(*args, **kwargs)
        logger.info(f"Category saved: {self} (path: /{self.path})")

    def get_absolute_url(self):
        """Returns URL like /shop/electronics/mobile/android/"""
        return reverse('category_detail', kwargs={'category_path': self.path})

    @property
    def product_count(self):
        """Count of active products in this category and subcategories"""
        from products.models import Product  # Avoid circular import
        return Product.objects.filter(
            category__in=self.get_descendants(include_self=True),
            is_active=True
        ).distinct().count()

    def get_full_path(self):
        """Human readable: Electronics > Mobile Phones > Android"""
        ancestors = self.get_ancestors(include_self=True)
        return " > ".join([cat.name for cat in ancestors])

    # Admin preview
    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="80" height="80" style="object-fit: contain; border-radius: 4px;">')
        return "(No image)"
    image_preview.short_description = _("Preview")

    def banner_preview(self):
        if self.banner:
            return mark_safe(f'<img src="{self.banner.url}" width="200" height="80" style="object-fit: cover; border-radius: 4px;">')
        return "(No banner)"
    banner_preview.short_description = _("Banner Preview")


class Brand(models.Model):
    """
    Brand/Manufacturer model with logo, country, and featured status.
    Used for filtering and brand pages.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Brand Name"))
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        db_index=True,
        help_text=_("Auto-generated from name")
    )

    description = models.TextField(blank=True, verbose_name=_("Description"))
    website_url = models.URLField(blank=True, null=True, verbose_name=_("Official Website"))

    # Logo
    logo = CloudinaryField(
        'logo',
        folder='ecommerce/brands/',
        blank=True,
        null=True,
        transformation=[
            {'width': 400, 'height': 400, 'crop': 'limit'},
            {'quality': 'auto', 'format': 'webp'}
        ],
    )

    # Extra info
    country = models.CharField(max_length=100, blank=True, verbose_name=_("Country of Origin"))
    founded_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("Founded Year"),
        help_text=_("e.g., 1903 for Ford")
    )

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name=_("Meta Title"))
    meta_description = models.TextField(blank=True, verbose_name=_("Meta Description"))

    # Status & Display
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Brand"))
    priority = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Higher = appears first in featured sections"),
        verbose_name=_("Display Priority")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        ordering = ['-is_featured', '-priority', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured', 'priority']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        super().save(*args, **kwargs)
        logger.info(f"Brand saved: {self.name} (featured: {self.is_featured})")

    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        from products.models import Product
        return Product.objects.filter(brand=self, is_active=True).count()

    def logo_preview(self):
        if self.logo:
            return mark_safe(f'<img src="{self.logo.url}" width="100" height="60" style="object-fit: contain;">')
        return "(No logo)"
    logo_preview.short_description = _("Logo")