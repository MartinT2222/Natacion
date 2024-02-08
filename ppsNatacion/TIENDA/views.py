import json
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.query_utils import Q
from django.http import JsonResponse, HttpResponseServerError
from django.urls import reverse
from USUARIOS.models import CustomUser
from USUARIOS.forms import RegistroForm
from .forms import ClaseNatacionForm, CompraForm, InscripcionForm  # Importa el formulario de clase de natación
from .models import ClaseNatacion, InscripcionClase, ComprasClase
from datetime import datetime, timedelta
from django.contrib import messages
from django.utils import timezone, translation
from django.views.decorators.http import require_POST
from calendar import monthrange
from django.db import IntegrityError
from django.db.models import F
from django.utils.translation import gettext as _
from django.db import transaction
from decimal import Decimal, InvalidOperation






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
                'precio_por_2_clases': precio * 2,
                'precio_por_3_clases': precio * 3,
                'precio_por_4_clases': precio * 4,
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
    return render(request, 'tienda/index.html', context)


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
            usuario_id = request.POST.get('alumno_id')
            usuario_eliminar = CustomUser.objects.get(pk=usuario_id)
            usuario_eliminar.delete()
            return redirect('tienda:lista_alumnos')
    else:
        form = RegistroForm()

    for usuario in usuarios:
        usuario.compras = ComprasClase.objects.filter(usuario=usuario)
        #usuario.incripciones = InscripcionClase.objects.filter(usuario=usuario)

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
    # Obtener las clases compradas por el usuario autenticado
    clases_compradas = ComprasClase.objects.filter(usuario=request.user).values_list('clase_comprada', flat=True)

    clases = ClaseNatacion.objects.filter(nombre__in=clases_compradas)


    #print(f"asociar_usuario_clases: {clases}")
    #print(f"Me trae todos los ClaseNatacion object (1)> al entrar en la vista Asiciar usuarios a clases: ")
    
    return render(request, 'tienda/asociar_usuario_clases.html', {'clases': clases})  # Reemplaza 'ruta_de_tu_template.html' con el nombre correcto de tu template

 



def get_horarios_clase(request):
    
    fecha_actual = datetime.now()
    primer_dia_mes_actual = fecha_actual
    ultimo_dia_mes_actual = fecha_actual.replace(day=monthrange(fecha_actual.year, fecha_actual.month)[1])
    
    clases_compradas = ComprasClase.objects.filter(usuario=request.user).values_list('clase_comprada', flat=True)
    clases = ClaseNatacion.objects.filter(nombre__in=clases_compradas)

    # Si estamos en la última semana del mes actual o la fecha actual es el día 25
    if fecha_actual.day == 25 or fecha_actual + timedelta(7) > ultimo_dia_mes_actual:
        # Obtenemos los eventos del mes siguiente hasta completar 35 días
        primer_dia_mes_siguiente = ultimo_dia_mes_actual + timedelta(days=1)
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente.replace(day=monthrange(primer_dia_mes_siguiente.year, primer_dia_mes_siguiente.month)[1])
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente + timedelta(days=34)
        
        eventos_mes_actual = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual], nombre__in=clases_compradas, cupos_disponibles__gt=0)
        eventos_mes_siguiente = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_siguiente, ultimo_dia_mes_siguiente], nombre__in=clases_compradas, cupos_disponibles__gt=0)
        
        # Combinamos los eventos del mes actual y del mes siguiente
        eventos = list(eventos_mes_actual) + list(eventos_mes_siguiente)
    else:
        # Si no estamos en la última semana o no es el día 25, obtenemos solo los eventos del mes actual
        eventos = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual], nombre__in=clases_compradas, cupos_disponibles__gt=0)
    
    #print(f"eventos: {eventos}")
    
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

        with transaction.atomic():
            for horario_id in horarios_seleccionados:
                try:
                    clase_natacion = ClaseNatacion.objects.get(pk=horario_id)
                except ClaseNatacion.DoesNotExist:
                    return JsonResponse({'error': f'El horario con ID {horario_id} no existe'}, status=400)

                # Verifica si el usuario ya está inscrito en esta clase
                existe_inscripcion = InscripcionClase.objects.filter(usuario=request.user, clase_natacion=clase_natacion).exists()
                compra_clase = ComprasClase.objects.filter(usuario=request.user, clase_comprada=clase_natacion.nombre).first()
                if existe_inscripcion:
                    messages.append(f'Ya estás inscrito para el horario con ID {horario_id}')
                elif clase_natacion.cupos_disponibles > 0 and compra_clase and compra_clase.cupos_disponibles_pagos > 0:
                    # Buscar el registro existente en ComprasClase y actualizar cupos_disponibles_pagos
                    InscripcionClase.objects.create(usuario=request.user, clase_natacion=clase_natacion)
                    clase_natacion.cupos_disponibles -= 1
                    compra_clase.cupos_disponibles_pagos -= 1
                    compra_clase.save()
                    clase_natacion.save()
                    messages.append(f'Turno agendado para el horario con ID {horario_id}')
                else:
                    messages.append(f'No se pudo agendar para el horario con ID {horario_id}: no hay cupos disponibles')

        # Componer la respuesta basada en los mensajes recopilados
        response_data = {
            'messages': messages,
            'success': all('No se pudo agendar' not in msg for msg in messages),
            'success_message': 'Inscripción exitosa' if all('No se pudo agendar' not in msg for msg in messages) else ''
        }
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)


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
    try:
        with transaction.atomic():
            turno = get_object_or_404(InscripcionClase, pk=turno_id)
            print(f"Turno a cancelar: {turno.id} - Usuario: {turno.usuario.username}")

            clase_natacion = turno.clase_natacion
            clase_natacion.cupos_disponibles += 1
            clase_natacion.save()

            # Buscar el registro existente en ComprasClase y actualizar cupos_disponibles_pagos
            compra_clase = ComprasClase.objects.filter(
                usuario=turno.usuario,
                clase_comprada=turno.clase_natacion.nombre,  # Ajusta según la estructura de tu modelo
            ).first()

            if compra_clase:
                compra_clase.cupos_disponibles_pagos += 1
                compra_clase.save()
                
            #print(f"Clase de Natación: {clase_natacion}")

            #print(f"compra_clase: {compra_clase} - ")
            turno.delete()
            print("Turno cancelado exitosamente")

            return JsonResponse({'message': 'Turno cancelado exitosamente'})
    except Exception as e:
        print(f"Error al cancelar el turno: {e}")
        return JsonResponse({'error': 'Error al cancelar el turno'}, status=500)
    
    
    
    

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






