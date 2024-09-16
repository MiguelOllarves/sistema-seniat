import datetime
import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Create your models here.

class Fiscales(models.Model):
    datos_fical = models.CharField(max_length=100, verbose_name="Nombres y Apellidos")
    cargo_fiscal = models.TextField(null=True)
    profesion = models.CharField(max_length=300, verbose_name="Especialidad")
    ubicacion = models.TextField(null=True)
    telefono = models.CharField(max_length=300, verbose_name="Telefono")
    email = models.CharField(max_length=300, verbose_name="Email")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.datos_fical}-{self.cargo_fiscal}-{self.profesion}-{self.ubicacion}-{self.telefono}-{self.email}"


class Informacion(models.Model):
    TAREA_ESTADO_CHOICES = [
        ("Proceso", "Proceso"),
        ("Falta_un_dia", "Falta un dia"),
        ("Completado", "Completado"),
    ]

    tarea = models.TextField(null=True)
    fecha_entrada = models.DateField(auto_now_add=True)
    fecha_salida = models.DateField(blank=True, null=True)
    dias = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    fiscales = models.ForeignKey(Fiscales, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=TAREA_ESTADO_CHOICES, default="Proceso")

    def save(self, *args, **kwargs):
        if self.fecha_salida:
            self.estado = self.status()
        super().save(*args, **kwargs)

    @property
    def dias_restantes(self):
        if self.fecha_salida:
            hoy = datetime.date.today()
            return max((self.fecha_salida - hoy).days, 0)
        else:
            return None

    def status(self):
        hoy = datetime.date.today()
        if self.fecha_salida:
            dias_restantes = (self.fecha_salida - hoy).days
            if dias_restantes < 0:
                return "Completado"
            elif dias_restantes == 0:
                return "Completado"
            elif dias_restantes == 1:
                return "Falta un dia"
            else:
                return "Proceso"
        else:
            return "Sin fecha"

    def __str__(self):
        return f"{self.tarea}-{self.fecha_entrada}-{self.fecha_salida}"


class Pasos(models.Model):

    nombre = models.CharField(max_length=255)
    archivo = models.FileField(upload_to="pasos/", null=True, blank=False)
    completado = models.BooleanField(default=False)
    tarea = models.ForeignKey(Informacion, on_delete=models.CASCADE, null=True, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    @staticmethod
    def son_completados(pasos):
        # Si pasos es una lista, filtramos por la tarea de los primeros elementos y contamos cuántos están completados.
        # Si solo hay un elemento en la lista, usamos ese elemento directamente.
        if isinstance(pasos, list) and len(pasos) > 0:
            tarea_id = pasos[0].tarea.id
            completed_count = Pasos.objects.filter(completado=True, tarea__id=tarea_id).count()
            return completed_count >= 12
        elif hasattr(pasos, 'tarea'):
            # Si pasos es un solo objeto, simplemente filtramos por la tarea de ese objeto.
            completed_count = Pasos.objects.filter(completado=True, tarea=pasos.tarea).count()
            return completed_count >= 12
        else:
            raise ValueError("Argumento inválido para son_completados")


    def __str__(self):
        return self.nombre


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)  # Campo para marcar si la notificación fue leída

    def __str__(self):
        return self.title


class Paim(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Paim")
    jefe = models.CharField(max_length=255, verbose_name="Nombre de Encargado")
    ubicacion = models.TextField(null=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=6,  null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=6,  null=True, blank=True)
    image = models.ImageField(upload_to="imagenes/", default="imagen.jpg", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return f"{self.name}-{self.jefe}"

class DiariosReport(models.Model):
    datos = models.CharField(max_length=255, verbose_name="Nombre y Apellido")
    f = models.DateField(max_length=255, verbose_name="Fecha")
    vt = models.IntegerField()
    ob1 = models.TextField(null=True, blank=True)
    plc_ex = models.IntegerField()
    ob2 = models.TextField(null=True, blank=True)
    vr = models.IntegerField()
    ob3 = models.TextField(null=True, blank=True)
    mta = models.IntegerField()
    ob4 = models.TextField(null=True, blank=True)
    mdua = models.IntegerField()
    ob5 = models.TextField(null=True, blank=True)
    mn = models.IntegerField()
    ob6 = models.TextField(null=True, blank=True)
    rp = models.IntegerField()
    ob7 = models.TextField(null=True, blank=True)
    nd = models.IntegerField()
    ob8 = models.TextField(null=True, blank=True)
    paim= models.ForeignKey(Paim, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.datos}-{self.f}"


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="avatar/", default="imagenes/avatar2.png", blank=True, verbose_name="imagen")

    def __str__(self):
        return f"{self.user.username}"


class UserConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    connected_at = models.DateTimeField()
   

    def __str__(self):
        return f"{self.user.username} connected at {self.connected_at}"
