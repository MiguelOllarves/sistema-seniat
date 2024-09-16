import decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Fiscales, Informacion, Pasos, User, Paim, DiariosReport, Perfil


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "password"]


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name', 'last_name', 'email')


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class FormPerfil(forms.ModelForm):
    
    class Meta:
        model = Perfil
        fields = ["image"]

class FormFiscales(forms.ModelForm):

    class Meta:
        model = Fiscales
        fields = [
            "datos_fical",
            "cargo_fiscal",
            "profesion",
            "ubicacion",
            "telefono",
            "email",
        ]

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class FormInformacion(forms.ModelForm):

    class Meta:
        model = Informacion
        fields = [
            "tarea",
            "fecha_salida",
            "fiscales",
        ]

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class PasosForm1(forms.ModelForm):

    class Meta:
        model = Pasos  
        fields = ["tarea", "nombre", "archivo"]

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class FormPaim(forms.ModelForm):

    class Meta:
        model = Paim
        fields = [
            "name",
            "latitude",
            "longitude",
            "image",
            "jefe",
            "ubicacion",

        ]
        widgets = {
            "latitude": forms.NumberInput(
                attrs={"step": "any", "class": "form-control"}
            ),
            "longitude": forms.NumberInput(
                attrs={"step": "any", "class": "form-control"}
            ),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Apply Bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class FormReport(forms.ModelForm):

    class Meta:
        model = DiariosReport
        fields = [
            "datos",
            "f",
            "vt",
            "vr",
            "mta",
            "mdua",
            "mn",
            "rp",
            "nd",
            "plc_ex",
            "paim",
            "ob1",
            "ob2",
            "ob3",
            "ob4",
            "ob5",
            "ob6",
            "ob7",
            "ob8",
        ]
        widgets = {
            "f": forms.DateInput(format='%Y-%m-%d', attrs={"class": "form-control", "type":"date"}),
        }
