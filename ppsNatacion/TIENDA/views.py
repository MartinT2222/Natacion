

from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.query_utils import Q
from django.http import JsonResponse
from USUARIOS.models import CustomUser
from USUARIOS.forms import RegistroForm
from .forms import ClaseNatacionForm, HorarioClaseForm  # Importa el formulario de clase de natación
from .models import ClaseNatacion, InscripcionClase, HorarioClase
from datetime import datetime, timedelta
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseServerError



def home(request):
    # Aquí puedes agregar la lógica que desees para la página de inicio
    # Por ejemplo, podrías obtener algunos datos de la base de datos y pasarlos a la plantilla
    # Luego renderiza la plantilla y envía los datos como contexto

    # Ejemplo de datos (puedes personalizar estos datos según tu aplicación)
    data = {
        'titulo': 'Bienvenido a nuestro sitio',
        'mensaje': 'Esto es un mensaje de bienvenida',
        # Otros datos que desees enviar a la plantilla
    }

    # Renderiza la plantilla y envía el contexto
    return render(request, 'tienda/index.html', data)



def buscar(request):
    buscar = request.GET['buscar']
    usuario = CustomUser.objects.filter(
        Q(descripcion__icontains=buscar) | Q(titulo__icontains=buscar))

    return render(request, 'tienda/buscar.html', {

        'usuario': usuario,

    })

@permission_required('TIENDA.lista_alumnos')
def lista_alumnos(request):
    usuarios = CustomUser.objects.filter(is_superuser=False)
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if 'eliminar' in request.POST:
            usuario_id = request.POST.get('alumno_id')  # Corregir obtención del ID del usuario a eliminar
            usuario_eliminar = CustomUser.objects.get(pk=usuario_id)
            usuario_eliminar.delete()
            return redirect('tienda:lista_alumnos')

    else:
        form = RegistroForm()

    return render(request, 'tienda/lista_alumnos.html', {'usuarios': usuarios, 'form': form})



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

def agregar_clase_natacion(request):
    if request.method == 'POST':
        clase_form = ClaseNatacionForm(request.POST)
        horario_form = HorarioClaseForm(request.POST)
        if clase_form.is_valid() and horario_form.is_valid():
            nueva_clase = clase_form.save()

            hora_inicio = horario_form.cleaned_data['hora_inicio']
            hora_fin = horario_form.cleaned_data['hora_fin']
            dias_semana = horario_form.cleaned_data['dias_semana']

            # Obtener horarios recurrentes para la nueva clase
            horarios_recurrentes = generar_horarios_recurrentes(dias_semana, hora_inicio, hora_fin)

            for fecha in horarios_recurrentes:
                clases_superpuestas = HorarioClase.objects.filter(
                    fecha=fecha,
                    hora_inicio__lte=hora_fin,
                    hora_fin__gte=hora_inicio
                )

                if clases_superpuestas.exists():
                    messages.error(request, '¡La clase se superpone con otra existente!')
                    return redirect('tienda:agregar_clase')

            # Si no hay superposición, procedes a guardar la nueva clase
            HorarioClase.objects.create(
                clase_natacion=nueva_clase,
                fecha=fecha,  # Aquí debes definir la fecha apropiada para guardar
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                cupos_disponibles=horario_form.cleaned_data['cupos_disponibles']
            )
            messages.success(request, 'La clase se ha guardado exitosamente!')
            return redirect('tienda:agregar_clase')
    else:
        clase_form = ClaseNatacionForm()
        horario_form = HorarioClaseForm()
    return render(request, 'tienda/agregar_clase.html', {'clase_form': clase_form, 'horario_form': horario_form})



