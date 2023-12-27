from django.contrib import admin
from .models import ClaseNatacion, InscripcionClase

@admin.register(ClaseNatacion)
class ClaseNatacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'hora_inicio', 'hora_fin', 'cupos_disponibles')
    search_fields = ('nombre', 'fecha')
    list_filter = ('fecha',)

@admin.register(InscripcionClase)
class InscripcionClaseAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'clase_natacion', 'fecha_inscripcion', 'obtener_nombre_clase', 'obtener_fecha', 'obtener_hora_inicio', 'obtener_hora_fin', 'obtener_cupos_disponibles')
    search_fields = ('usuario__username', 'clase_natacion__nombre')
    list_filter = ('fecha_inscripcion',)
