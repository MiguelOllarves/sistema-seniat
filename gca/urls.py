from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


from gca.views import (
    VistaPrincipal,
    FiscalInformacion,
    PasosVista,
    # LoginView,
    # LogoutView,
    NotificationListView,
    PaimVista,
    CrearReport,
    EditarFiscal,
    CrearSubPaim,
    ChartsVista,
    SubChartsVista,
    EliminarFiscal,
    PerfilVista,
    PerfilAvatar,
    EliminarPasos,
    EliminarReporte,
    EditarReporte,
    RegisterView,
    EliminarTarea,
    EditarPaim,
    EliminarPaim,
    RetencionesVista,
    ActivityChartView,
    LoadingPageView,
)

urlpatterns = [
    path("", VistaPrincipal.as_view(), name="principal"),
    path("principal/editar/<int:pk>", EditarFiscal.as_view(), name="editar_fiscal"),
    path("principal/eliminar/<int:pk>", EliminarFiscal.as_view(), name="eliminar"),
    # INDICADOR DE QUE AQUI VA LA INFORMACION DE FISCALES
    path("fiscal_index/<int:pk>", FiscalInformacion.as_view(), name="informacion"),
    path("eliminar/<int:pk>", EliminarTarea.as_view(), name="eliminar_tarea"),
    path("pasos/<int:pk>/", PasosVista.as_view(), name="pasos_vista"),
    path("eliminar/<int:pk>/", EliminarPasos.as_view(), name="eliminar_pasos"),
    # INDICADOR DE QUE AQUI VA LA INFORMACION DE LOGIN Y ACCESO
    # path("login/", LoginView.as_view(), name="login"),
    # path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("registro/", RegisterView.as_view(), name="registro"),
    # INDICADOR DE QUE AQUI VA LA INFORMACION DE FISCALES
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    # paim los paim principal que muestra el grafico y los sub paim
    path("paim/paim/<int:pk>/", PaimVista.as_view(), name="paim"),
    path("paim/editar_paim/<int:pk>/", EditarPaim.as_view(), name="editar_paim"),
    path("paim/eliminar/<int:pk>/", EliminarPaim.as_view(), name="eliminarpaim"),
    path("report/crear/<int:pk>/", CrearReport.as_view(), name="report"),
    path("editar/<int:pk>", EditarReporte.as_view(), name="editar_reporte"),
    path(
        "report/eliminar/<int:pk>/", EliminarReporte.as_view(), name="eliminar_reporte"
    ),
    path("paim/subpaim/paim/<int:id>", CrearSubPaim.as_view(), name="subpaim"),
    # Las Retenciones
    path("retenciones/retenciones", RetencionesVista.as_view(), name="retenciones"),
    # PDF IMPRIMIR REPORTE
    path("pdf/pdf_uno/<int:id>", views.pdf_uno, name="pdf_uno"),
    # grafico charts
    path("charts/<int:id>/", ChartsVista.as_view(), name="charts"),
    path("subcharts/<int:id>/", SubChartsVista.as_view(), name="subcharts"),
    path("actvidad", ActivityChartView.as_view(), name="actividad"),
    # usuario
    path("perfil/", PerfilVista.as_view(), name="perfil"),
    path("avatar/", PerfilAvatar.as_view(), name="avatar"),
    # loander
    path("loading/", LoadingPageView.as_view(), name="loading"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
