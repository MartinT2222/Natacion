import json
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.query_utils import Q
from django.http import JsonResponse, HttpResponseServerError
from USUARIOS.models import CustomUser
from USUARIOS.forms import RegistroForm
from .forms import ClaseNatacionForm  # Importa el formulario de clase de natación
from .models import ClaseNatacion, InscripcionClase
from datetime import datetime, timedelta
from django.contrib import messages
from django.utils import timezone, translation
from django.views.decorators.http import require_POST
from calendar import monthrange
from django.db import IntegrityError
from django.db.models import F
from django.utils.translation import gettext as _


def home(request):
    translation.activate('es')
    clases = ClaseNatacion.objects.all()
    clases_unicas = {}
    for clase in clases:
        nombre = clase.nombre
        dias = [_(clase.fecha.strftime('%A'))]
        hora_inicio = clase.hora_inicio.strftime('%H:%M')
        hora_fin = clase.hora_fin.strftime('%H:%M')
        precio = clase.precio  # Precio por 1 clase
        cupos_disponibles_pagos = 0

        
        imagen = ClaseNatacion.objects.filter(nombre=nombre).first().imagen

        if nombre not in clases_unicas:
            clases_unicas[nombre] = {
                'nombre': nombre,
                'dias': dias,
                'hora_inicio': hora_inicio,
                'hora_fin': hora_fin,
                'precio': precio,
                'precio_por_2_clases': precio * 2,  # Agrega los precios al diccionario
                'precio_por_3_clases': precio * 3,
                'precio_por_4_clases': (precio * 4),
                'precio_por_5_clases': precio * 5,
                'precio_por_6_clases': precio * 6,
                'imagen': imagen,
                'cupos': cupos_disponibles_pagos
            }
        else:
            if dias[0] not in clases_unicas[nombre]['dias']:
                clases_unicas[nombre]['dias'].append(dias[0])
    
    context = {
        'clases': clases_unicas.values(),
    }
    # Renderiza la plantilla y envía el contexto
    return render(request, 'tienda/index.html',context)



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
@permission_required('TIENDA.agregar_clase')
def agregar_clase_natacion(request):
    if request.method == 'POST':
        clase_form = ClaseNatacionForm(request.POST, request.FILES)
        if clase_form.is_valid():
            hora_inicio = clase_form.cleaned_data['hora_inicio']
            hora_fin = clase_form.cleaned_data['hora_fin']
            dias_semana = request.POST.getlist('dias_semana')

            nueva_clase = clase_form.save(commit=False)

            horarios_recurrentes = generar_horarios_recurrentes(dias_semana, hora_inicio, hora_fin)

            for fecha in horarios_recurrentes:
                try:
                    nueva_instancia = ClaseNatacion.objects.create(
                        nombre=nueva_clase.nombre,
                        fecha=fecha,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        cupos_disponibles=nueva_clase.cupos_disponibles,
                        precio=nueva_clase.precio,
                        imagen=nueva_clase.imagen  # Asigna la imagen a cada instancia
                    )
                    nueva_instancia.save()
                except IntegrityError as e:
                    print(f"Error de integridad al guardar para la fecha {fecha}: {e}")
                    # Manejo específico para la excepción de integridad, puedes agregar aquí lo que consideres necesario

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
    fecha_actual = datetime.now()
    primer_dia_mes_actual = fecha_actual
    ultimo_dia_mes_actual = fecha_actual.replace(day=monthrange(fecha_actual.year, fecha_actual.month)[1])
    
    # Si estamos en la última semana del mes actual o la fecha actual es el día 25
    if fecha_actual.day == 25 or fecha_actual + timedelta(7) > ultimo_dia_mes_actual:
        # Obtenemos los eventos del mes siguiente hasta completar 35 días
        primer_dia_mes_siguiente = ultimo_dia_mes_actual + timedelta(days=1)
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente.replace(day=monthrange(primer_dia_mes_siguiente.year, primer_dia_mes_siguiente.month)[1])
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente + timedelta(days=34)
        
        eventos_mes_actual = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual])
        eventos_mes_siguiente = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_siguiente, ultimo_dia_mes_siguiente])
        
        # Combinamos los eventos del mes actual y del mes siguiente
        eventos = list(eventos_mes_actual) + list(eventos_mes_siguiente)
    else:
        # Si no estamos en la última semana o no es el día 25, obtenemos solo los eventos del mes actual
        eventos = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual])

    eventos_json = [{
        'id': evento.id,
        'title': evento.nombre,
        'start': evento.fecha.strftime('%Y-%m-%d') + 'T' + evento.hora_inicio.strftime('%H:%M:%S'),
        'end': evento.fecha.strftime('%Y-%m-%d') + 'T' + evento.hora_fin.strftime('%H:%M:%S'),
    } for evento in eventos]

    return JsonResponse(eventos_json, safe=False)



@require_POST
@login_required
def capturar_id(request):
    try:
        data = json.loads(request.body)
        horarios_seleccionados = data.get('horariosSeleccionados', [])

        # Lista para almacenar mensajes de respuesta
        messages = []

        for horario_id in horarios_seleccionados:
            try:
                clase_natacion = ClaseNatacion.objects.get(pk=horario_id)
            except ClaseNatacion.DoesNotExist:
                return JsonResponse({'error': f'El horario con ID {horario_id} no existe'}, status=400)

            # Verifica y reduce los cupos disponibles
            if clase_natacion.cupos_disponibles > 0:
                InscripcionClase.objects.create(usuario=request.user, clase_natacion=clase_natacion)
                clase_natacion.cupos_disponibles -= 1
                clase_natacion.save()  # Guarda la instancia actualizada
                messages.append(f'Turno agendado para el horario con ID {horario_id}')
            else:
                messages.append(f'No se pudo agendar para el horario con ID {horario_id}: no hay cupos disponibles')

        # Componer la respuesta basada en los mensajes recopilados
        response_data = {
            'messages': messages,
            'success': all('No se pudo agendar' not in msg for msg in messages)
        }
        return JsonResponse(response_data)

    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)



@login_required
def ver_turnos(request):
    fecha_actual = datetime.now()
    
    if request.user.is_superuser:
        # Si el usuario es superusuario, muestra todos los turnos
        turnos = InscripcionClase.objects.filter(clase_natacion__fecha__gte=fecha_actual)
    else:
        # Si no es superusuario, muestra los turnos del usuario actual
        turnos = InscripcionClase.objects.filter(usuario=request.user, clase_natacion__fecha__gte=fecha_actual)
        
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
    
from django.utils.translation import gettext as _


def calcular_precio(nombre_clase, numero_clases):
    # Define un diccionario que mapea los nombres de las clases a sus precios respectivos
    precios_clases = {
        'Clase A': [1250, 5500, 6000, 6500, 7000, 7500],
        'Clase B': [1300, 5600, 6100, 6600, 7100, 7600],
        # Agrega más clases y sus precios respectivos aquí
    }

    # Verifica si el nombre de la clase está en el diccionario de precios
    if nombre_clase in precios_clases:
        # Obtiene la lista de precios para la clase específica
        precios = precios_clases[nombre_clase]

        # Verifica si el número de clases es válido para obtener el precio correspondiente
        if 1 <= numero_clases <= len(precios):
            return precios[numero_clases - 1]  # El índice de lista comienza en 0, por eso se resta 1

    # Retorna -1 o algún valor por defecto si el nombre de la clase no está en el diccionario
    return -1

