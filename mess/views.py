import datetime
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from .models import Mess, Menu, Dish, Rating, Favorite, OwnerInquiry, MessPhoto
from .forms import (
    OwnerInquiryForm, MessForm, MenuForm, DishForm, RatingForm, MessPhotoForm
)


# ─── Homepage ───────────────────────────────────────────────────────────────

def homepage(request):
    return render(request, 'mess/homepage.html')


def owner_inquiry(request):
    if request.method == 'POST':
        form = OwnerInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Our team will contact you for registration.")
            return redirect('owner_inquiry_success')
    else:
        form = OwnerInquiryForm()
    return render(request, 'mess/owner_inquiry.html', {'form': form})


def owner_inquiry_success(request):
    return render(request, 'mess/owner_inquiry_success.html')


# ─── Mess List ───────────────────────────────────────────────────────────────

def mess_list(request):
    messes = Mess.objects.prefetch_related('photos', 'ratings').all()
    mess_data = []
    user_favorites = set()

    if request.user.is_authenticated:
        user_favorites = set(
            Favorite.objects.filter(user=request.user).values_list('mess_id', flat=True)
        )

    for mess in messes:
        mess_data.append({
            'mess': mess,
            'avg_rating': mess.average_rating(),
            'rating_count': mess.rating_count(),
            'is_favorite': mess.id in user_favorites,
            'cover_photo': mess.primary_photo(),
        })

    return render(request, 'mess/mess_list.html', {'mess_data': mess_data})


# ─── Mess Detail ─────────────────────────────────────────────────────────────
@login_required
def mess_detail(request, pk):
    mess = get_object_or_404(Mess.objects.prefetch_related('photos'), pk=pk)
    today = datetime.date.today()

    general_menu = Menu.objects.filter(mess=mess, menu_type='GENERAL', date=None).first()
    lunch_menu = Menu.objects.filter(mess=mess, menu_type='LUNCH', date=today).first()
    dinner_menu = Menu.objects.filter(mess=mess, menu_type='DINNER', date=today).first()

    user_rating = None
    is_favorite = False
    rating_form = RatingForm()

    if request.user.is_authenticated:
        user_rating_obj = Rating.objects.filter(user=request.user, mess=mess).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating
            rating_form = RatingForm(initial={'rating': user_rating})
        is_favorite = Favorite.objects.filter(user=request.user, mess=mess).exists()

    photos = mess.photos.all()

    context = {
        'mess': mess,
        'avg_rating': mess.average_rating(),
        'rating_count': mess.rating_count(),
        'general_menu': general_menu,
        'lunch_menu': lunch_menu,
        'dinner_menu': dinner_menu,
        'user_rating': user_rating,
        'is_favorite': is_favorite,
        'rating_form': rating_form,
        'today': today,
        'is_owner': request.user.is_authenticated and mess.owner == request.user,
        'photos': photos,
        'has_location': mess.latitude is not None and mess.longitude is not None,
    }
    return render(request, 'mess/mess_detail.html', context)


# ─── Nearby Messes ───────────────────────────────────────────────────────────

