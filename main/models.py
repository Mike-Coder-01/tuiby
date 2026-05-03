from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from accounts.models import CustomUser

def validate_handle_input(value):
    if not value.startswith('@'):
        raise ValidationError('The handle should start with "@"')

class BusinessProfile(models.Model):
    PRODUCT_CATEGORIES = [
        ('Electronics', 'Electronics'),
        ('Fashion', 'Fashion'),
        ('Handmade', 'Handmade'),
        ('Home Goods', 'Home Goods'),
        ('Other', 'other')
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=150)
    business_descriptions = models.TextField(max_length=350)
    product_category = models.CharField(max_length=100, choices=PRODUCT_CATEGORIES)

    def __str__(self):
        return self.business_name

class ProductInfo(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=15)
    product_descriptions = models.CharField(max_length=100)
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.SET_NULL, null=True, related_name='business_profile')

    def __str__(self):
        return self.product_name
    
class SocialInfo(models.Model):
    SOCIAL_CATEGORIES = [
        ('Facebook', 'facebook'),
        ('Instagram', 'instagram'),
        ('Tiktok', 'tiktok'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    social_category = models.CharField(max_length=50, choices=SOCIAL_CATEGORIES, default='Instagram')
    handle = models.CharField(max_length=100)
    product_infos = models.ManyToManyField(ProductInfo, related_name='social_handles', blank=True)

    def __str__(self):
        return self.handle

    
class SellerLocation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sellerlocation')
    latitude = models.FloatField(db_index=True)
    longitude = models.FloatField(db_index=True)
    location = models.CharField(max_length=100, default='Dar es salaam')

    def __str__(self):
        return f"Latitude is {self.latitude} and Longitude is {self.longitude}"
    
class Statistic(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='statistics', null=True)
    appearence_count = models.PositiveIntegerField(default=0)
    link_copied_count = models.PositiveIntegerField(default=0)
    new_customers_count = models.PositiveIntegerField(default=0)
    date_time = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date_time']
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date_time"],
                name="unique_user_stat_per_day",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.date_time}"