def pago_producto(request):
    if request.method == 'GET':
        # Obtener parámetros de la URL
        clase_id = request.GET.get('claseId')
        precio_seleccionado = request.GET.get('precioSeleccionado')
        dias = request.GET.get('dias')
        hora_inicio = request.GET.get('horaInicio')
        hora_fin = request.GET.get('horaFin')
        cupos_disponibles = request.GET.get('cupos')

        return render(request, 'tienda/pago_producto.html', {
            'clase_id': clase_id,
            'precio_seleccionado': precio_seleccionado,
            'dias': dias,
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'cupos_disponibles': cupos_disponibles,
        })
    else:
        # Manejar otras solicitudes según sea necesario
        return redirect('tienda:home')  # Redirigir a la página principal, por ejemplo




from django.http import JsonResponse

def realizar_pago(request):
    messages = []

    if request.method == 'POST':
        # Lógica de verificación del pago
        # ...

        pago_aprobado = True  # Coloca aquí tu lógica para determinar si el pago fue aprobado

        if pago_aprobado:
            # Obtener los datos JSON de la solicitud
            data = json.loads(request.body.decode('utf-8'))

            # Crear instancia de ComprasClase
            usuario = request.user  # Obtener el usuario actual
            clase_id = data.get('clase_id')
            precio_seleccionado = data.get('precio_seleccionado')
            cupos_disponibles = data.get('cupos_disponibles')
            # Reemplazar la coma con un punto en el precio seleccionado
            precio_seleccionado = precio_seleccionado.replace(',', '.')

            try:
                precio_seleccionado_decimal = Decimal(str(precio_seleccionado))
            except InvalidOperation as e:
                print(f"Error al convertir precio_seleccionado a Decimal: {e}")
                precio_seleccionado_decimal = Decimal('0.00')

            print(f"usuario: {usuario}")
            print(f"clase_id: {clase_id}")
            print(f"precio_seleccionado: {precio_seleccionado}")
            print(f"cupos_disponibles: {cupos_disponibles}")

            compra_existente = ComprasClase.objects.filter(
                usuario=usuario,
                clase_comprada=clase_id
            ).first()

            if compra_existente:
                # Si existe, actualizar la compra existente
                compra_existente.precio_clase += precio_seleccionado_decimal
                compra_existente.cupos_disponibles_pagos += int(cupos_disponibles)
                compra_existente.save()
            else:
                # Si no existe, crear una nueva compra
                compra_clase = ComprasClase.objects.create(
                    usuario=usuario,
                    clase_comprada=clase_id,
                    precio_clase=precio_seleccionado_decimal,
                    cupos_disponibles_pagos=int(cupos_disponibles),
                    fecha_compra=timezone.now()
                )
                compra_clase.save()

            messages.append('Pago aprobado. Compras registradas correctamente.')
        else:
            messages.append('Pago desaprobado. No se realizaron compras.')

    # Si el método no es POST, puedes manejarlo según tus necesidades
    return JsonResponse({'messages': messages})




