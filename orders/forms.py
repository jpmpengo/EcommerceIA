from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    billing_same_as_shipping = forms.BooleanField(
        label="Adresse de facturation identique à l’adresse de livraison",
        required=False,
        initial=True,
    )

    country = forms.ChoiceField(
        choices=Order.COUNTRY_CHOICES,
        label="Pays",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

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
            "country",
            "billing_same_as_shipping",
            "billing_first_name",
            "billing_last_name",
            "billing_address",
            "billing_postal_code",
            "billing_city",
            "billing_country",
        ]

        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
            "phone": "Téléphone",
            "address": "Adresse",
            "postal_code": "Code postal",
            "city": "Ville",
            "country": "Pays",
            "billing_first_name": "Prénom de facturation",
            "billing_last_name": "Nom de facturation",
            "billing_address": "Adresse de facturation",
            "billing_postal_code": "Code postal de facturation",
            "billing_city": "Ville de facturation",
            "billing_country": "Pays de facturation",
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


    def clean(self):
        cleaned_data = super().clean()

        if (
            self.is_bound
            and "billing_same_as_shipping" not in self.data
        ):
            cleaned_data["billing_same_as_shipping"] = True

        if not cleaned_data.get("billing_same_as_shipping"):
            required_fields = [
                "billing_first_name",
                "billing_last_name",
                "billing_address",
                "billing_postal_code",
                "billing_city",
                "billing_country",
            ]

            for field_name in required_fields:
                if not cleaned_data.get(field_name):
                    self.add_error(
                        field_name,
                        "Ce champ est obligatoire pour une adresse de facturation différente.",
                    )

        return cleaned_data

        