def nearby_messes(request):
    """
    GET  ?lat=XX&lng=YY&radius=5  → page with map + list
    Without params → show the location-picker page.
    """
    lat_str = request.GET.get('lat', '').strip()
    lng_str = request.GET.get('lng', '').strip()
    try:
        radius_km = float(request.GET.get('radius', 5))
        radius_km = max(0.5, min(radius_km, 50))  # clamp 0.5–50 km
    except ValueError:
        radius_km = 5.0

    if not lat_str or not lng_str:
        return render(request, 'mess/nearby.html', {'searched': False})

    try:
        user_lat = float(lat_str)
        user_lng = float(lng_str)
    except ValueError:
        messages.error(request, "Invalid coordinates.")
        return render(request, 'mess/nearby.html', {'searched': False})

    if not (-90 <= user_lat <= 90 and -180 <= user_lng <= 180):
        messages.error(request, "Coordinates out of range.")
        return render(request, 'mess/nearby.html', {'searched': False})

    # Filter messes that have coordinates, compute distance, sort
    geo_messes = Mess.objects.exclude(latitude=None).exclude(longitude=None).prefetch_related('photos', 'ratings')

    nearby = []
    for mess in geo_messes:
        dist = mess.distance_to(user_lat, user_lng)
        if dist is not None and dist <= radius_km:
            nearby.append({
                'mess': mess,
                'distance': dist,
                'avg_rating': mess.average_rating(),
                'rating_count': mess.rating_count(),
                'cover_photo': mess.primary_photo(),
                'lat': float(mess.latitude),
                'lng': float(mess.longitude),
            })

    nearby.sort(key=lambda x: x['distance'])

    user_favorites = set()
    if request.user.is_authenticated:
        user_favorites = set(
            Favorite.objects.filter(user=request.user).values_list('mess_id', flat=True)
        )
    for item in nearby:
        item['is_favorite'] = item['mess'].id in user_favorites

    context = {
        'searched': True,
        'nearby': nearby,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'radius_km': radius_km,
        'count': len(nearby),
    }
    return render(request, 'mess/nearby.html', context)


# ─── Rating ──────────────────────────────────────────────────────────────────

@login_required
def rate_mess(request, pk):
    if request.method != 'POST':
        return redirect('mess_detail', pk=pk)

    mess = get_object_or_404(Mess, pk=pk)
    form = RatingForm(request.POST)

    if form.is_valid():
        rating_value = form.cleaned_data['rating']
        if not (1 <= rating_value <= 5):
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect('mess_detail', pk=pk)

        Rating.objects.update_or_create(
            user=request.user,
            mess=mess,
            defaults={'rating': rating_value}
        )
        messages.success(request, f"Your rating of {rating_value}/5 has been saved.")
    else:
        messages.error(request, "Invalid rating. Please enter a value between 1 and 5.")

    return redirect('mess_detail', pk=pk)


# ─── Favorites ───────────────────────────────────────────────────────────────

@login_required
def toggle_favorite(request, pk):
    if request.method != 'POST':
        return redirect('mess_detail', pk=pk)

    mess = get_object_or_404(Mess, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, mess=mess)

    if not created:
        fav.delete()
        messages.info(request, f"Removed {mess.name} from your favorites.")
    else:
        messages.success(request, f"Added {mess.name} to your favorites.")

    return redirect('mess_detail', pk=pk)


@login_required
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('mess').prefetch_related('mess__photos')
    fav_data = []
    for fav in favorites:
        fav_data.append({
            'mess': fav.mess,
            'avg_rating': fav.mess.average_rating(),
            'rating_count': fav.mess.rating_count(),
            'cover_photo': fav.mess.primary_photo(),
        })
    return render(request, 'mess/my_favorites.html', {'fav_data': fav_data})


# ─── Owner: Mess Management ──────────────────────────────────────────────────

@login_required
def owner_dashboard(request):
    messes = Mess.objects.filter(owner=request.user).prefetch_related('photos')
    return render(request, 'mess/owner_dashboard.html', {'messes': messes})


@login_required
def create_mess(request):
    if request.method == 'POST':
        form = MessForm(request.POST)
        if form.is_valid():
            mess = form.save(commit=False)
            mess.owner = request.user
            mess.save()
            messages.success(request, f"Mess '{mess.name}' created. You can now add photos.")
            return redirect('manage_photos', pk=mess.pk)
    else:
        form = MessForm()
    return render(request, 'mess/mess_form.html', {'form': form, 'action': 'Create'})


