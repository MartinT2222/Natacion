from django import forms
from .models import ClaseNatacion, ComprasClase, InscripcionClase
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q


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
        widgets = {
            'precio_clase': forms.TextInput(attrs={'readonly': 'readonly'}),
            'cupos_disponibles_pagos': forms.NumberInput(attrs={'value': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Obtén la lista de nombres de clases sin repeticiones
        nombres_clases = ClaseNatacion.objects.values_list('nombre', flat=True).distinct()
        
        # Crea una lista de tuplas para usar en el campo 'choices'
        choices = [(nombre, nombre) for nombre in nombres_clases]
        
        # Asigna las opciones al campo 'clase_comprada'
        self.fields['clase_comprada'].widget = forms.Select(choices=choices)

    def clean(self):
        cleaned_data = super().clean()
        clase_comprada = cleaned_data.get('clase_comprada')
        
        # Obtén el precio de la clase seleccionada
        precio_clase = ClaseNatacion.objects.get(nombre=clase_comprada).precio
        cleaned_data['precio_clase'] = precio_clase
        
        # Realiza la validación u otras operaciones de limpieza según sea necesario
        return cleaned_data
    
class CompraForm(forms.ModelForm):
    class Meta:
        model = ComprasClase
        fields = ['clase_comprada', 'precio_clase', 'cupos_disponibles_pagos']
        labels = {
            'cupos_disponibles_pagos': 'Horas Mensuales:'
        }
        widgets = {
            'precio_clase': forms.TextInput(attrs={'readonly': 'readonly'}),  
            'cupos_disponibles_pagos': forms.NumberInput(attrs={'value': 1}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Obtén la lista de nombres de clases sin repeticiones
        nombres_clases = ClaseNatacion.objects.values_list('nombre', flat=True).distinct()
        
        # Crea una lista de tuplas para usar en el campo 'choices'
        choices = [(nombre, nombre) for nombre in nombres_clases]
        
        #choices2 = [(precio, precio) for precio in precio_clases]
        # Asigna las opciones al campo 'clase_comprada'
        self.fields['clase_comprada'].widget = forms.Select(choices=choices)
        #self.fields['precio_clase'].widget = forms.Select(choices=choices2)
        
        
    def clean(self):
        cleaned_data = super().clean()
        # Realiza la validación u otras operaciones de limpieza según sea necesario
        return cleaned_data


#precio_clases = ClaseNatacion.objects.values_list('precio', flat=True).distinct()
#        print(f"precio_clases: {precio_clases}")        
        
class InscripcionForm(forms.ModelForm):
    class Meta:
        model = InscripcionClase
        fields = ['clase_natacion']
        
    def __init__(self, usuario, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Calcula la fecha actual
        fecha_actual = datetime.now()

        # Calcula la fecha hasta la que quieres mostrar clases (60 días en este caso)
        fecha_limite = fecha_actual + timedelta(days=60)

        # Obtén la lista de clases disponibles filtradas por usuario, cupos_disponibles y fechas
        clases_disponibles = ClaseNatacion.objects.filter(
            fecha__gte=fecha_actual,  # Filtra clases con fechas mayores o iguales a la actual
            fecha__lte=fecha_limite,  # Filtra clases con fechas menores o iguales a la fecha límite (60 días en el futuro)
            nombre__in=ComprasClase.objects.filter(usuario=usuario).values('clase_comprada').distinct(),  # Filtra clases compradas por el usuario
            cupos_disponibles__gt=0  # Filtra clases con cupos_disponibles mayores a 0
        )

        # Crea una lista de tuplas para usar en el campo 'choices'
        choices = [(clase.id, f"{clase.nombre} - {clase.fecha.strftime('%d/%m/%Y')} - {clase.hora_inicio.strftime('%H:%M')} - {clase.hora_fin.strftime('%H:%M')}") for clase in clases_disponibles]

        # Asigna las opciones al campo 'clase_natacion'
        self.fields['clase_natacion'].choices = choices
        
        # Cambiar el texto del label para el campo 'cupos_disponibles_pagos'
        self.fields['clase_natacion'].label = "Elige una clase de natación disponible:"
