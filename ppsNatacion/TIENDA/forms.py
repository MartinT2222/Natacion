from django import forms
from .models import ClaseNatacion, Alumno

class ClaseNatacionForm(forms.ModelForm):
    class Meta:
        model = ClaseNatacion
        fields = ['especialidad', 'nombre_docente', 'precio', 'tipo_pago', 'plan_elegido', 'fecha_clase', 'horas_clase']
        widgets = {
            'fecha_clase': forms.DateInput(attrs={'type': 'date'}),
            'horas_clase': forms.TimeInput(attrs={'type': 'time'}),
        }

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = [ 'nombre', 'direccion', 'telefono', 'sexo', 'edad', 'email', 
                  'fecha_inscripcion', 'telefono_emergencia', 'mensualidad', 'membresia_vip', 
                  'alergias', 'docente_a_cargo', 'pago','clase_natacion']
        widgets = {
            'fecha_inscripcion': forms.DateInput(attrs={'type': 'date'}),
            'pago': forms.CheckboxInput(),
        }