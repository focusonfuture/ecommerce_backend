import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django.utils import timezone

from mptt.models import MPTTModel, TreeForeignKey
from cloudinary.models import CloudinaryField

logger = logging.getLogger(__name__)


# ======================================================
# CATEGORY MODEL
# ======================================================
class Category(MPTTModel):
    """
    Hierarchical product category using MPTT.
    """

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    slug = models.SlugField(
        max_length=250,
        blank=True,
        db_index=True,
        help_text=_("Auto-generated from name")
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

    icon = models.CharField(max_length=100, blank=True, verbose_name=_("Icon Class"))

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Display & status
    is_active = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    # URL path
    path = models.CharField(
        max_length=1000,
        unique=True,
        editable=False,
        blank=True,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            ),
            models.UniqueConstraint(
                fields=['path'],
                name='unique_category_path'
            ),
        ]

    def __str__(self):
        return self.get_full_path()

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):
        if self.pk and self.parent:
            if self.parent.get_descendants(include_self=True).filter(pk=self.pk).exists():
                raise ValidationError(_("A category cannot be its own descendant."))

    # -------------------------
    # SLUG HANDLING
    # -------------------------
    def _generate_unique_slug(self):
        if self.slug:
            return

        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Category.objects.filter(
            slug=slug, parent=self.parent
        ).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug

    # -------------------------
    # PATH HANDLING
    # -------------------------
    def _build_path(self):
        if self.parent:
            return f"{self.parent.path}/{self.slug}".lstrip('/')
        return self.slug

    # -------------------------
    # SAVE (SAFE FOR MPTT)
    # -------------------------
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_parent = None

        if self.pk:
            old_parent = Category.objects.get(pk=self.pk).parent

        self._generate_unique_slug()
        super().save(*args, **kwargs)

        new_path = self._build_path()

        if is_new or self.path != new_path or old_parent != self.parent:
            self.path = new_path
            super().save(update_fields=['path'])

            # Rebuild descendants if parent changed
            if old_parent != self.parent:
                for child in self.get_descendants():
                    child.path = child._build_path()
                    child.save(update_fields=['path'])

        logger.info("Category saved: /%s", self.path)

    # -------------------------
    # HELPERS
    # -------------------------
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'category_path': self.path})

    def get_full_path(self):
        return " > ".join(
            cat.name for cat in self.get_ancestors(include_self=True)
        )

    @property
    def product_count(self):
        # from products.models import Product
        # return Product.objects.filter(
        #     category__in=self.get_descendants(include_self=True),
        #     is_active=True
        # ).distinct().count()
        return 0

    # -------------------------
    # ADMIN PREVIEWS
    # -------------------------
    def image_preview(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="80" height="80" '
                'style="object-fit:contain;border-radius:4px;">'
            )
        return _("No image")

    image_preview.short_description = _("Preview")

    def banner_preview(self):
        if self.banner:
            return mark_safe(
                f'<img src="{self.banner.url}" width="200" height="80" '
                'style="object-fit:cover;border-radius:4px;">'
            )
        return _("No banner")

    banner_preview.short_description = _("Banner Preview")


# ======================================================
# BRAND MODEL
# ======================================================
class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, db_index=True)

    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True, null=True)

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

    country = models.CharField(max_length=100, blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Status & display
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    priority = models.PositiveSmallIntegerField(default=0)

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

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):
        if self.founded_year and self.founded_year > timezone.now().year:
            raise ValidationError(_("Founded year cannot be in the future."))

    # -------------------------
    # SAVE
    # -------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)
        logger.info("Brand saved: %s", self.name)

    # -------------------------
    # HELPERS
    # -------------------------
    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        # from products.models import Product
        # return Product.objects.filter(brand=self, is_active=True).count()
        return 0

    def logo_preview(self):
        if self.logo:
            return mark_safe(
                f'<img src="{self.logo.url}" width="100" height="60" '
                'style="object-fit:contain;">'
            )
        return _("No logo")

    logo_preview.short_description = _("Logo")
