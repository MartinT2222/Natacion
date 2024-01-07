import json
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.query_utils import Q
from django.http import JsonResponse
from USUARIOS.models import CustomUser
from USUARIOS.forms import RegistroForm
from .forms import ClaseNatacionForm  # Importa el formulario de clase de natación
from .models import ClaseNatacion, InscripcionClase
from datetime import datetime, timedelta
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseServerError
from django.shortcuts import HttpResponse
from django.views.decorators.http import require_POST



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

@login_required
def agregar_clase_natacion(request):
    if request.method == 'POST':
        clase_form = ClaseNatacionForm(request.POST)
        if clase_form.is_valid():
            nueva_clase = clase_form.save(commit=False)  # Evitar guardar la instancia por ahora

            hora_inicio = nueva_clase.hora_inicio
            hora_fin = nueva_clase.hora_fin
            dias_semana = request.POST.getlist('dias_semana')  # Obtener los días seleccionados desde el formulario

            # Obtener horarios recurrentes para la nueva clase
            horarios_recurrentes = generar_horarios_recurrentes(dias_semana, hora_inicio, hora_fin)

            for fecha in horarios_recurrentes:
                # Crear una nueva instancia de ClaseNatacion para cada fecha
                nueva_clase.pk = None  # Asignar None al ID para crear una nueva instancia
                nueva_clase.fecha = fecha  # Asignar la fecha generada
                nueva_clase.save()  # Guardar la instancia de ClaseNatacion

            # Redireccionar o mostrar mensajes de éxito después de guardar todas las instancias
            messages.success(request, 'Las clases se han guardado exitosamente!')
            return redirect('tienda:agregar_clase')

    else:
        clase_form = ClaseNatacionForm()

    return render(request, 'tienda/agregar_clase.html', {'clase_form': clase_form})

@login_required
def asociar_usuario_clases(request):
    if request.method == 'POST':
        try:
            usuario = request.user  # Acceder al usuario autenticado
            clase_id = request.POST.get('clase_id')  # Obtener el ID de la clase seleccionada

            # Obtener la clase usando el ID obtenido
            clase = get_object_or_404(ClaseNatacion, pk=clase_id)

            # Crear la inscripción para el usuario y la clase seleccionada
            InscripcionClase.objects.create(usuario=usuario, clase_natacion=clase, fecha_inscripcion=timezone.now())

            # Lógica adicional como redirección o mensajes de éxito
            # ...

        except Exception as e:
            # Captura cualquier excepción y muestra información útil para depuración
            print(f"Error: {e}")
            return HttpResponseServerError('Internal Server Error')

    clases = ClaseNatacion.objects.all()
    #print(f"asociar_usuario_clases: {clases}")
    #print(f"Me trae todos los ClaseNatacion object (1)> al entrar en la vista Asiciar usuarios a clases: ")
    
    return render(request, 'tienda/asociar_usuario_clases.html', {'clases': clases})  # Reemplaza 'ruta_de_tu_template.html' con el nombre correcto de tu template

 
def get_horarios_clase(request):
    # Obtener horarios de clases y convertirlos a formato de eventos
    fecha_actual = timezone.now()
    clases = ClaseNatacion.objects.filter(fecha__gte=fecha_actual)
    eventos = []

    for clase in clases:
        evento = {
            'id': clase.id,  # Debes asegurarte de tener un identificador único para cada evento
            'title': clase.nombre,
            'start': clase.fecha.strftime('%Y-%m-%d') + 'T' + clase.hora_inicio.strftime('%H:%M:%S'),
            'end': clase.fecha.strftime('%Y-%m-%d') + 'T' + clase.hora_fin.strftime('%H:%M:%S'),
            # Otros campos que puedas necesitar para el evento
        }
        eventos.append(evento)
    #print(f"get_horarios_clase TODOS ARRAY CON ID, NOMBRE DE LA CLASE,FECHA HORA DE INICIO,FECHA HORA DE FIN DE LA CLASE: {eventos}")
    #print(f"get_horarios_clase TODOS ARRAY CON ID, NOMBRE DE LA CLASE,FECHA HORA DE INICIO,FECHA HORA DE FIN DE LA CLASE: ")    
    return JsonResponse(eventos, safe=False)






@require_POST
@login_required
def capturar_id(request):
    try:
        data = json.loads(request.body)
        horarios_seleccionados = data.get('horariosSeleccionados', [])

        # Procesamiento de los horarios seleccionados
        for horario_id in horarios_seleccionados:
            # Verifica si el ID es válido y está presente en la ClaseNatacion
            try:
                clase_natacion = ClaseNatacion.objects.get(pk=horario_id)
            except ClaseNatacion.DoesNotExist:
                return JsonResponse({'error': f'El horario con ID {horario_id} no existe'}, status=400)

            # Verifica y reduce los cupos disponibles
            if clase_natacion.cupos_disponibles > 0:
                InscripcionClase.objects.create(usuario=request.user, clase_natacion=clase_natacion)
                clase_natacion.cupos_disponibles -= 1
                clase_natacion.save()  # Guarda la instancia actualizada

        # Respuesta exitosa
        return JsonResponse({'message': 'Proceso completado'})

    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)




@login_required
def ver_turnos(request):
    if request.user.is_superuser:
        # Si el usuario es superusuario, muestra todos los turnos
        turnos = InscripcionClase.objects.all()
    else:
        # Si no es superusuario, muestra los turnos del usuario actual
        turnos = InscripcionClase.objects.filter(usuario=request.user)

    return render(request, 'tienda/ver_turnos.html', {'turnos': turnos})


@require_POST
@login_required
def cancelar_turno(request, turno_id):
    turno = get_object_or_404(InscripcionClase, pk=turno_id, usuario=request.user)

    try:
        clase_natacion = turno.clase_natacion
        clase_natacion.cupos_disponibles += 1
        clase_natacion.save()

        turno.delete()
        return JsonResponse({'message': 'Turno cancelado exitosamente'})
    except Exception as e:
        return JsonResponse({'error': 'Error al cancelar el turno'}, status=500)