def ver_mas_usuario(request, usuario_id):
    usuario = get_object_or_404(CustomUser, pk=usuario_id)
    compras = ComprasClase.objects.filter(usuario=usuario)
    inscripciones = InscripcionClase.objects.filter(usuario=usuario)
    return render(request, 'tienda/ver_mas_usuario.html', {'usuario': usuario, 'compras': compras, 'inscripciones': inscripciones})



def AgregarAlumno(request):
    template_name = 'tienda/agregar_alumno.html'
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario agregado correctamente')
            return redirect('tienda:lista_alumnos')
        else:
            messages.error(request, 'Error en el formulario. Por favor, verifica los datos.')
    else:
        form = RegistroForm()
    return render(request, template_name, {'form': form})

def agregar_compra(request, usuario_id):
    usuario = get_object_or_404(CustomUser, pk=usuario_id)
    compras = ComprasClase.objects.filter(usuario=usuario)

    if request.method == 'POST':
        form = CompraForm(request.POST)
        
        if form.is_valid():
            nombre_clase = form.cleaned_data['clase_comprada']
            
            # Verificar si hay una compra existente con el mismo nombre
            compra_existente = ComprasClase.objects.filter(
                usuario=usuario,
                clase_comprada=nombre_clase  # Usar la variable nombre_clase aquí
            ).first()

            if compra_existente:
                # Si existe, actualizar la compra existente
                compra_existente.precio_clase = form.cleaned_data['precio_clase']
                compra_existente.cupos_disponibles_pagos += form.cleaned_data['cupos_disponibles_pagos']
                compra_existente.fecha_compra = timezone.now()
                compra_existente.save()
            else:
                # Si no existe, crear una nueva compra
                compra = form.save(commit=False)
                compra.usuario = usuario
                compra.save()

            return redirect('tienda:ver_mas_usuario', usuario_id=usuario_id)
    else:
        form = CompraForm(request.POST or None)

    return render(request, 'tienda/agregar_compra.html', {'form': form, 'usuario': usuario, 'compras': compras})



from django.db.models import Q

def Inscripcion_alumno(request, usuario_id):
    print("Entrando en la vista Inscripcion_alumno")  # Agrega este mensaje de depuración
    usuario = get_object_or_404(CustomUser, pk=usuario_id)
    print(f"usuario: {usuario}")
    
    if request.method == 'POST':
        try:
            usuario = get_object_or_404(CustomUser, pk=usuario_id)
            print(f"usuario: {usuario}")
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
            
    # Obtener las clases compradas por el usuario autenticado
    clases_compradas = ComprasClase.objects.filter(usuario=get_object_or_404(CustomUser, pk=usuario_id)).values_list('clase_comprada', flat=True)
    print(f"clases_compradas: {clases_compradas}")
    
    clases = ClaseNatacion.objects.filter(nombre__in=clases_compradas)
    print(f"clases: {clases}")

    return render(request, 'tienda/inscripciones_alumno.html', {'usuario': usuario, 'getHorariosClaseURL': reverse('tienda:get_horarios', kwargs={'usuario_id': usuario_id})})


