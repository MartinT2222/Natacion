# PPS
PASANTIAS UTN-FRSR
    clases_info_str = request.GET.get('clasesInfo')
    # Lista para almacenar mensajes de respuesta
    messages = []
    if clases_info_str:
        clases_info = json.loads(clases_info_str)
        usuario_actual = request.user

        # Verificar si el pago fue aprobado (puedes adaptar esto según tus necesidades)
        pago_aprobado = False    # Coloca aquí tu lógica para determinar si el pago fue aprobado
        if pago_aprobado:
            # Actualizar el valor de cupos_disponibles_pagos o crear una nueva compra
            for claseInfo in clases_info:
                clase_nombre = claseInfo['claseNombre']
                precio_clase = float(claseInfo['precio'].replace(',', '.'))
                cupos_disponibles = claseInfo['cuposDisponibles']
                
                # Verificar si ya existe una compra para esta clase
                compra_existente = ComprasClase.objects.filter(
                    usuario=usuario_actual,
                    clase_comprada=clase_nombre
                ).first()

                if compra_existente:
                    # Si existe, actualizar la compra existente
                    compra_existente.precio_clase += Decimal(str(precio_clase))
                    compra_existente.cupos_disponibles_pagos += cupos_disponibles
                    compra_existente.save()
                else:
                    # Si no existe, crear una nueva compra
                    compra_clase = ComprasClase.objects.create(
                        usuario=usuario_actual,
                        clase_comprada=clase_nombre,
                        precio_clase=precio_clase,
                        cupos_disponibles_pagos=cupos_disponibles,
                        fecha_compra=timezone.now()  # Asigna la fecha actual
                    )
                    compra_clase.save()

            messages.append('Pago aprobado. Compras registradas correctamente.')
        else:
            messages.append('Pago desaprobado. No se realizaron compras.')
            # Lógica para manejar un pago no aprobado
            
            # Por ejemplo, renderizar una página de error
            messages.append(f'pago desaprobado ')
    else:
        clases_info = []
    # Realiza cualquier lógica adicional relacionada con el pago si es necesario
    # Obtener el usuario actual
    context = {
        'clases_info': clases_info,
        'messages': messages,
    }
    return render(request, 'tienda/pago_producto.html', context)
