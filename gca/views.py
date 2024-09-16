import requests,socket,time
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.db.models import Count
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.contrib import messages
from django.views import View
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    Http404,
)
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import (
    Fiscales,
    Informacion,
    Pasos,
    Notification,
    User,
    Paim,
    DiariosReport,
    Perfil,
    UserConnection,
)
from .forms import (
    FormFiscales,
    FormInformacion,
    FormPaim,
    FormReport,
    UsuarioForm,
    UserRegisterForm,
    PasosForm1,
)

from django import template
register = template.Library()

@register.filter
def has_perm(user, perm):
    return user.has_perm(perm)


def is_internet_available():
    try:
        socket.setdefaulttimeout(50)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("seniat.gov.ve", 53))
        return True
    except socket.error:
        return False


class LoadingPageView(LoginRequiredMixin, View):
    template_name = "loader/loading.html"
    def get(self, request, *args, **kwargs):
        return render(request,self.template_name)


class RegisterView(CreateView):
    form_class = UserRegisterForm
    model = User
    template_name = "registration/registro.html"
    success_url = reverse_lazy("login")


class PerfilVista(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UsuarioForm
    template_name = "registration/perfil.html"
    success_url = reverse_lazy ("principal")

    def get(self, request):
        form = self.form_class(instance=request.user)

        vistas = Paim.objects.all()

        if self.request.user.is_superuser:
            notifications = Notification.objects.all().order_by("-created_at")

        else:
            notifications = Notification.objects.filter(
                user=self.request.user
            ).order_by("-created_at")

        context = {
            "form": form,
            "notifications": notifications,
            "vistas": vistas,
        }
        return render(request, self.template_name, context)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def post(self, request):
        form = self.form_class(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(self.request, "Perfil Modificado exitosamente.")
            return redirect("principal")
        return render(request, self.template_name, {"form": form})


class PerfilAvatar(LoginRequiredMixin, CreateView):
    template_name = "registration/avatar.html"

    def get(self, request, *args, **kwargs):
        vistas = Paim.objects.all()
        notifications = Notification.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        context = {
            "notifications": notifications,
            "vistas": vistas,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.FILES:
            perfil = Perfil.objects.get_or_create(user=request.user)[0]
            perfil.image = request.FILES["image"]
            perfil.save()
            messages.success(request, "Imagen actualizada exitosamente")
        return redirect("perfil")


class VistaPrincipal(LoginRequiredMixin, View):
    template_name = "principal/index.html"
    form_paim_class = FormPaim
    form_fiscales_class = FormFiscales

    def get_context_data(self):
        fiscal = Fiscales.objects.all()
        vistas = Paim.objects.all()
        tarea = Informacion.objects.all()

        UserConnection.objects.update_or_create(
            user=self.request.user, defaults={"connected_at": timezone.now()}
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        user_connections = (UserConnection.objects.filter(connected_at__date__gte=yesterday).annotate(user_count=Count("user", distinct=True)).order_by("-connected_at__date"))

        today_connections = user_connections.filter(connected_at__date=today).count()
        yesterday_connections = user_connections.filter(connected_at__date=yesterday).count()

        percentage_increase = ((today_connections - yesterday_connections) / yesterday_connections * 100 if yesterday_connections > 0 else 0)

        tareas_terminadas = tarea.filter(estado="Terminado").count()
        tareas_en_proceso = tarea.filter(estado="Proceso").count()
        tareas_falta_un_dia = tarea.filter(estado="Falta un dia").count()
        usuarios_total = User.objects.count()

        if self.request.user.is_superuser:
            notifications = Notification.objects.all().order_by("-created_at")

        else:
            notifications = Notification.objects.filter(
                user=self.request.user
            ).order_by("-created_at")

        form_paim = self.form_paim_class(self.request.user)
        form_fiscales = self.form_fiscales_class(self.request.user)

        context = {
            "fiscales": fiscal,
            "notifications": notifications,  
            "vistas": vistas,
            "tarea": tarea,  
            "tareas_terminadas": tareas_terminadas,
            "tareas_en_proceso": tareas_en_proceso,
            "tareas_falta_un_dia": tareas_falta_un_dia,
            "usuarios_total": usuarios_total,
            "form_fiscales": form_fiscales,
            "form_paim": form_paim,
            "user_connections": user_connections,
            "today_connections": today_connections,
            "percentage_increase": percentage_increase,
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
           
            form_fiscales = self.form_fiscales_class(request.user, request.POST)
            form_paim = self.form_paim_class(request.user, request.POST, request.FILES)

       
            if form_fiscales.is_valid():
                form_fiscales.save()
                messages.success(request, "Se registro Fiscal Exitosamente")
                return redirect("principal")

            elif form_paim.is_valid():
                form_paim.save()
                messages.success(request, "Se registro el Paim Exitosamente")
                return redirect("principal")
            else:
                context = self.get_context_data()
                context["form_fiscales"] = form_fiscales
                context["form_paim"] = form_paim
                return render(request, self.template_name, context)
        
        except TimeoutError:
            messages.error(request, "Se produjo un error de timeout. Verifique su conexión a internet.")
        except requests.Timeout:
            messages.error(
                request,
                "Se produjo un error por el tiempo límite de la red o la conexión es muy lenta."
            )
        except requests.ConnectionError as e:
            messages.error(
                request, "No hay conexión a internet. Por favor, verifique su conexión."
            )
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
        
        return redirect("principal")


class EditarFiscal(LoginRequiredMixin, UpdateView):
    model = Fiscales
    form_class = FormFiscales
    template_name = "principal/editar.html"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para editar este registro")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        return super(EditarFiscal, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Fiscal editado exitosamente.")
        return reverse_lazy("principal")

    def get_object(self, queryset=None):

        obj = super().get_object(queryset)
        if obj is None:
            raise Http404("No se encontró el Fiscal especificado.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_fiscales"] = self.get_form()
        return context


class EliminarFiscal(LoginRequiredMixin, DeleteView):
    model = Fiscales
    template_name = "principal/eliminar.html"
    success_url = reverse_lazy("principal")

    def get_success_url(self):
        messages.success(self.request, "Fiscal Eliminado exitosamente.")
        return reverse_lazy("principal")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para eliminar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EliminarFiscal, self).dispatch(request, *args, **kwargs)


class FiscalInformacion(LoginRequiredMixin, View):
    model = Informacion
    template_name = "info/fiscal_index.html"
    form_class = FormInformacion

    def get(self, request, pk, *args, **kwargs):

        try:

            fiscal = Fiscales.objects.get(pk=pk)

        except Fiscales.DoesNotExist:

            messages.error(request, "No existe un fiscal con ese ID")

            return redirect("principal")

        tarea = Informacion.objects.filter(fiscales=fiscal).order_by("-fecha_entrada")

        tareas_terminadas = tarea.filter(estado="Completado").count()
        tareas_en_proceso = tarea.filter(estado="Proceso").count()
        tareas_falta_un_dia = tarea.filter(estado="Falta un dia").count()

        for t in tarea:
            pasos_completed = t.pasos_set.filter(completado=True).count()
            if pasos_completed >= 12:
                if t.estado in ["Proceso", "Falta un dia"]:
                    t.estado = "Completado"
                    t.save()

        if self.request.user.is_superuser:
            notifications = Notification.objects.all().order_by("-created_at")

        else:
            notifications = Notification.objects.filter(
                user=self.request.user
            ).order_by("-created_at")

        vistas = Paim.objects.all()

        form_tarea = kwargs.get("form_tarea")
        if form_tarea is None:
            form_tarea = self.form_class(request.user)

        context = {
            "fiscal": fiscal,
            "tarea": tarea,
            "notifications": notifications,
            "vistas": vistas,
            "tareas_terminadas": tareas_terminadas,
            "tareas_en_proceso": tareas_en_proceso,
            "tareas_falta_un_dia": tareas_falta_un_dia,
            "form_tarea": form_tarea,
        
        }
        return render(request, "info/fiscal_index.html", context)

    def post(self, request, *args, **kwargs):
        
        try:
            if not is_internet_available():
                messages.error(
                    request, "Conéctese a la red, no podrá recibir notificaciones."
                )
                return self.get(request, kwargs.get("principal"))
            
            form_tarea = FormInformacion(request.user, request.POST)

            if form_tarea.is_valid():
                form_tarea.save()
                pk = kwargs.get("pk", None)
                if pk:
                    messages.success(request, "Se creo una Tarea con Exito")
                    return redirect("informacion", pk=pk)
                else:
                    messages.error(self.request,"Se encontro un Error en la Tarea")
                    return redirect("informacion", pk=pk)

            else:
                return self.get(request, kwargs.get("pk"), form_tarea=form_tarea)
            
        except TimeoutError:
            messages.error(
                request,
                "Se produjo un error de timeout. Verifique su conexión a internet.",
            )
        except requests.Timeout:
            messages.error(
                request,
                "Se produjo un error por el tiempo límite de la red o la conexión es muy lenta.",
            )
        except requests.ConnectionError as e:
            messages.error(
                request, "No hay conexión a internet. Por favor, verifique su conexión."
            )
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {str(e)}")

        return redirect("principal")


class EliminarTarea(LoginRequiredMixin, DeleteView):
    model = Informacion
    template_name = "info/eliminar.html"
    success_url = reverse_lazy("informacion")

    def get_success_url(self):
        pk = self.kwargs["pk"]
        diario_obj = Informacion.objects.get(pk=pk)
        paim_obj = diario_obj.fiscales
        if paim_obj:
            messages.success(self.request, "Tarea o Actividad Eliminada exitosamente.")
            return reverse_lazy("informacion", args=[paim_obj.pk])
        else:
            messages.error(self.request, "No se encontró el Tarea asociado al Fiscal o Funcionario.")
            return reverse_lazy("principal")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para eliminar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EliminarTarea, self).dispatch(request, *args, **kwargs)


class PasosVista(LoginRequiredMixin, View):
    model = Pasos
    template_name = "evaluacion/pasos.html"
    form_class = PasosForm1

    def get(self, request, pk, *args, **kwargs):

        form = kwargs.get("form")
        if form is None: 
            form = self.form_class(request.user)

        tarea_obj = Informacion.objects.get(pk=pk)
        vistas = Paim.objects.all()
        fiscal_obj = tarea_obj.fiscales
        pasos = Pasos.objects.filter(tarea=tarea_obj).order_by("nombre")
        fiscal = fiscal_obj

        if self.request.user.is_superuser:
            notifications = Notification.objects.all().order_by("-created_at")
        else:
            notifications = Notification.objects.filter(
                user=self.request.user
            ).order_by("-created_at")

        context = {
            "notifications": notifications,
            "pasos": pasos,
            "tarea": tarea_obj,
            "fiscal": fiscal,
            "vistas": vistas,
            "form": form
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        try:
            if not is_internet_available():
                messages.error(
                    request, "Conéctese a la red, no podrá recibir notificaciones."
                )
                return self.get(request, kwargs.get("principal"))

            form = self.form_class(request.user, request.POST, request.FILES)

            if form.is_valid():
                new_pasos = form.save(commit=False)
                new_pasos.completado = True
                new_pasos.save()

                pk = kwargs.get("pk", None)
                tarea = Informacion.objects.get(pk=pk)
                if Pasos.son_completados([new_pasos]):
                    tarea.estado = ""
                    tarea.save()

                messages.success(request, "Se registro Archivo")
                return redirect("pasos_vista", pk=pk)
            else:
                return self.get(request, kwargs.get("pk"), form=form)
            
        except TimeoutError:
            messages.error(
                request,
                "Se produjo un error de timeout. Verifique su conexión a internet.",
            )
        except requests.Timeout:
            messages.error(
                request,
                "Se produjo un error por el tiempo límite de la red o la conexión es muy lenta.",
            )
        except requests.ConnectionError as e:
            messages.error(
                request, "No hay conexión a internet. Por favor, verifique su conexión."
            )
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {str(e)}")

        return redirect("principal")


class EliminarPasos(LoginRequiredMixin, DeleteView):
    model = Pasos
    template_name = "evaluacion/eliminar.html"
    success_url = reverse_lazy("pasos_vista")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para eliminar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EliminarPasos, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        diario_obj = Pasos.objects.get(pk=pk)
        paim_obj = diario_obj.tarea
        if paim_obj:
            messages.success(self.request, "Paso Eliminado exitosamente.")
            return reverse_lazy("pasos_vista", args=[paim_obj.pk])
        else:
            messages.error(self.request, "No se encontró el Paso asociado a la Tarea.")
            return reverse_lazy("principal")


@receiver(post_save, sender=Pasos)
def send_notification(instance, created, *args, **kwargs):
    if created:
        subject = f"{instance.user.first_name} {instance.user.last_name} Realizo una Accion"
        message = f"Este Usuario a subido Archivo de la Tarea o Actividad asignada {instance.nombre}"

        user = instance.user
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

        Notification.objects.create(
            title=f"Este Usuario subio un Archivo de la Tarea ",
            message=f" {instance.nombre}",
            user=user,
        )

@receiver(post_save, sender=Fiscales)
def fiscales_notification(sender, instance, created, *args, **kwargs):
    if created:
            subject = f"{instance.user.first_name} {instance.user.last_name}"
            message = f"Este Usuario Realizo el Registro de un Funcionario"

            user = instance.user
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

            Notification.objects.create(
                title=f"Este Usuario Realizo el Registro de un Funcionario",
                message=f"{instance.datos_fical}",
                user=user,
            )

@receiver(post_save, sender=Paim)
def paim_notification(sender, instance, created, *args, **kwargs):
    if created:
            subject = f"{instance.user.first_name} {instance.user.last_name}"
            message = f"El presente usuario realizo el registro de un paim"

            user = instance.user
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

            Notification.objects.create(
                title=f"{instance.name}",
                message=f"Este Usuario Realizo el Registro de un Paim",
                user=user,
            )

@receiver(post_save, sender=Informacion)
def tareas_notification(sender, instance, created, *args, **kwargs):
    if created:
        subject = f"{instance.user.first_name} {instance.user.last_name}"
        message = f"El presente Usuario creo una Actividad sobre {instance.tarea} "

        user = instance.user
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

        Notification.objects.create(
            title=f"Este Usuario Realizo el Registro de una Tarea",
            message=f"{instance.tarea}",
            user=user,
        )

class NotificationListView(LoginRequiredMixin, View):
    template_name = "principal/notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        
        if self.request.user.is_superuser:
            return Notification.objects.all().order_by("-created_at")
        else:
            return Notification.objects.filter(user=self.request.user).order_by(
                "-created_at"
            )

    def get(self, request):
        vistas = Paim.objects.all()

        notifications = self.get_queryset()
        unread_notifications = notifications.filter(
            read=False
        ).count()  # Contar notificaciones no leídas
        for notification in notifications:
            if (
                not notification.read and self.request.user.is_superuser
            ):  # Solo marcar como leído si el usuario es superusuario
                notification.read = True
                notification.save()  # Marcar notificaciones como leídas
        return render(
            request,
            self.template_name,
            {
                self.context_object_name: notifications,
                "unread_notifications": unread_notifications,
                "vistas":vistas
            },
        )


# """ REALIZAR TODOS LOS PUNTOS DE PAIM CON IMAGENES Y CORDENADAS """

class PaimVista(LoginRequiredMixin, View):

    def get(self, request, pk):

        paim = get_object_or_404(Paim, pk=pk)
        report = DiariosReport.objects.filter(paim=paim)

        vt = report.aggregate(Sum("vt"))["vt__sum"] or 0
        plc_ex = report.aggregate(Sum("plc_ex"))["plc_ex__sum"] or 0
        vr = report.aggregate(Sum("vr"))["vr__sum"] or 0
        mta = report.aggregate(Sum("mta"))["mta__sum"] or 0
        mdua = report.aggregate(Sum("mdua"))["mdua__sum"] or 0
        mn = report.aggregate(Sum("mn"))["mn__sum"] or 0

        context = {
            "paim": paim,
            "vistas": Paim.objects.all(),
            "report": report,
            "vt": vt,
            "plc_ex": plc_ex,
            "vr": vr,
            "mta": mta,
            "mdua": mdua,
            "mn": mn,
        }
        return render(request, "paim/paim.html", context)


# EDITAR EL PAIM
class EditarPaim(LoginRequiredMixin, UpdateView):
    model = Paim
    form_class = FormPaim
    template_name = "paim/editar_paim.html"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para editar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EditarPaim, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Paim editado exitosamente.")
        return reverse_lazy("principal")

    def get_object(self, queryset=None):

        obj = super().get_object(queryset)
        if obj is None:
            raise Http404("No se encontró el Piam especificado.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_paim"] = self.get_form()
        context["vistas"] = Paim.objects.all()
        return context


class EliminarPaim(LoginRequiredMixin, DeleteView):
    model = Paim
    template_name = "paim/eliminar_paim.html"
    success_url = reverse_lazy("principal")

    def get_success_url(self):
        messages.success(self.request, "Paim Eliminado exitosamente.")
        return reverse_lazy("principal")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para eliminar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EliminarPaim, self).dispatch(request, *args, **kwargs)


class CrearReport(LoginRequiredMixin, CreateView):
    form_class = FormReport
    template_name = "report/crear.html"
    success_url = reverse_lazy("paim")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        context["form_report"] = self.get_form()
        context["vistas"] = Paim.objects.all()
        context["ver"] = Paim.objects.get(pk=pk)

        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Reporte creado exitosamente.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Hubo un error al crear el reporte.")
        return super().form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        if pk:
            return reverse_lazy("paim", args=[pk])
        else:
            return self.success_url


# Vista para editar reporte
class EditarReporte(LoginRequiredMixin, UpdateView):
    model = DiariosReport
    form_class = FormReport
    template_name = "report/editar.html"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para Editar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EditarReporte, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        diario_obj = DiariosReport.objects.get(pk=pk)
        paim_obj = diario_obj.paim
        if paim_obj:
            messages.success(self.request, "Reporte editado exitosamente.")
            return reverse_lazy("paim", args=[paim_obj.pk])
        else:
            messages.error(self.request, "No se encontró el Paim asociado al reporte.")
            return reverse_lazy("principal")

    def get_object(self, queryset=None):

        obj = super().get_object(queryset)
        if obj is None:
            raise Http404("No se encontró el Reporte especificado.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        diario_obj = self.object
        paim_obj = diario_obj.paim
        context["form_report"] = self.get_form()
        context["ver"] = paim_obj
        context["vistas"] = Paim.objects.all()
        return context


# eliminar reporte
class EliminarReporte(LoginRequiredMixin, DeleteView):
    model = DiariosReport
    template_name = "report/eliminar.html"
    success_url = reverse_lazy("paim")

    def get_success_url(self):
        pk = self.kwargs["pk"]
        diario_obj = DiariosReport.objects.get(pk=pk)
        paim_obj = diario_obj.paim
        if paim_obj:
            messages.success(self.request, "Reporte Eliminado exitosamente.")
            return reverse_lazy("paim", args=[paim_obj.pk])
        else:
            messages.error(self.request, "No se encontró el Paim asociado al reporte.")
            return reverse_lazy("principal")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para eliminar este registro")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return super(EliminarReporte, self).dispatch(request, *args, **kwargs)


# vista para crear sub paim
class CrearSubPaim(LoginRequiredMixin, View):

    def get(self, request, id, *args, **kwargs):

        contador = DiariosReport.objects.get(pk=id)

        context = {
            "fiscales": Fiscales.objects.all(),
            "vistas": Paim.objects.all(),
            "contador": contador,
        }
        return render(request, "paim/subpaim/paim.html", context)


class RetencionesVista(LoginRequiredMixin,  View):
    template_name = "retenciones/retenciones.html"

    def get(self, request, *args, **kwargs):
        vistas = Paim.objects.all()

        context ={"vistas": vistas,}
        return render(request, self.template_name, context)


# pdf imprimir crear reporte

def pdf_uno(request, id):

    img_uno = settings.STATIC_ROOT + "/imagenes/seniat.png"

    reporte = DiariosReport.objects.get(pk=id)
    template = get_template("pdf/pdf_uno.html")
    context = {"reporte": reporte, "img_uno": img_uno}
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="reporte_diarios.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Nuevo error <pre>" + html + "</pre>")
    return response


# vista de los chartjs o graficos
class ActivityChartView(LoginRequiredMixin, View):
    def get(self, request):
        # Agrupa las conexiones por fecha y cuenta el número de usuarios únicos por fecha
        connections_data = (
            UserConnection.objects.values("connected_at__date")
            .annotate(user_count=Count("user", distinct=True))
            .order_by("connected_at__date")
        )

        labels = [connection["connected_at__date"] for connection in connections_data]
        data = [connection["user_count"] for connection in connections_data]

        return JsonResponse({"data": data, "labels": labels})


class ChartsVista(LoginRequiredMixin, View):
    def get(self, request, id):
        paim = Paim.objects.get(pk=id)
        report = DiariosReport.objects.filter(paim=paim)

        data = {
            "labels": [
                "Vehiculos Transitarón (VT)",
                "Placas Extranjeras Transitaron(V-PLCEX-T)",
                "Vehiculos Revisados (VR)",
                "Mercancia en Transito Aduanero (MTA)",
                "Mercancia con Declaración Única de Aduanas (MDUA)",
                "Mercancia Nacional (MN)",
                "Retención Preventiva (RP)",
                "Numero de Documentación (ND)",
            ],
            "series": [
                {
                    "name": "Vehiculos Transitados",
                    "data": [report.aggregate(Sum("vt"))["vt__sum"] or 0],
                },
                {
                    "name": "Placa de Vehiculos Extrajeros",
                    "data": [report.aggregate(Sum("plc_ex"))["plc_ex__sum"] or 0],
                },
                {
                    "name": "Vehiculos Revisados",
                    "data": [report.aggregate(Sum("vr"))["vr__sum"] or 0],
                },
                {
                    "name": "Mercancia de Transito Aduanero",
                    "data": [report.aggregate(Sum("mta"))["mta__sum"] or 0],
                },
                {
                    "name": "Mercancia de Declaracion Unica de Aduana",
                    "data": [report.aggregate(Sum("mdua"))["mdua__sum"] or 0],
                },
                {
                    "name": "Mercancia Nacionales",
                    "data": [report.aggregate(Sum("mn"))["mn__sum"] or 0],
                },
                {
                    "name": "Retencion Preventiva",
                    "data": [report.aggregate(Sum("rp"))["rp__sum"] or 0],
                },
                {
                    "name": "Numero de Documentos",
                    "data": [report.aggregate(Sum("nd"))["nd__sum"] or 0],
                },
            ],
        }
        return JsonResponse(data)


class SubChartsVista(LoginRequiredMixin, View):
    def get(self, request, id):
        report = DiariosReport.objects.get(pk=id)

        data = {
            "labels": [
                "Vehiculos Transitarón (VT)",
                "Placas Extranjeras Transitaron(V-PLCEX-T)",
                "Vehiculos Revisados (VR)",
                "Mercancia en Transito Aduanero (MTA)",
                "Mercancia con Declaración Única de Aduanas (MDUA)",
                "Mercancia Nacional (MN)",
                "Retención Preventiva (RP)",
                "Numero de Documentación (ND)",
            ],
            "series": [
                {
                    "name": "Vehiculos Transitados",
                    "data": [report.vt],
                },
                {
                    "name": "Placa de Vehiculos Extrajeros",
                    "data": [report.plc_ex],
                },
                {
                    "name": "Vehiculos Revisados",
                    "data": [report.vr],
                },
                {
                    "name": "Mercancia de Transito Aduanero",
                    "data": [report.mta],
                },
                {
                    "name": "Mercancia de Declaracion Unica de Aduana",
                    "data": [report.mdua],
                },
                {
                    "name": "Mercancia Nacionales",
                    "data": [report.mn],
                },
                {
                    "name": "Retencion Preventiva",
                    "data": [report.rp],
                },
                {
                    "name": "Numero de Documentos",
                    "data": [report.nd],
                },
            ],
        }
        return JsonResponse(data)
