import logging
from django.db import models
from django.db.models import Q, Avg
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

from mptt.models import MPTTModel, TreeForeignKey
from cloudinary.models import CloudinaryField

logger = logging.getLogger(__name__)


# =========================
# CATEGORY MODEL (MPTT)
# =========================
class Category(MPTTModel):
    """
    Hierarchical product category using MPTT.
    Example: Electronics > Mobiles > Smartphones
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True, db_index=True)

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    image = CloudinaryField(
        'image',
        folder='ecommerce/categories/',
        blank=True,
        null=True
    )

    banner = CloudinaryField(
        'banner',
        folder='ecommerce/categories/banners/',
        blank=True,
        null=True
    )

    icon = models.CharField(max_length=100, blank=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Display
    is_active = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

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
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                name='unique_category_name_per_parent'
            )
        ]

    def __str__(self):
        return self.get_full_path()

    def clean(self):
        if self.pk and self.parent:
            if self.parent.get_descendants(include_self=True).filter(pk=self.pk).exists():
                raise ValidationError(_("A category cannot be its own descendant."))

    def _generate_unique_slug(self):
        if self.slug:
            return

        base = slugify(self.name)
        slug = base
        counter = 1

        while Category.objects.filter(
            slug=slug, parent=self.parent
        ).exclude(pk=self.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1

        self.slug = slug

    def _build_path(self):
        return f"{self.parent.path}/{self.slug}" if self.parent else self.slug

    def save(self, *args, **kwargs):
        self._generate_unique_slug()
        super().save(*args, **kwargs)

        new_path = self._build_path()
        if self.path != new_path:
            self.path = new_path
            super().save(update_fields=['path'])

            for child in self.get_descendants():
                child.path = child._build_path()
                child.save(update_fields=['path'])

    def get_full_path(self):
        return " > ".join(
            cat.name for cat in self.get_ancestors(include_self=True)
        )

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'category_path': self.path})



# =========================
# BRAND MODEL
# =========================
class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)

    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True)

    logo = CloudinaryField(
        'logo',
        folder='ecommerce/brands/',
        blank=True,
        null=True
    )

    country = models.CharField(max_length=100, blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    priority = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-priority', 'name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.founded_year and self.founded_year > timezone.now().year:
            raise ValidationError(_("Founded year cannot be in the future."))

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# =========================
# PRODUCT MODEL
# =========================
class Product(models.Model):
    """
    Product concept (NO price, NO stock, NO images).
    Example: iPhone 15
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    category = TreeForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True)

    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    related_products = models.ManyToManyField('self', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        return (
            self.reviews.filter(is_approved=True)
            .aggregate(avg=Avg('rating'))['avg'] or 0
        )


# =========================
# VARIANT ATTRIBUTES
# =========================
class VariantAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class VariantAttributeValue(models.Model):
    attribute = models.ForeignKey(
        VariantAttribute,
        on_delete=models.CASCADE,
        related_name="values"
    )
    value = models.CharField(max_length=100)

    hex_code = models.CharField(max_length=7, blank=True)
    swatch_image = CloudinaryField('swatch', blank=True, null=True)

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# =========================
# PRODUCT VARIANT
# =========================
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    sku = models.CharField(max_length=100, unique=True, db_index=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    stock = models.PositiveIntegerField(default=0)

    weight_kg = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    length_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_class = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.sale_price and self.sale_price >= self.price:
            raise ValidationError(_("Sale price must be less than price."))

    def get_price(self):
        return self.sale_price or self.price

    def __str__(self):
        return f"{self.product.name} ({self.sku})"



# =========================
# VARIANT → ATTRIBUTE LINK
# =========================
class ProductVariantAttribute(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="attributes"
    )
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE)
    value = models.ForeignKey(VariantAttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('variant', 'attribute'),
            ('variant', 'value'),
        )

    def clean(self):
        if self.value.attribute_id != self.attribute_id:
            raise ValidationError(_("Value does not belong to attribute."))


# =========================
# VARIANT IMAGES
# =========================
class ProductVariantImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = CloudinaryField(
        'image',
        folder='ecommerce/products/variants/'
    )

    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']
        constraints = [
            models.UniqueConstraint(
                fields=['variant'],
                condition=Q(is_primary=True),
                name='unique_primary_image_per_variant'
            )
        ]


# =========================
# PRODUCT REVIEW
# =========================
class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    review = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')


