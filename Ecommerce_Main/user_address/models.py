"""
User Address Models for E-commerce Application
Enterprise-grade address models with comprehensive validation, geocoding support,
and international phone number handling for Django e-commerce applications.
"""
import re
from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
User = get_user_model()
class Country(models.Model):
    """
    Country model for storing country information.
   
    Attributes:
        name: Full country name
        code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'IN', 'GB')
        phone_code: International dialing code (e.g., '+1', '+91')
        is_active: Whether the country is available for shipping
    """
   
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Full country name")
    )
    code = models.CharField(
        max_length=2,
        unique=True,
        db_index=True,
        help_text=_("ISO 3166-1 alpha-2 country code")
    )
    phone_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(
                regex=r'^\+\d{1,4}$',
                message=_('Phone code must start with + followed by 1-4 digits')
            )
        ],
        help_text=_("International dialing code (e.g., +1, +91)")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Is this country available for shipping?")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ['name']
    def __str__(self):
        return f"{self.name} ({self.code})"
    def clean(self):
        """Validate country data."""
        super().clean()
        if self.code:
            if not re.match(r'^[A-Z]{2}$', self.code.upper()):
                raise ValidationError({
                    'code': _('Country code must be 2 uppercase letters (ISO 3166-1 alpha-2)')
                })
    def save(self, *args, **kwargs):
        """Normalize data before saving."""
        if self.code:
            self.code = self.code.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)