def get_horarios(request, usuario_id):
    print("Entrando en la vista get_horarios")
    # Obtener el usuario correspondiente al ID proporcionado
    usuario = get_object_or_404(CustomUser, pk=usuario_id)
    #print(f"usuario: {usuario}")
    fecha_actual = datetime.now()
    primer_dia_mes_actual = fecha_actual
    ultimo_dia_mes_actual = fecha_actual.replace(day=monthrange(fecha_actual.year, fecha_actual.month)[1])
    
    # Obtener las clases compradas por el usuario
    clases_compradas = ComprasClase.objects.filter(usuario=usuario).values_list('clase_comprada', flat=True)
    clases = ClaseNatacion.objects.filter(nombre__in=clases_compradas)
    #print(f"usuario: {clases}")
    # Si estamos en la última semana del mes actual o la fecha actual es el día 25
    if fecha_actual.day == 25 or fecha_actual + timedelta(7) > ultimo_dia_mes_actual:
        # Obtenemos los eventos del mes siguiente hasta completar 35 días
        primer_dia_mes_siguiente = ultimo_dia_mes_actual + timedelta(days=1)
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente.replace(day=monthrange(primer_dia_mes_siguiente.year, primer_dia_mes_siguiente.month)[1])
        ultimo_dia_mes_siguiente = primer_dia_mes_siguiente + timedelta(days=34)
        
        eventos_mes_actual = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual], nombre__in=clases_compradas, cupos_disponibles__gt=0)
        eventos_mes_siguiente = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_siguiente, ultimo_dia_mes_siguiente], nombre__in=clases_compradas, cupos_disponibles__gt=0)
        
        # Combinamos los eventos del mes actual y del mes siguiente
        eventos = list(eventos_mes_actual) + list(eventos_mes_siguiente)
    else:
        # Si no estamos en la última semana o no es el día 25, obtenemos solo los eventos del mes actual
        eventos = ClaseNatacion.objects.filter(fecha__range=[primer_dia_mes_actual, ultimo_dia_mes_actual], nombre__in=clases_compradas, cupos_disponibles__gt=0)
    
    # Convertimos los eventos en formato JSON
    eventos_json = [{
        'id': evento.id,
        'title': evento.nombre,
        'start': evento.fecha.strftime('%Y-%m-%d') + 'T' + evento.hora_inicio.strftime('%H:%M:%S'),
        'end': evento.fecha.strftime('%Y-%m-%d') + 'T' + evento.hora_fin.strftime('%H:%M:%S'),
    } for evento in eventos]

    return JsonResponse(eventos_json, safe=False)





@require_POST
@login_required
def capturar_id_Admin(request, usuario_id):
    print("Entrando en la vista capturar_id_Admin")
    usuario = get_object_or_404(CustomUser, pk=usuario_id)
    print(f"usuario: {usuario}")
    try:
        data = json.loads(request.body)
        horarios_seleccionados = data.get('horariosSeleccionados', [])

        # Lista para almacenar mensajes de respuesta
        messages = []

        with transaction.atomic():
            # Obtener el usuario correspondiente al usuario_id de la URL
            usuario = get_object_or_404(CustomUser, pk=usuario_id)
            print(f"usuario_id de la URL: {usuario}")
            for horario_id in horarios_seleccionados:
                try:
                    clase_natacion = ClaseNatacion.objects.get(pk=horario_id)
                except ClaseNatacion.DoesNotExist:
                    return JsonResponse({'error': f'El horario con ID {horario_id} no existe'}, status=400)

                # Verifica si el usuario ya está inscrito en esta clase
                existe_inscripcion = InscripcionClase.objects.filter(usuario=usuario, clase_natacion=clase_natacion).exists()

                # Buscar el registro existente en ComprasClase y actualizar cupos_disponibles_pagos
                compra_clase = ComprasClase.objects.filter(usuario=usuario, clase_comprada=clase_natacion.nombre).first()

                if existe_inscripcion:
                    messages.append(f'El usuario ya está inscrito para el horario con ID {horario_id}')
                elif clase_natacion.cupos_disponibles > 0 and compra_clase and compra_clase.cupos_disponibles_pagos > 0:
                    # Si no está inscrito y hay cupos disponibles, proceder con la inscripción
                    InscripcionClase.objects.create(usuario=usuario, clase_natacion=clase_natacion)
                    clase_natacion.cupos_disponibles -= 1
                    compra_clase.cupos_disponibles_pagos -= 1
                    compra_clase.save()
                    clase_natacion.save()
                    messages.append(f'Turno agendado para el horario con ID {horario_id}')
                else:
                    messages.append(f'No se pudo agendar para el horario con ID {horario_id}: no hay cupos disponibles')

        # Componer la respuesta basada en los mensajes recopilados
        response_data = {
            'messages': messages,
            'success': all('No se pudo agendar' not in msg for msg in messages),
            'success_message': 'Inscripción exitosa' if all('No se pudo agendar' not in msg for msg in messages) else ''
        }
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)

    
    
    