# models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from cloudinary.models import CloudinaryField  # This is the best way


class Category(MPTTModel):
    """
    Hierarchical Product Category using MPTT (Modified Preorder Tree Traversal)
    Supports unlimited depth (e.g., Electronics > Mobile Phones > Android)
    """
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    slug = models.SlugField(max_length=250, unique=True, blank=True, db_index=True)

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Category")
    )

    # === Cloudinary Images ===
    image = CloudinaryField(
        folder='ecommerce/categories/',   # Organized folder in Cloudinary
        blank=True,
        null=True,
        transformation={'quality': 'auto', 'fetch_format': 'auto'},
        verbose_name=_("Category Image")
    )

    icon = models.CharField(max_length=100, blank=True, help_text="FontAwesome class (e.g., fas fa-mobile)")

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name=_("Meta Title"))
    meta_description = models.TextField(blank=True, verbose_name=_("Meta Description"))

    # Status & Ordering
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort Order"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['sort_order', 'name']
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()

    def get_full_path(self):
        ancestors = self.get_ancestors(include_self=True)
        return " > ".join([cat.name for cat in ancestors])


class Brand(models.Model):
    """
    Brand / Manufacturer model
    """
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Brand Name"))
    slug = models.SlugField(max_length=250, unique=True, blank=True, db_index=True)

    description = models.TextField(blank=True, verbose_name=_("Description"))
    website_url = models.URLField(blank=True, null=True, verbose_name=_("Official Website"))

    # === Cloudinary Logo ===
    logo = CloudinaryField(
        folder='ecommerce/brands/',
        blank=True,
        null=True,
        transformation=[
            {'width': 300, 'height': 300, 'crop': 'limit', 'quality': 'auto', 'format': 'webp'}
        ],
        verbose_name=_("Brand Logo")
    )

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Brand"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        ordering = ['name']
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Brand.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()