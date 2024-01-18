from django import forms
from .models import ClaseNatacion, ComprasClase
from datetime import datetime, timedelta

class ClaseNatacionForm(forms.ModelForm):
    DIAS_SEMANA_CHOICES = (
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
    )
    
    dias_semana = forms.MultipleChoiceField(
        choices=DIAS_SEMANA_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    # Campo para la imagen
    imagen = forms.ImageField(required=False)  


    def generar_horarios_recurrentes(dias_semana, hora_inicio, hora_fin):
            # Generar horarios recurrentes según los días seleccionados
        horarios = []
        dias = {'LUN': 0, 'MAR': 1, 'MIE': 2, 'JUE': 3, 'VIE': 4, 'SAB': 5, 'DOM': 6}
        today = datetime.today()
        for dia in dias_semana:
            delta_days = (dias[dia] - today.weekday() + 7) % 7
            fecha = today + timedelta(days=delta_days)
            fecha = fecha.replace(hour=hora_inicio.hour, minute=hora_inicio.minute, second=0, microsecond=0)
            while fecha <= today + timedelta(days=365):  # Limitar el rango a un año
                horarios.append(fecha)
                fecha += timedelta(days=7)
        return horarios
        
    class Meta:
        model = ClaseNatacion
        fields = ['nombre', 'hora_inicio', 'hora_fin', 'cupos_disponibles', 'precio', 'imagen']
        
class CompraForm(forms.ModelForm):
    class Meta:
        model = ComprasClase
        fields = ['clase_comprada', 'precio_clase', 'cupos_disponibles_pagos']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Obtén la lista de nombres de clases sin repeticiones
        nombres_clases = ClaseNatacion.objects.values_list('nombre', flat=True).distinct()

        # Crea una lista de tuplas para usar en el campo 'choices'
        choices = [(nombre, nombre) for nombre in nombres_clases]

        # Asigna las opciones al campo 'clase_comprada'
        self.fields['clase_comprada'].widget = forms.Select(choices=choices)