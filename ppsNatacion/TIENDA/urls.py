from django.urls import path
from . import views

app_name = 'tienda'

urlpatterns = [
    path('', views.home, name = 'home'),
#    path('clases/', views.lista_clases_natacion, name='lista_clases_natacion'),
#    path('clases/<int:clase_id>/', views.detalle_clase_natacion, name='detalle_clase_natacion'),
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('buscar/', views.buscar, name = 'buscar'),
#    path('alumnos/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('asociar_usuario_clases/', views.asociar_usuario_clases, name='asociar_usuario_clases'),
    path('clase/agregar/', views.agregar_clase_natacion, name='agregar_clase'),  # Ruta para agregar clase
    path('get_horarios_clase/', views.get_horarios_clase, name='get_horarios_clase'),
    path('capturar_id/', views.capturar_id, name='capturar_id'),
#    path('alumnos/editar/<int:alumno_id>/', views.editar_alumno, name='edit_alumno'),
    path('cancelar_turno/<int:turno_id>/', views.cancelar_turno, name='cancelar_turno'),
    path('ver-turnos/', views.ver_turnos, name='ver_turnos'),
    path('pago_producto/', views.pago_producto, name='pago_producto'),
    path('ver_mas_usuario/<int:usuario_id>/', views.ver_mas_usuario, name='ver_mas_usuario'),
    path('realizar_pago/', views.realizar_pago, name='realizar_pago'),
    path('agregar_alumno/', views.AgregarAlumno, name='agregar_alumno'),
    path('agregar_compra/<int:usuario_id>/', views.agregar_compra, name='agregar_compra'),
    path('inscribir_alumno/<int:usuario_id>/', views.Inscripcion_alumno, name='Inscripcion_alumno'),
]