@login_required
def asociar_usuario_clases(request):
    if request.method == 'POST':
        try:
            usuario = request.user  # Acceder al usuario autenticado
            clase_id = request.POST.get('clase_id')  # Obtener el ID de la clase seleccionada

            # Obtener la clase usando el ID obtenido
            clase = get_object_or_404(ClaseNatacion, pk=clase_id)

            # Verificar si se reciben los datos esperados
            print(f"Usuario: {usuario}")
            print(f"Clase ID: {clase_id}")

            # Obtener el horario de la clase
            horario_clase = clase.horarioclase_set.first()  # Ajusta esto según la lógica de tu aplicación

            # Verificar si se están obteniendo las clases y los horarios correctamente
            print(f"Clase: {clase}")
            print(f"Horario Clase: {horario_clase}")

            # Si ambas entidades existen, proceder con la inscripción
            if usuario and clase and horario_clase:
                InscripcionClase.objects.create(usuario=usuario, horario_clase=horario_clase, fecha_inscripcion=timezone.now())
                # Lógica adicional como redirección o mensajes de éxito
        except Exception as e:
            # Captura cualquier excepción y muestra información útil para depuración
            print(f"Error: {e}")
            return HttpResponseServerError('Internal Server Error')

    clases = ClaseNatacion.objects.all()
    return render(request, 'tienda/asociar_usuario_clases.html', {'clases': clases})


def get_horarios_clase(request):
    # Obtener horarios de clases y convertirlos a formato de eventos
    horarios = HorarioClase.objects.all()
    eventos = []

    for horario in horarios:
        evento = {
            'id': horario.id,  # Debes asegurarte de tener un identificador único para cada evento
            'title': horario.clase_natacion.nombre,
            'start': horario.fecha.strftime('%Y-%m-%d') + 'T' + horario.hora_inicio.strftime('%H:%M:%S'),
            'end': horario.fecha.strftime('%Y-%m-%d') + 'T' + horario.hora_fin.strftime('%H:%M:%S'),
            # Otros campos que puedas necesitar para el evento
        }
        eventos.append(evento)
    return JsonResponse(eventos, safe=False)






