from django.contrib import admin
from .models import ConsultaAuditoria, CategoriaReporte, Reporte, MSSQLServer

@admin.register(ConsultaAuditoria)
class ConsultaAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'sp_ejecutado', 'fecha_hora', 'ip_origen', 'exitoso')
    list_filter = ('exitoso', 'fecha_hora', 'usuario')
    search_fields = ('sp_ejecutado', 'parametros', 'mensaje_error')
    readonly_fields = ('fecha_hora',)

@admin.register(CategoriaReporte)
class CategoriaReporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activo')
    list_editable = ('orden', 'activo')

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'sp_nombre', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'sp_nombre')

@admin.register(MSSQLServer)
class MSSQLServerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'host', 'database')
