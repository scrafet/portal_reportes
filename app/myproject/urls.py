from django.contrib import admin
from django.urls import path
from core.views import (
    home, ReporteExecutorView, 
    reporte_list, reporte_create, reporte_update, reporte_delete,
    categoria_list, categoria_create, categoria_update, categoria_delete,
    usuario_list, usuario_create, usuario_update, usuario_delete,
    reporte_wizard_connection, reporte_wizard_discovery
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('reporte-executor/', ReporteExecutorView.as_view(), name='reporte_executor'),
    
    # Reportes
    path('reportes/', reporte_list, name='reporte_list'),
    path('reportes/nuevo/', reporte_create, name='reporte_create'),
    path('reportes/editar/<int:pk>/', reporte_update, name='reporte_update'),
    path('reportes/eliminar/<int:pk>/', reporte_delete, name='reporte_delete'),
    
    # Wizard
    path('reportes/wizard/conexion/', reporte_wizard_connection, name='reporte_wizard_connection'),
    path('reportes/wizard/discovery/', reporte_wizard_discovery, name='reporte_wizard_discovery'),

    # Categorias
    path('categorias/', categoria_list, name='categoria_list'),
    path('categorias/nuevo/', categoria_create, name='categoria_create'),
    path('categorias/editar/<int:pk>/', categoria_update, name='categoria_update'),
    path('categorias/eliminar/<int:pk>/', categoria_delete, name='categoria_delete'),

    # Usuarios
    path('usuarios/', usuario_list, name='usuario_list'),
    path('usuarios/nuevo/', usuario_create, name='usuario_create'),
    path('usuarios/editar/<int:pk>/', usuario_update, name='usuario_update'),
    path('usuarios/eliminar/<int:pk>/', usuario_delete, name='usuario_delete'),
]