'''



def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(User, pk=alumno_id)
    return render(request, 'detalle_alumno.html', {'alumno': alumno})


#@permission_required('TIENDA.agregar_alumno_y_clase')
#def agregar_alumno_y_clase(request):
#    alumno_form = None
#    clase_natacion_form = None
#    if request.method == 'POST':
#        # Si el formulario de alumno es enviado
#        if 'alumno_form' in request.POST:
#            alumno_form = AlumnoForm(request.POST)
#            if alumno_form.is_valid():
#                # Guardar el alumno en la base de datos
#                alumno = alumno_form.save()
                # Redireccionar o hacer lo que necesites con el alumno

#        # Si el formulario de clase de natación es enviado
#        elif 'clase_natacion_form' in request.POST:
#            clase_natacion_form = ClaseNatacionForm(request.POST)
#            if clase_natacion_form.is_valid():
#                # Guardar la clase de natación en la base de datos
#                # Redireccionar o hacer lo que necesites con la clase de natación
#                clase_natacion = clase_natacion_form.save(commit=False)
#                clase_natacion.clase_id = clase_natacion_form.cleaned_data.get('clase_id')  # Aquí debes asignar el valor correcto
#                clase_natacion.save()  # Ahora puedes guardarla en la base de datos
#    else:
#        alumno_form = AlumnoForm()
#        clase_natacion_form = ClaseNatacionForm()

#    return render(request, 'tienda/agregar_alumno_y_clase.html', {
#        'alumno_form': alumno_form,
#        'clase_natacion_form': clase_natacion_form,
#    })


@permission_required('TIENDA.agregar_clase')
def agregar_clase(request):
    if request.method == 'POST':
        if 'clase_natacion_form' in request.POST:
                clase_natacion_form = ClaseNatacionForm(request.POST)
                if clase_natacion_form.is_valid():
                    # Guardar la clase de natación en la base de datos
                    # Redireccionar o hacer lo que necesites con la clase de natación
                    clase_natacion = clase_natacion_form.save(commit=False)
                    clase_natacion.clase_id = clase_natacion_form.cleaned_data.get('clase_id')  # Aquí debes asignar el valor correcto
                    clase_natacion.save()  # Ahora puedes guardarla en la base de datos
    else:
        clase_natacion_form = ClaseNatacionForm()

    return render(request, 'tienda/agregar_clase.html', {'clase_natacion_form': clase_natacion_form})



@permission_required('TIENDA.agregar_alumno')
def agregar_alumno(request):
    if request.method == 'POST':
        alumno_form = User(request.POST)
        if alumno_form.is_valid():
            # Guardar el alumno en la base de datos
            alumno = User.save()
            # Obtener los datos del alumno
            datos_alumno = {
                'alumno_id': alumno.id,
                'nombre': alumno.nombre,
                'direccion': alumno.direccion,
                'telefono': alumno.telefono,
                'sexo': alumno.get_sexo_display(),
                'edad': alumno.edad,
                'email': alumno.email,
                'telefono_emergencia': alumno.telefono_emergencia,
                'alergias': alumno.alergias,
                
                # Agrega más datos según los que quieras mostrar
            }
            return render(request, 'tienda/agregar_alumno.html', {'alumno_form': alumno_form, 'datos_alumno': datos_alumno})
    else:
        alumno_form = AlumnoForm()

    return render(request, 'tienda/agregar_alumno.html', {'alumno_form': alumno_form})


def crear_actualizar_alumno(request, alumno_id=None):
    # ... lógica para crear o actualizar un alumno ...

    # Obtener el alumno según el ID proporcionado
    alumno = get_object_or_404(User, id=alumno_id)

    # Después de crear o actualizar el alumno, enviar el recordatorio de cuota
    alumno.enviar_recordatorio_cuota_whatsapp()

    # Verificar si el pago está marcado como pagado
    if alumno.pago:
        # Actualizar la fecha de inscripción si el pago está marcado como pagado
        alumno.fecha_inscripcion = timezone.now().date()
        alumno.save()
    
    # Resto del código para renderizar la página
    return render(request, 'tienda/lista_alumnos.html', {'alumnos': [alumno]})



@permission_required('TIENDA.edit_alumno')
def editar_alumno(request, alumno_id):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        sexo = request.POST.get('sexo')
        edad = request.POST.get('edad')
        pago = request.POST.get('pago')

        try:
            alumno = get_object_or_404(Alumno, pk=alumno_id)
            alumno.nombre = nombre
            alumno.direccion = direccion
            alumno.telefono = telefono
            alumno.sexo = sexo
            alumno.edad = edad

            # Validación y conversión del campo 'pago' a booleano
            pago_bool = pago.lower() == 'true' if pago.lower() in ['true', 'false'] else False
            alumno.pago = pago_bool

            # Guardar los cambios
            alumno.save()

            # Redirigir a la lista de alumnos después de editar exitosamente
            return redirect('tienda:lista_alumnos')

        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'})
    
    return JsonResponse({'success': False, 'error': 'Método no válido'})
'''
'''
@csrf_exempt
@permission_required('TIENDA.delete_alumno')
def eliminar_alumno(request, alumno_id):
    if request.method == 'POST':
        try:
            alumno = Alumno.objects.get(pk=alumno_id)
            print('Alumno encontrado:', alumno.nombre)
            alumno.delete()
            print('Alumno eliminado correctamente.')
            return redirect('tienda:lista_alumnos')
        except Alumno.DoesNotExist:
            print('No se encontró el alumno con ID:', alumno_id)
            return JsonResponse({'error': 'Alumno no encontrado.'}, status=404)
        except Exception as e:
            print('Ocurrió un error al eliminar el alumno:', str(e))
            return JsonResponse({'error': 'Error al eliminar el alumno.'}, status=500)
    else:
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    
    
    

import logging

logger = logging.getLogger(__name__)



def ver_turnos(request):
    # Obtener turnos disponibles y ocupados desde la base de datos
    turnos_disponibles = Turno.objects.filter(disponible=True)
    turnos_ocupados = Turno.objects.filter(disponible=False)

    # Formatear los datos en el formato requerido por FullCalendar
    eventos_disponibles = []
    eventos_ocupados = []

    for turno_disponible in turnos_disponibles:
        evento_disponible = {
            'title': 'Disponible',
            'start': f"{turno_disponible.fecha}T{turno_disponible.hora}",  # Formato ISO: YYYY-MM-DDTHH:MM:SS
            'color': 'green'
        }
        eventos_disponibles.append(evento_disponible)

    for turno_ocupado in turnos_ocupados:
        evento_ocupado = {
            'title': 'Ocupado',
            'start': f"{turno_ocupado.fecha}T{turno_ocupado.hora}",
            'color': 'red'
        }
        eventos_ocupados.append(evento_ocupado)

    # Imprimir los eventos disponibles y ocupados
    for evento in eventos_disponibles:
        logger.info(evento)

    for evento in eventos_ocupados:
        logger.info(evento)
    
    return render(request, 'tienda/ver_turnos.html', {'turnos_disponibles': turnos_disponibles, 'turnos_ocupados': turnos_ocupados})
'''