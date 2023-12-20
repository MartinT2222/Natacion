#from django.contrib import admin
#from .models import ClaseNatacion


#admin.site.register(ClaseNatacion)


#class TurnoAdmin(admin.ModelAdmin):
#    list_display = ('fecha', 'hora', 'disponible')

#admin.site.register(TurnoAdmin)

from django.contrib import admin
from .models import ClaseNatacion, HorarioClase, InscripcionClase

admin.site.register(ClaseNatacion)
admin.site.register(InscripcionClase)

@admin.register(HorarioClase)
class HorarioClaseAdmin(admin.ModelAdmin):
    list_display = ('clase_natacion', 'fecha', 'hora_inicio', 'hora_fin', 'cupos_disponibles')
    list_filter = ('clase_natacion', 'fecha')
    search_fields = ['clase_natacion__nombre']  # Puedes ajustar los campos de búsqueda según sea necesario
