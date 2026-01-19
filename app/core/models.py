from django.db import models

class MSSQLServer(models.Model):
    nombre = models.CharField(max_length=100, help_text="Nombre identificador del servidor")
    host = models.CharField(max_length=255, help_text="IP o Hostname del servidor SQL")
    database = models.CharField(max_length=100, help_text="Base de datos por defecto")
    usuario = models.CharField(max_length=100, help_text="Usuario SQL")
    password_encrypted = models.CharField(max_length=500, blank=True, help_text="Contraseña encriptada")

    def __str__(self):
        return f"{self.nombre} ({self.host})"

class CategoriaReporte(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=50, default="fas fa-folder", help_text="Clase FontAwesome, ej: fas fa-chart-line")
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

class Reporte(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaReporte, on_delete=models.CASCADE, related_name='reportes')
    sp_nombre = models.CharField(max_length=100, help_text="Nombre del Stored Procedure en SQL Server")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class ConsultaAuditoria(models.Model):
    usuario = models.CharField(max_length=150)
    sp_ejecutado = models.CharField(max_length=255)
    parametros = models.TextField()
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField(default=False)
    mensaje_error = models.TextField(null=True, blank=True)
