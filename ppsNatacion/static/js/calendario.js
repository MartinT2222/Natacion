
var horariosSeleccionados = new Set(); // Usar un Set para almacenar los IDs únicos de los horarios seleccionados

document.addEventListener('DOMContentLoaded', function() {
    
    var calendarEl = document.getElementById('calendario');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        selectable: false, // Cambiar a false para habilitar la selección de eventos individuales
        events: {
            url: getHorariosClaseURL,
            method: 'GET'
        },eventClick: function(info) {
            // Verificar si el evento ya está seleccionado
            console.log('Evento select activado');
            if (horariosSeleccionados.has(info.event.id)) {
                // Si ya está seleccionado, deseleccionarlo
                console.log('Evento select activado');
                horariosSeleccionados.delete(info.event.id);
                info.jsEvent.target.style.backgroundColor = ''; // Restaurar el color original del evento
            } else {
                // Si no está seleccionado, agregarlo a la lista de horarios seleccionados
                horariosSeleccionados.add(info.event.id);
                info.jsEvent.target.style.backgroundColor = 'gray'; // Cambiar el color del evento seleccionado
            }
            console.log('IDs de los eventos seleccionados:', Array.from(horariosSeleccionados));
        }
    });
    calendar.render();
});

function enviarHorariosSeleccionados() {
    console.log('Valores de horariosSeleccionados:', Array.from(horariosSeleccionados));
    document.getElementById('horariosSeleccionados').value = JSON.stringify(horariosSeleccionados);
    console.log('Valor del campo horariosSeleccionados:', document.getElementById('horariosSeleccionados').value);
    console.log('Enviando formulario');
    document.getElementById('claseForm').submit();
    var horariosSeleccionados = Array.from(horariosSeleccionados); // Convierte el Set a un array para recorrerlo

    var usuarioId = "{{ request.user.id }}"; // Obteniendo el ID del usuario autenticado

    horariosSeleccionados.forEach(function(eventId) {
        var nombreClase = obtenerNombreClase(eventId); // Lógica para obtener el nombre de la clase desde el ID
        var horarioClase = obtenerHorarioClase(eventId); // Lógica para obtener el horario de la clase desde el ID

        // Aquí debes enviar una petición POST al backend con los datos requeridos por la vista
        fetch('/asociar_usuario_clases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usuario: usuarioId,
                nombreClase: nombreClase,
                horarioClase: horarioClase,
                // Otros datos que puedas necesitar para la inscripción
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Inscripción guardada:', data);
        })
        .catch((error) => {
            console.error('Error al guardar la inscripción:', error);
        });
    });

    horariosSeleccionados.clear(); // Limpiar los eventos seleccionados después de guardar las inscripciones
    console.log('Eventos seleccionados limpiados:', Array.from(horariosSeleccionados));
}

