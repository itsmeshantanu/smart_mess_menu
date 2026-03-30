from django.contrib import admin
from .models import Mess, Menu, Dish, Rating, Favorite, OwnerInquiry, MessPhoto


class DishInline(admin.TabularInline):
    model = Dish
    extra = 1


class MenuInline(admin.TabularInline):
    model = Menu
    extra = 0


class MessPhotoInline(admin.TabularInline):
    model = MessPhoto
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Mess)
class MessAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'owner', 'latitude', 'longitude', 'average_rating', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location', 'owner__username')
    inlines = [MessPhotoInline, MenuInline]


@admin.register(MessPhoto)
class MessPhotoAdmin(admin.ModelAdmin):
    list_display = ('mess', 'caption', 'is_cover', 'uploaded_at')
    list_filter = ('is_cover',)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('mess', 'menu_type', 'date', 'created_at')
    list_filter = ('menu_type', 'date')
    search_fields = ('mess__name',)
    inlines = [DishInline]


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu')
    search_fields = ('name',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'mess', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'mess', 'created_at')


@admin.register(OwnerInquiry)
class OwnerInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'mess_name', 'location', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('name', 'mess_name', 'phone')
