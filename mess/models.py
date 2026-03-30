from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import math


def mess_photo_upload_path(instance, filename):
    return f'mess_photos/{instance.mess.id}/{filename}'


class Mess(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messes')
    # Geo coordinates — nullable so existing messes don't break
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="e.g. 20.011200"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="e.g. 73.790300"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Messes'
        ordering = ['name']

    def __str__(self):
        return self.name

    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings.exists():
            return None
        total = sum(r.rating for r in ratings)
        return round(total / ratings.count(), 1)

    def rating_count(self):
        return self.ratings.count()

    def primary_photo(self):
        """Return the first (cover) photo or None."""
        return self.photos.filter(is_cover=True).first() or self.photos.first()

    def distance_to(self, lat, lng):
        """Haversine distance in km from (lat, lng) to this mess."""
        if self.latitude is None or self.longitude is None:
            return None
        R = 6371  # Earth radius km
        lat1, lon1 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
        lat2, lon2 = math.radians(lat), math.radians(lng)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return round(R * 2 * math.asin(math.sqrt(a)), 2)


class MessPhoto(models.Model):
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to=mess_photo_upload_path)
    caption = models.CharField(max_length=200, blank=True)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'uploaded_at']

    def __str__(self):
        return f"Photo for {self.mess.name}"

    def save(self, *args, **kwargs):
        # Enforce only one cover per mess
        if self.is_cover:
            MessPhoto.objects.filter(mess=self.mess, is_cover=True).exclude(pk=self.pk).update(is_cover=False)
        super().save(*args, **kwargs)


class Menu(models.Model):
    MENU_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
    ]

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='menus')
    menu_type = models.CharField(max_length=10, choices=MENU_TYPE_CHOICES)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mess', 'date', 'menu_type')
        ordering = ['menu_type', 'date']

    def __str__(self):
        date_str = str(self.date) if self.date else 'General'
        return f"{self.mess.name} - {self.menu_type} ({date_str})"

    def clean(self):
        if self.menu_type == 'GENERAL' and self.date is not None:
            raise ValidationError("General menus must not have a date.")
        if self.menu_type in ('LUNCH', 'DINNER') and self.date is None:
            raise ValidationError("Lunch and Dinner menus must have a date.")


class Dish(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'mess')

    def __str__(self):
        return f"{self.user.username} rated {self.mess.name}: {self.rating}/5"

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mess')

    def __str__(self):
        return f"{self.user.username} → {self.mess.name}"


class OwnerInquiry(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    mess_name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Owner Inquiries'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} - {self.mess_name}"
