from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Mess, Menu, Dish, Rating, OwnerInquiry, MessPhoto
import datetime


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class OwnerInquiryForm(forms.ModelForm):
    class Meta:
        model = OwnerInquiry
        fields = ('name', 'phone', 'mess_name', 'location')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit phone number'}),
            'mess_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of your mess'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full address / area'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 10:
            raise ValidationError("Enter a valid phone number with at least 10 digits.")
        return phone


class MessForm(forms.ModelForm):
    class Meta:
        model = Mess
        fields = ('name', 'location', 'latitude', 'longitude')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area / full address'}),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any',
                'placeholder': 'e.g. 20.011200', 'id': 'id_latitude',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any',
                'placeholder': 'e.g. 73.790300', 'id': 'id_longitude',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        if (lat is None) != (lng is None):
            raise ValidationError("Provide both latitude and longitude, or leave both empty.")
        if lat is not None and not (-90 <= float(lat) <= 90):
            self.add_error('latitude', "Latitude must be between -90 and 90.")
        if lng is not None and not (-180 <= float(lng) <= 180):
            self.add_error('longitude', "Longitude must be between -180 and 180.")
        return cleaned_data


class MessPhotoForm(forms.ModelForm):
    class Meta:
        model = MessPhoto
        fields = ('image', 'caption', 'is_cover')
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short caption (optional)'}),
            'is_cover': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ('menu_type', 'date')
        widgets = {
            'menu_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        menu_type = cleaned_data.get('menu_type')
        date = cleaned_data.get('date')

        if menu_type == 'GENERAL' and date is not None:
            self.add_error('date', "General menus must not have a date.")
        if menu_type in ('LUNCH', 'DINNER') and date is None:
            self.add_error('date', "Lunch and Dinner menus require a date.")

        return cleaned_data


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dish name'}),
        }


class RatingForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'})
    )
