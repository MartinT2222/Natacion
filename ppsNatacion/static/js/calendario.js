
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendario');
    var horariosSeleccionados = new Set();

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        selectable: false,
        events: {
            url: getHorariosClaseURL, // Variable definida en la plantilla Django
            method: 'GET'
        },
        eventClick: function(info) {
            console.log('Evento select activado');
            if (horariosSeleccionados.has(info.event.id)) {
                console.log('Evento select activado');
                horariosSeleccionados.delete(info.event.id);
                info.jsEvent.target.style.backgroundColor = '';
            } else {
                horariosSeleccionados.add(info.event.id);
                info.jsEvent.target.style.backgroundColor = 'gray';
            }
            //console.log('IDs de los eventos seleccionados:', Array.from(horariosSeleccionados));
        }
    });

    calendar.render();

    function enviarHorariosSeleccionados() {
        var horarios = Array.from(horariosSeleccionados);
        
        var csrftoken = getCookie('csrftoken'); // Función para obtener el valor de la cookie del token CSRF
        // Verificar si horarios es None o vacío
        if (!horarios || horarios.length === 0) {
            console.error('No hay datos para enviar');
            return;
        }
        // Obtener la URL a la que se enviará la solicitud POST
        
        fetch('/capturar_id/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                horariosSeleccionados: Array.from(horariosSeleccionados)
                
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            console.log('Respuesta desde Django:', data);
        })
        .catch(error => {
            console.error('Error en la solicitud:', error);
        });
        


        console.log('IDs de los eventos seleccionados:', horariosSeleccionados);
        horariosSeleccionados.clear();
    }
    
    document.getElementById('enviarHorariosBtn').addEventListener('click', enviarHorariosSeleccionados);
});


