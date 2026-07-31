from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "postal_code",
            "city",
        ]

        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
            "phone": "Téléphone",
            "address": "Adresse",
            "postal_code": "Code postal",
            "city": "Ville",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }
        