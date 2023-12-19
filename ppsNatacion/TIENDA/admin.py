from django.contrib import admin
from .models import ClaseNatacion, Alumno, Turno


admin.site.register(ClaseNatacion)
admin.site.register(Alumno)

class TurnoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'disponible', 'alumno')

admin.site.register(Turno, TurnoAdmin)