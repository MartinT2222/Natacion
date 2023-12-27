from django import forms
from .models import ClaseNatacion

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
        widget=forms.CheckboxSelectMultiple,
        required=False  # Ajusta esto según tus necesidades
    )

    class Meta:
        model = ClaseNatacion
        fields = ['nombre', 'hora_inicio', 'hora_fin', 'cupos_disponibles']
