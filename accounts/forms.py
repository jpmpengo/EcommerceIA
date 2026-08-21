from django import forms
from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.forms import (
    UserCreationForm,
)


User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": (
                    "given-name"
                ),
            }
        ),
    )

    last_name = forms.CharField(
        required=True,
        label="Nom",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": (
                    "family-name"
                ),
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

        labels = {
            "username": (
                "Nom d’utilisateur"
            ),
        }

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": (
                        "username"
                    ),
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        for field_name in (
            "password1",
            "password2",
        ):
            self.fields[
                field_name
            ].widget.attrs.update(
                {
                    "class": "form-control",
                    "autocomplete": (
                        "new-password"
                    ),
                }
            )



    def clean_email(self):
        email = (
            self.cleaned_data[
                "email"
            ]
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email,
        ).exists():
            raise forms.ValidationError(
                (
                    "Un compte utilise déjà "
                    "cette adresse e-mail."
                )
            )

        return email
