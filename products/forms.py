# forms.py
import logging
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from cloudinary.forms import CloudinaryFileField
from mptt.forms import TreeNodeChoiceField

from .models import Category, Brand

logger = logging.getLogger(__name__)


class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating hierarchical categories with MPTT support.
    Prevents cycles in tree structure and validates image/banner uploads.
    """
    # Override fields to use Cloudinary + better widgets
    image = CloudinaryFileField(
        label=("Category Image"),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 '
                     'file:mr-4 file:py-2 file:px-4 file:rounded-lg '
                     'file:border-0 file:text-sm file:font-medium '
                     'file:bg-blue-50 file:text-blue-700 '
                     'hover:file:bg-blue-100',
            'accept': 'image/*'
        }),
        help_text=("Recommended: 600x600px or larger, JPG/PNG/WEBP")
    )

    banner = CloudinaryFileField(
        label=("Banner Image"),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 '
                     'file:mr-4 file:py-2 file:px-4 file:rounded-lg '
                     'file:border-0 file:text-sm file:font-medium '
                     'file:bg-indigo-50 file:text-indigo-700 '
                     'hover:file:bg-indigo-100',
            'accept': 'image/*'
        }),
        help_text=("Wide banner for category page header (e.g., 1920x600)")
    )

    parent = TreeNodeChoiceField(
        queryset=Category.objects.all(),
        level_indicator='→ ',
        required=False,
        label=("Parent Category"),
        empty_label=("— No Parent (Top Level) —"),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                     'focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
        })
    )

    meta_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                     'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Brief description for search engines...'
        }),
        required=False,
        validators=[MaxLengthValidator(320)]
    )

    class Meta:
        model = Category
        fields = [
            'name', 'parent', 'image', 'banner', 'icon',
            'meta_title', 'meta_description',
            'is_active', 'show_in_menu', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'e.g., Smartphones, Summer Dresses...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'fas fa-mobile-alt'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Best Smartphones 2025 - Great Deals'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': 0
            }),
        }
        help_texts = {
            'icon': ("FontAwesome 6 class, e.g., 'fas fa-laptop', 'fas fa-tshirt'"),
            'show_in_menu': ("Uncheck to hide from main navigation"),
            'sort_order': ("Higher number = appears later"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prevent a category from being its own parent or descendant
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(
                pk__in=self.instance.get_descendant_pks(self.instance)
            ).exclude(pk=self.instance.pk)

        # Improve parent field display with indentation
        self.fields['parent'].label_from_instance = lambda obj: f"{obj.get_full_path()}"

    def get_descendant_pks(self, instance):
        """Helper to get all descendant PKs of descendants (including self)"""
        return list(instance.get_descendants(include_self=True).values_list('pk', flat=True))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError(("Category name is required."))

        name = name.strip()
        if len(name) < 2:
            raise ValidationError(("Name must be at least 2 characters long."))

        parent = self.cleaned_data.get('parent')
        queryset = Category.objects.filter(parent=parent, name__iexact=name)

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError(("A category with this name already exists under the selected parent."))

        return name

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        banner = cleaned_data.get('banner')

        # Optional: limit file size via Cloudinary, but add friendly warning
        if image and hasattr(image, 'file') and image.file.size > 5 * 1024 * 1024:
            self.add_error('image', ("Image should be smaller than 5MB."))

        if banner and hasattr(banner.file.size if hasattr(banner, 'file') else 0) > 10 * 1024 * 1024:
            self.add_error('banner', ("Banner should be smaller than 10MB."))

        return cleaned_data


class BrandForm(forms.ModelForm):
    """
    Form for Brand creation and update with logo upload via Cloudinary.
    """
    logo = CloudinaryFileField(
        label=("Brand Logo"),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 '
                     'file:mr-4 file:py-2 file:px-4 file:rounded-lg '
                     'file:border-0 file:text-sm file:font-medium '
                     'file:bg-violet-50 file:text-violet-700 '
                     'hover:file:bg-violet-100',
            'accept': 'image/*'
        }),
        help_text=("Square logo, preferably 400x400px or higher, transparent PNG recommended")
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                     'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Tell us about this brand...'
        }),
        required=False,
        validators=[MaxLengthValidator(2000)]
    )

    website_url = forms.URLField(
        label=("Official Website"),
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                     'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'https://www.apple.com'
        })
    )

    class Meta:
        model = Brand
        fields = [
            'name', 'description', 'logo', 'website_url',
            'country', 'founded_year', 'is_featured', 'priority',
            'is_active', 'meta_title', 'meta_description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Apple, Nike, Samsung...'
            }),
            'country': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'United States'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': 1800, 'max': 2100, 'placeholder': '1903'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'meta_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'priority': forms.NumberInput(attrs={'min': 0, 'max': 1000}),
        }
        help_texts = {
            'is_featured': ("Show this brand in featured sections and homepage"),
            'priority': ("Higher priority = appears first in featured lists"),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise ValidationError(("Brand name must be at least 2 characters."))

        if Brand.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError(("A brand with this name already exists."))

        return name

    def clean_website_url(self):
        url = self.cleaned_data.get('website_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError(("Website URL must start with http:// or https://"))
        return url

    def clean(self):
        cleaned_data = super().clean()
        logo = cleaned_data.get('logo')

        if logo and hasattr(logo, 'file') and logo.file.size > 5 * 1024 * 1024:
            self.add_error('logo', ("Logo image should be smaller than 5MB."))

        return cleaned_data