@login_required
def edit_mess(request, pk):
    mess = get_object_or_404(Mess, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MessForm(request.POST, instance=mess)
        if form.is_valid():
            form.save()
            messages.success(request, "Mess updated successfully.")
            return redirect('owner_dashboard')
    else:
        form = MessForm(instance=mess)
    return render(request, 'mess/mess_form.html', {'form': form, 'action': 'Edit', 'mess': mess})


# ─── Owner: Photo Management ─────────────────────────────────────────────────

@login_required
def manage_photos(request, pk):
    mess = get_object_or_404(Mess, pk=pk, owner=request.user)
    photos = mess.photos.all()
    photo_form = MessPhotoForm()

    if request.method == 'POST':
        photo_form = MessPhotoForm(request.POST, request.FILES)
        if photo_form.is_valid():
            photo = photo_form.save(commit=False)
            photo.mess = mess
            photo.save()
            messages.success(request, "Photo uploaded successfully.")
            return redirect('manage_photos', pk=pk)

    return render(request, 'mess/manage_photos.html', {
        'mess': mess,
        'photos': photos,
        'photo_form': photo_form,
    })


@login_required
def set_cover_photo(request, photo_pk):
    if request.method != 'POST':
        return redirect('owner_dashboard')
    photo = get_object_or_404(MessPhoto, pk=photo_pk, mess__owner=request.user)
    # Save triggers the single-cover enforcement logic in MessPhoto.save()
    photo.is_cover = True
    photo.save()
    messages.success(request, "Cover photo updated.")
    return redirect('manage_photos', pk=photo.mess.pk)


@login_required
def delete_photo(request, photo_pk):
    if request.method != 'POST':
        return redirect('owner_dashboard')
    photo = get_object_or_404(MessPhoto, pk=photo_pk, mess__owner=request.user)
    mess_pk = photo.mess.pk
    photo.image.delete(save=False)  # delete file from disk
    photo.delete()
    messages.success(request, "Photo deleted.")
    return redirect('manage_photos', pk=mess_pk)


# ─── Owner: Menu Management ──────────────────────────────────────────────────

@login_required
def create_menu(request, mess_pk):
    mess = get_object_or_404(Mess, pk=mess_pk, owner=request.user)

    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu_type = form.cleaned_data['menu_type']
            date = form.cleaned_data['date']

            exists = Menu.objects.filter(mess=mess, menu_type=menu_type, date=date).exists()
            if exists:
                messages.error(request, "A menu of this type already exists for this date.")
                return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Create'})

            menu = form.save(commit=False)
            menu.mess = mess
            menu.save()
            messages.success(request, "Menu created successfully.")
            return redirect('manage_menu', pk=menu.pk)
    else:
        form = MenuForm()

    return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Create'})


@login_required
def edit_menu(request, pk):
    menu = get_object_or_404(Menu, pk=pk, mess__owner=request.user)
    mess = menu.mess

    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            menu_type = form.cleaned_data['menu_type']
            date = form.cleaned_data['date']

            conflict = Menu.objects.filter(
                mess=mess, menu_type=menu_type, date=date
            ).exclude(pk=pk).exists()

            if conflict:
                messages.error(request, "Another menu of this type already exists for this date.")
                return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Edit'})

            form.save()
            messages.success(request, "Menu updated successfully.")
            return redirect('manage_menu', pk=pk)
    else:
        form = MenuForm(instance=menu)

    return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Edit'})


@login_required
def manage_menu(request, pk):
    menu = get_object_or_404(Menu, pk=pk, mess__owner=request.user)
    dishes = menu.dishes.all()
    dish_form = DishForm()

    if request.method == 'POST':
        dish_form = DishForm(request.POST)
        if dish_form.is_valid():
            dish = dish_form.save(commit=False)
            dish.menu = menu
            dish.save()
            messages.success(request, "Dish added.")
            return redirect('manage_menu', pk=pk)

    return render(request, 'mess/manage_menu.html', {
        'menu': menu,
        'dishes': dishes,
        'dish_form': dish_form,
    })


@login_required
def delete_dish(request, pk):
    dish = get_object_or_404(Dish, pk=pk, menu__mess__owner=request.user)
    menu_pk = dish.menu.pk
    if request.method == 'POST':
        dish.delete()
        messages.success(request, "Dish removed.")
    return redirect('manage_menu', pk=menu_pk)



# ─── Homepage ───────────────────────────────────────────────────────────────

def homepage(request):
    return render(request, 'mess/homepage.html')


def owner_inquiry(request):
    if request.method == 'POST':
        form = OwnerInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Our team will contact you for registration.")
            return redirect('owner_inquiry_success')
    else:
        form = OwnerInquiryForm()
    return render(request, 'mess/owner_inquiry.html', {'form': form})


def owner_inquiry_success(request):
    return render(request, 'mess/owner_inquiry_success.html')


# ─── Mess List ───────────────────────────────────────────────────────────────

def mess_list(request):
    messes = Mess.objects.all()
    mess_data = []
    user_favorites = set()

    if request.user.is_authenticated:
        user_favorites = set(
            Favorite.objects.filter(user=request.user).values_list('mess_id', flat=True)
        )

    for mess in messes:
        # ✅ get cover photo using related_name='photos'
        cover_photo = mess.photos.filter(is_cover=True).first()

        # ✅ fallback if no cover photo
        if not cover_photo:
            cover_photo = mess.photos.first()

        mess_data.append({
            'mess': mess,
            'cover_photo': cover_photo,   # 🔥 IMPORTANT
            'avg_rating': mess.average_rating(),
            'rating_count': mess.rating_count(),
            'is_favorite': mess.id in user_favorites,
        })

    return render(request, 'mess/mess_list.html', {'mess_data': mess_data})

# ─── Mess Detail ─────────────────────────────────────────────────────────────
@login_required
def mess_detail(request, pk):
    mess = get_object_or_404(Mess, pk=pk)
    today = datetime.date.today()

    general_menu = Menu.objects.filter(mess=mess, menu_type='GENERAL', date=None).first()
    lunch_menu = Menu.objects.filter(mess=mess, menu_type='LUNCH', date=today).first()
    dinner_menu = Menu.objects.filter(mess=mess, menu_type='DINNER', date=today).first()

    user_rating = None
    is_favorite = False
    rating_form = RatingForm()

    if request.user.is_authenticated:
        user_rating_obj = Rating.objects.filter(user=request.user, mess=mess).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating
            rating_form = RatingForm(initial={'rating': user_rating})
        is_favorite = Favorite.objects.filter(user=request.user, mess=mess).exists()

    context = {
        'mess': mess,
        'avg_rating': mess.average_rating(),
        'rating_count': mess.rating_count(),
        'general_menu': general_menu,
        'lunch_menu': lunch_menu,
        'dinner_menu': dinner_menu,
        'user_rating': user_rating,
        'is_favorite': is_favorite,
        'rating_form': rating_form,
        'today': today,
        'is_owner': request.user.is_authenticated and mess.owner == request.user,
    }
    return render(request, 'mess/mess_detail.html', context)


# ─── Rating ──────────────────────────────────────────────────────────────────

@login_required
def rate_mess(request, pk):
    if request.method != 'POST':
        return redirect('mess_detail', pk=pk)

    mess = get_object_or_404(Mess, pk=pk)
    form = RatingForm(request.POST)

    if form.is_valid():
        rating_value = form.cleaned_data['rating']
        if not (1 <= rating_value <= 5):
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect('mess_detail', pk=pk)

        Rating.objects.update_or_create(
            user=request.user,
            mess=mess,
            defaults={'rating': rating_value}
        )
        messages.success(request, f"Your rating of {rating_value}/5 has been saved.")
    else:
        messages.error(request, "Invalid rating. Please enter a value between 1 and 5.")

    return redirect('mess_detail', pk=pk)


# ─── Favorites ───────────────────────────────────────────────────────────────

@login_required
def toggle_favorite(request, pk):
    if request.method != 'POST':
        return redirect('mess_detail', pk=pk)

    mess = get_object_or_404(Mess, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, mess=mess)

    if not created:
        fav.delete()
        messages.info(request, f"Removed {mess.name} from your favorites.")
    else:
        messages.success(request, f"Added {mess.name} to your favorites.")

    return redirect('mess_detail', pk=pk)


@login_required
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('mess')
    fav_data = []
    for fav in favorites:
        fav_data.append({
            'mess': fav.mess,
            'avg_rating': fav.mess.average_rating(),
            'rating_count': fav.mess.rating_count(),
        })
    return render(request, 'mess/my_favorites.html', {'fav_data': fav_data})


# ─── Owner: Mess Management ──────────────────────────────────────────────────

@login_required
def owner_dashboard(request):
    messes = Mess.objects.filter(owner=request.user)
    return render(request, 'mess/owner_dashboard.html', {'messes': messes})


@login_required
def create_mess(request):
    if request.method == 'POST':
        form = MessForm(request.POST)
        if form.is_valid():
            mess = form.save(commit=False)
            mess.owner = request.user
            mess.save()
            messages.success(request, f"Mess '{mess.name}' created successfully.")
            return redirect('owner_dashboard')
    else:
        form = MessForm()
    return render(request, 'mess/mess_form.html', {'form': form, 'action': 'Create'})


@login_required
def edit_mess(request, pk):
    mess = get_object_or_404(Mess, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MessForm(request.POST, instance=mess)
        if form.is_valid():
            form.save()
            messages.success(request, "Mess updated successfully.")
            return redirect('owner_dashboard')
    else:
        form = MessForm(instance=mess)
    return render(request, 'mess/mess_form.html', {'form': form, 'action': 'Edit', 'mess': mess})


# ─── Owner: Menu Management ──────────────────────────────────────────────────

@login_required
def create_menu(request, mess_pk):
    mess = get_object_or_404(Mess, pk=mess_pk, owner=request.user)

    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu_type = form.cleaned_data['menu_type']
            date = form.cleaned_data['date']

            exists = Menu.objects.filter(mess=mess, menu_type=menu_type, date=date).exists()
            if exists:
                messages.error(request, "A menu of this type already exists for this date.")
                return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Create'})

            menu = form.save(commit=False)
            menu.mess = mess
            menu.save()
            messages.success(request, "Menu created successfully.")
            return redirect('manage_menu', pk=menu.pk)
    else:
        form = MenuForm()

    return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Create'})


@login_required
def edit_menu(request, pk):
    menu = get_object_or_404(Menu, pk=pk, mess__owner=request.user)
    mess = menu.mess

    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            menu_type = form.cleaned_data['menu_type']
            date = form.cleaned_data['date']

            conflict = Menu.objects.filter(
                mess=mess, menu_type=menu_type, date=date
            ).exclude(pk=pk).exists()

            if conflict:
                messages.error(request, "Another menu of this type already exists for this date.")
                return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Edit'})

            form.save()
            messages.success(request, "Menu updated successfully.")
            return redirect('manage_menu', pk=pk)
    else:
        form = MenuForm(instance=menu)

    return render(request, 'mess/menu_form.html', {'form': form, 'mess': mess, 'action': 'Edit'})


@login_required
def manage_menu(request, pk):
    menu = get_object_or_404(Menu, pk=pk, mess__owner=request.user)
    dishes = menu.dishes.all()
    dish_form = DishForm()

    if request.method == 'POST':
        dish_form = DishForm(request.POST)
        if dish_form.is_valid():
            dish = dish_form.save(commit=False)
            dish.menu = menu
            dish.save()
            messages.success(request, "Dish added.")
            return redirect('manage_menu', pk=pk)

    return render(request, 'mess/manage_menu.html', {
        'menu': menu,
        'dishes': dishes,
        'dish_form': dish_form,
    })


@login_required
def delete_dish(request, pk):
    dish = get_object_or_404(Dish, pk=pk, menu__mess__owner=request.user)
    menu_pk = dish.menu.pk
    if request.method == 'POST':
        dish.delete()
        messages.success(request, "Dish removed.")
    return redirect('manage_menu', pk=menu_pk)
