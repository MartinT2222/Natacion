from django.db import models

from USUARIOS.models import CustomUser


class ClaseNatacion(models.Model):
    nombre = models.CharField(max_length=100)
    # Otros campos relevantes para la clase de natación

class HorarioClase(models.Model):
    clase_natacion = models.ForeignKey(ClaseNatacion, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupos_disponibles = models.PositiveIntegerField(default=0)
    # Otros campos relevantes para el horario de la clase

class InscripcionClase(models.Model):
    usuario = models.ForeignKey('USUARIOS.CustomUser', on_delete=models.CASCADE)
    horario_clase = models.ForeignKey(HorarioClase, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    # Otros campos relevantes para la inscripción














#class Alumno(models.Model):
#    nombre = models.CharField(max_length=100)
#    direccion = models.CharField(max_length=255)
#    alumno_id = models.AutoField(primary_key=True)
#    telefono = models.CharField(max_length=15)
#    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')])
#    edad = models.PositiveIntegerField()
#    email = models.EmailField()
#    fecha_inscripcion = models.DateField()
#    telefono_emergencia = models.CharField(max_length=15)
#    mensualidad = models.DecimalField(max_digits=10, decimal_places=2)
#    membresia_vip = models.BooleanField(default=False)
#    alergias = models.TextField(blank=True, null=True)
#    docente_a_cargo = models.CharField(max_length=100, blank=True, null=True)
#    clase_natacion = models.ForeignKey(ClaseNatacion, on_delete=models.CASCADE)
#    pago = models.BooleanField(default=False)
    
#    def enviar_recordatorio_cuota_whatsapp(self):
 #       # Calcular la fecha límite para la renovación de la cuota (30 días después de la fecha de inscripción)
#        fecha_actual = timezone.now()
#        fecha_limite_renovacion = self.fecha_inscripcion + timedelta(days=30)

#        # Verificar si la fecha actual está dentro del período de recordatorio
#        if self.fecha_inscripcion <= fecha_actual <= fecha_limite_renovacion and not self.pago:
#            mensaje = f'Hola {self.nombre}, tu cuota vence pronto y aún no has realizado el pago. Recuerda renovarla a tiempo.'
#
#            # Sustituye '1234567890' con el número de teléfono del alumno en formato internacional
#            numero_whatsapp = f'54{self.telefono}'
#
#            # Comando para enviar el mensaje a través de yowsup-cli
#            comando = f'yowsup-cli demos --send {numero_whatsapp} "{mensaje}"'
#
#            # Ejecuta el comando
#            os.system(comando)
#            
#    def _str_(self):
#        return self.nombre
    
    

#class Turno(models.Model):
#    fecha = models.DateField()
#    hora = models.TimeField()
#    disponible = models.BooleanField(default=True)
#    alumno = models.ForeignKey('TIENDA.Alumno', related_name='turnos', null=True, blank=True, on_delete=models.SET_NULL)