class State(models.Model):
    """
    State/Province model for storing regional information.
   
    Attributes:
        country: Foreign key to Country
        name: State/province name
        code: State code (e.g., 'CA', 'TX', 'KL')
        is_active: Whether the state is available for shipping
    """
   
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='states',
        help_text=_("Country this state belongs to")
    )
    name = models.CharField(
        max_length=100,
        help_text=_("State/Province name")
    )
    code = models.CharField(
        max_length=10,
        blank=True,
        help_text=_("State/Province code")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Is this state available for shipping?")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _("State/Province")
        verbose_name_plural = _("States/Provinces")
        ordering = ['country', 'name']
        unique_together = [['country', 'name']]
        indexes = [
            models.Index(fields=['country', 'name']),
        ]
    def __str__(self):
        return f"{self.name}, {self.country.code}"
    def save(self, *args, **kwargs):
        """Normalize data before saving."""
        if self.code:
            self.code = self.code.upper().strip()
        super().save(*args, **kwargs)
class City(models.Model):
    """
    City model for standardized city data (optional).
   
    Use this for better data quality and autocomplete features.
    Can be made optional by keeping city as CharField in UserAddress.
    """
   
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='cities',
        help_text=_("State this city belongs to")
    )
    name = models.CharField(
        max_length=100,
        help_text=_("City name")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Is this city available for delivery?")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ['state', 'name']
        unique_together = [['state', 'name']]
        indexes = [
            models.Index(fields=['state', 'name']),
        ]
    def __str__(self):
        return f"{self.name}, {self.state.name}"
class UserAddress(models.Model):
    """
    Enterprise-grade User Address model with geocoding and verification support.
   
    Supports multiple addresses per user with comprehensive validation including:
    - Phone number validation against selected country
    - Country-specific postal code validation (25+ countries)
    - Address verification status tracking
    - Geocoding coordinates for delivery optimization
    - Strict address type and default flag consistency
   
    Attributes:
        user: Foreign key to User model
        address_type: Type of address (shipping/billing/both)
        full_name: Recipient's full name
        phone: Contact phone number with country code
        alternate_phone: Optional alternate contact number
        address_line1: Primary address line
        address_line2: Secondary address line (optional)
        landmark: Nearby landmark for easier delivery
        city: City name (CharField for flexibility)
        city_ref: Optional FK to City model for standardization
        state: Foreign key to State model
        country: Foreign key to Country model
        postal_code: ZIP/Postal code
        latitude: Geocoded latitude
        longitude: Geocoded longitude
        verification_status: Address verification status
        is_default_shipping: Is this the default shipping address?
        is_default_billing: Is this the default billing address?
        is_active: Is this address currently active?
    """
   
    ADDRESS_TYPE_CHOICES = [
        ('shipping', _('Shipping Address')),
        ('billing', _('Billing Address')),
        ('both', _('Shipping & Billing Address')),
    ]
   
    VERIFICATION_STATUS_CHOICES = [
        ('unverified', _('Not Verified')),
        ('pending', _('Verification Pending')),
        ('verified', _('Verified')),
        ('failed', _('Verification Failed')),
    ]
   
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        help_text=_("User who owns this address")
    )
   
    # Address Type
    address_type = models.CharField(
        max_length=10,
        choices=ADDRESS_TYPE_CHOICES,
        default='both',
        help_text=_("Type of address")
    )
   
    # Contact Information
    full_name = models.CharField(
        max_length=200,
        help_text=_("Recipient's full name")
    )
    phone = models.CharField(
        max_length=20,
        help_text=_("Contact phone number with country code (e.g., +919876543210)")
    )
    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Alternate contact number (optional)")
    )
   
    # Address Details
    address_line1 = models.CharField(
        max_length=255,
        help_text=_("House/Flat number, Building name, Street")
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Area, Colony, Sector (optional)")
    )
    landmark = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Nearby landmark for easier delivery (optional)")
    )
   
    # City - dual approach for flexibility and standardization
    city = models.CharField(
        max_length=100,
        help_text=_("City name")
    )
    city_ref = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='addresses',
        help_text=_("Reference to standardized city (optional)")
    )
   
    state = models.ForeignKey(
        State,
        on_delete=models.PROTECT,
        related_name='addresses',
        help_text=_("State/Province")
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='addresses',
        help_text=_("Country")
    )
    postal_code = models.CharField(
        max_length=20,
        help_text=_("ZIP/Postal code")
    )
   
    # Geocoding fields for delivery optimization
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('-90.0')),
            MaxValueValidator(Decimal('90.0'))
        ],
        help_text=_("Latitude coordinate")
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('-180.0')),
            MaxValueValidator(Decimal('180.0'))
        ],
        help_text=_("Longitude coordinate")
    )
   
    # Address verification
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified',
        help_text=_("Address verification status")
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date when address was last verified")
    )
   
    # Address Flags
    is_default_shipping = models.BooleanField(
        default=False,
        help_text=_("Is this the default shipping address?")
    )
    is_default_billing = models.BooleanField(
        default=False,
        help_text=_("Is this the default billing address?")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Is this address currently active?")
    )
   
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        verbose_name = _("User Address")
        verbose_name_plural = _("User Addresses")
        ordering = ['-is_default_shipping', '-is_default_billing', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'is_default_shipping']),
            models.Index(fields=['user', 'is_default_billing']),
            models.Index(fields=['user', 'address_type']),
            models.Index(fields=['country', 'state', 'city']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        constraints = [
            # Only one default shipping address per user for each address type
            models.UniqueConstraint(
                fields=['user', 'address_type'],
                condition=Q(is_default_shipping=True, is_active=True, address_type__in=['shipping', 'both']),
                name='unique_default_shipping_per_user_type'
            ),
            # Only one default billing address per user for each address type
            models.UniqueConstraint(
                fields=['user', 'address_type'],
                condition=Q(is_default_billing=True, is_active=True, address_type__in=['billing', 'both']),
                name='unique_default_billing_per_user_type'
            ),
        ]
    def __str__(self):
        return f"{self.full_name} - {self.address_line1}, {self.city}"
    def _validate_phone_number(self, phone_field_name='phone'):
        """
        Validate phone number format and country code match.
       
        Args:
            phone_field_name: Name of the phone field to validate
           
        Raises:
            ValidationError: If phone number is invalid
        """
        phone = getattr(self, phone_field_name)
        if not phone:
            return
       
        # Basic format validation
        if not re.match(r'^\+?[1-9]\d{7,14}$', phone):
            raise ValidationError({
                phone_field_name: _('Phone number must be 8-15 digits with optional + prefix. Cannot start with 0.')
            })
       
        # Validate country code prefix matches selected country
        if self.country_id and hasattr(self.country, 'phone_code'):
            country_code = self.country.phone_code
           
            # Normalize phone to include +
            normalized_phone = phone if phone.startswith('+') else f'+{phone}'
           
            # Check if phone starts with country code
            if not normalized_phone.startswith(country_code):
                raise ValidationError({
                    phone_field_name: _(
                        f'Phone number should start with {country_code} for {self.country.name}. '
                        f'Current number appears to be from a different country.'
                    )
                })
    def _validate_postal_code(self):
        """
        Country-specific postal code validation for 25+ major markets.
       
        Raises:
            ValidationError: If postal code format is invalid for the country
        """
        # Comprehensive postal code patterns: (regex, error_message)
        postal_patterns = {
            # North America
            'US': (r'^\d{5}(-\d{4})?$', 'US ZIP code must be 5 digits or 5+4 format (e.g., 12345 or 12345-6789)'),
            'CA': (r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$', 'Canadian postal code format invalid (e.g., K1A 0B1)'),
            'MX': (r'^\d{5}$', 'Mexican postal code must be 5 digits'),
           
            # South America
            'BR': (r'^\d{5}-?\d{3}$', 'Brazilian CEP must be 8 digits (e.g., 12345-678)'),
            'AR': (r'^[A-Z]?\d{4}[A-Z]{0,3}$', 'Argentine postal code format invalid (e.g., C1425 or 1425)'),
            'CL': (r'^\d{7}$', 'Chilean postal code must be 7 digits'),
           
            # Europe
            'GB': (r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$', 'UK postcode format invalid (e.g., SW1A 1AA)'),
            'DE': (r'^\d{5}$', 'German postcode must be 5 digits'),
            'FR': (r'^\d{5}$', 'French postcode must be 5 digits'),
            'IT': (r'^\d{5}$', 'Italian CAP must be 5 digits'),
            'ES': (r'^\d{5}$', 'Spanish postal code must be 5 digits'),
            'NL': (r'^\d{4}\s?[A-Z]{2}$', 'Dutch postcode format invalid (e.g., 1234 AB)'),
            'BE': (r'^\d{4}$', 'Belgian postcode must be 4 digits'),
            'CH': (r'^\d{4}$', 'Swiss postcode must be 4 digits'),
            'AT': (r'^\d{4}$', 'Austrian postcode must be 4 digits'),
            'SE': (r'^\d{3}\s?\d{2}$', 'Swedish postcode format invalid (e.g., 123 45)'),
            'NO': (r'^\d{4}$', 'Norwegian postcode must be 4 digits'),
            'DK': (r'^\d{4}$', 'Danish postcode must be 4 digits'),
            'PL': (r'^\d{2}-\d{3}$', 'Polish postcode format invalid (e.g., 00-950)'),
           
            # Asia
            'IN': (r'^\d{6}$', 'Indian PIN code must be exactly 6 digits'),
            'CN': (r'^\d{6}$', 'Chinese postcode must be 6 digits'),
            'JP': (r'^\d{3}-?\d{4}$', 'Japanese postal code must be 7 digits (e.g., 100-0001)'),
            'KR': (r'^\d{5}$', 'South Korean postcode must be 5 digits'),
            'SG': (r'^\d{6}$', 'Singapore postcode must be 6 digits'),
            'MY': (r'^\d{5}$', 'Malaysian postcode must be 5 digits'),
            'TH': (r'^\d{5}$', 'Thai postcode must be 5 digits'),
           
            # Oceania
            'AU': (r'^\d{4}$', 'Australian postcode must be 4 digits'),
            'NZ': (r'^\d{4}$', 'New Zealand postcode must be 4 digits'),
        }
       
        if self.country_id:
            country_code = self.country.code if hasattr(self.country, 'code') else None
           
            if country_code and country_code in postal_patterns:
                pattern, error_message = postal_patterns[country_code]
                normalized_postal = self.postal_code.strip().upper().replace(' ', '')
               
                if not re.match(pattern, normalized_postal):
                    raise ValidationError({
                        'postal_code': _(error_message)
                    })
    def clean(self):
        """
        Comprehensive validation for address data.
       
        Raises:
            ValidationError: If validation fails
        """
        super().clean()
       
        errors = {}
       
        # Validate state belongs to selected country
        if self.state_id and self.country_id:
            state_country_id = self.state.country_id if hasattr(self.state, 'country_id') else None
            if state_country_id and state_country_id != self.country_id:
                errors['state'] = _('Selected state does not belong to the selected country.')
       
        # Validate country is active
        if self.country_id:
            try:
                if hasattr(self.country, 'is_active') and not self.country.is_active:
                    errors['country'] = _('Shipping to this country is currently unavailable.')
            except Country.DoesNotExist:
                errors['country'] = _('Invalid country selected.')
       
        # Validate state is active
        if self.state_id:
            try:
                if hasattr(self.state, 'is_active') and not self.state.is_active:
                    errors['state'] = _('Shipping to this state is currently unavailable.')
            except State.DoesNotExist:
                errors['state'] = _('Invalid state selected.')
       
        # CRITICAL: Validate address_type consistency with default flags
        if self.address_type == 'shipping':
            # Shipping-only addresses can ONLY be default shipping
            if self.is_default_billing:
                errors['is_default_billing'] = _(
                    'A shipping-only address cannot be the default billing address. '
                    'Change address type to "both" or uncheck default billing.'
                )
       
        elif self.address_type == 'billing':
            # Billing-only addresses can ONLY be default billing
            if self.is_default_shipping:
                errors['is_default_shipping'] = _(
                    'A billing-only address cannot be the default shipping address. '
                    'Change address type to "both" or uncheck default shipping.'
                )
       
        elif self.address_type == 'both':
            # 'Both' type can be either or both defaults - this is valid
            pass
       
        # Validate phone numbers
        try:
            self._validate_phone_number('phone')
        except ValidationError as e:
            errors.update(e.message_dict)
       
        if self.alternate_phone:
            try:
                self._validate_phone_number('alternate_phone')
            except ValidationError as e:
                errors.update(e.message_dict)
       
        # Validate postal code format
        if self.postal_code:
            try:
                self._validate_postal_code()
            except ValidationError as e:
                errors.update(e.message_dict)
       
        # Validate city_ref matches state if provided
        if self.city_ref_id and self.state_id:
            city_state_id = self.city_ref.state_id if hasattr(self.city_ref, 'state_id') else None
            if city_state_id and city_state_id != self.state_id:
                errors['city_ref'] = _('Selected city does not belong to the selected state.')
       
        # Validate coordinates if provided
        if (self.latitude is not None) != (self.longitude is not None):
            errors['latitude'] = _('Both latitude and longitude must be provided together.')
       
        if errors:
            raise ValidationError(errors)
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Override save to handle default address logic and normalization.
       
        Ensures only one default shipping/billing address per user and address type.
        Uses transaction to prevent race conditions.
        """
        # Normalize data before validation
        if self.postal_code:
            self.postal_code = self.postal_code.strip().upper()
       
        if self.full_name:
            self.full_name = self.full_name.strip()
       
        if self.city:
            self.city = self.city.strip()
       
        if self.phone:
            self.phone = self.phone.strip()
            # Ensure phone starts with +
            if not self.phone.startswith('+'):
                self.phone = f'+{self.phone}'
       
        if self.alternate_phone:
            self.alternate_phone = self.alternate_phone.strip()
            if not self.alternate_phone.startswith('+'):
                self.alternate_phone = f'+{self.alternate_phone}'
       
        # Run validations
        self.full_clean()
       
        # Handle default shipping address based on address_type
        if self.is_default_shipping and self.is_active:
            if self.address_type in ['shipping', 'both']:
                UserAddress.objects.filter(
                    user=self.user,
                    is_default_shipping=True,
                    is_active=True,
                    address_type__in=['shipping', 'both']
                ).exclude(pk=self.pk).update(is_default_shipping=False)
       
        # Handle default billing address based on address_type
        if self.is_default_billing and self.is_active:
            if self.address_type in ['billing', 'both']:
                UserAddress.objects.filter(
                    user=self.user,
                    is_default_billing=True,
                    is_active=True,
                    address_type__in=['billing', 'both']
                ).exclude(pk=self.pk).update(is_default_billing=False)
       
        # If this is the first address, make it default based on type
        if not self.pk: # New address
            user_addresses = UserAddress.objects.filter(
                user=self.user,
                is_active=True
            )
           
            if not user_addresses.exists():
                if self.address_type in ['shipping', 'both']:
                    self.is_default_shipping = True
                if self.address_type in ['billing', 'both']:
                    self.is_default_billing = True
       
        super().save(*args, **kwargs)
    def soft_delete(self):
        """
        Soft delete the address by marking it as inactive.
        Automatically assigns new defaults if this was a default address.
        """
        was_default_shipping = self.is_default_shipping
        was_default_billing = self.is_default_billing
       
        self.is_active = False
        self.is_default_shipping = False
        self.is_default_billing = False
        self.save(update_fields=['is_active', 'is_default_shipping', 'is_default_billing', 'updated_at'])
       
        # Assign new defaults if needed
        if was_default_shipping:
            new_default = UserAddress.objects.filter(
                user=self.user,
                is_active=True,
                address_type__in=['shipping', 'both']
            ).first()
            if new_default:
                new_default.is_default_shipping = True
                new_default.save(update_fields=['is_default_shipping', 'updated_at'])
       
        if was_default_billing:
            new_default = UserAddress.objects.filter(
                user=self.user,
                is_active=True,
                address_type__in=['billing', 'both']
            ).first()
            if new_default:
                new_default.is_default_billing = True
                new_default.save(update_fields=['is_default_billing', 'updated_at'])
    def get_full_address(self):
        """
        Return the complete formatted address.
       
        Returns:
            str: Formatted complete address
        """
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.landmark,
            self.city,
            self.state.name if self.state_id else None,
            self.country.name if self.country_id else None,
            self.postal_code
        ]
        return ', '.join(filter(None, address_parts))
    def has_coordinates(self):
        """Check if address has geocoded coordinates."""
        return self.latitude is not None and self.longitude is not None
    @classmethod
    def get_user_default_shipping(cls, user):
        """
        Get user's default shipping address with optimized query.
       
        Args:
            user: User instance
           
        Returns:
            UserAddress or None
        """
        try:
            return cls.objects.select_related(
                'country', 'state', 'state__country', 'city_ref'
            ).get(
                user=user,
                is_default_shipping=True,
                is_active=True,
                address_type__in=['shipping', 'both']
            )
        except cls.DoesNotExist:
            return None
    @classmethod
    def get_user_default_billing(cls, user):
        """
        Get user's default billing address with optimized query.
       
        Args:
            user: User instance
           
        Returns:
            UserAddress or None
        """
        try:
            return cls.objects.select_related(
                'country', 'state', 'state__country', 'city_ref'
            ).get(
                user=user,
                is_default_billing=True,
                is_active=True,
                address_type__in=['billing', 'both']
            )
        except cls.DoesNotExist:
            return None
   
    @classmethod
    def get_user_addresses(cls, user, active_only=True, address_type=None):
        """
        Get all addresses for a user with optimized query.
       
        Args:
            user: User instance
            active_only: Return only active addresses (default: True)
            address_type: Filter by address type ('shipping', 'billing', 'both')
           
        Returns:
            QuerySet of UserAddress
        """
        queryset = cls.objects.select_related(
            'country', 'state', 'state__country', 'city_ref'
        ).filter(user=user)
       
        if active_only:
            queryset = queryset.filter(is_active=True)
       
        if address_type:
            queryset = queryset.filter(address_type=address_type)
       
        return queryset
   
    @classmethod
    def get_nearby_addresses(cls, latitude, longitude, radius_km=10, user=None):
        """
        Get addresses within a certain radius (requires geocoding).
       
        Note: This is a simple implementation. For production, use PostGIS or
        a geospatial database for better performance.
       
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Radius in kilometers
            user: Optional user filter
           
        Returns:
            QuerySet of UserAddress
        """
        from math import radians, cos, sin, asin, sqrt
       
        queryset = cls.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True
        )
       
        if user:
            queryset = queryset.filter(user=user)
       
        # Filter by bounding box first for performance
        lat_range = radius_km / 111.0 # Rough km to degrees
        lon_range = radius_km / (111.0 * cos(radians(latitude)))
       
        queryset = queryset.filter(
            latitude__range=(latitude - lat_range, latitude + lat_range),
            longitude__range=(longitude - lon_range, longitude + lon_range)
        )
       
        return queryset