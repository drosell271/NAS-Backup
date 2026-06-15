# Guia de uso

## Crear una tarea

Pulsa **Nueva tarea** y completa:

- **Nombre**: identificador visible de la tarea.
- **Carpeta origen**: carpeta local que se quiere copiar.
- **Carpeta destino**: ruta local, unidad de red o ruta UNC del NAS.
- **Red requerida**: red WiFi, perfil de red o conexion cableada necesaria.
- **Modo**: define cuando se ejecuta la tarea.
- **Exclusiones**: un patron por linea.

La lista de redes se obtiene con **Escanear**. Selecciona **Cualquier red** si la tarea no depende de una red concreta.

## Modos de ejecucion

- **Solo manual**: se ejecuta con **Ejecutar ahora**.
- **Cada X minutos**: se ejecuta automaticamente segun el intervalo.
- **Cuando haya cambios**: observa la carpeta origen en tiempo real y ejecuta la copia automaticamente tras una espera corta.
- **Ambas**: combina intervalo y deteccion de cambios.

## Opciones de seguridad

### Prueba sin copiar

Ejecuta `robocopy /L`. Genera log e historial, pero no copia ni elimina archivos.

Se puede usar de dos formas:

- Boton **Prueba sin copiar** para una ejecucion puntual.
- Opcion persistente **Modo prueba** dentro de la tarea.

### Borrado espejo

La opcion **Borrar en destino lo borrado en origen** activa `robocopy /MIR`.

Esta opcion puede eliminar archivos del NAS. La aplicacion:

- No la activa por defecto.
- Solicita confirmacion.
- Bloquea destinos demasiado generales.

Haz primero una prueba sin copiar y revisa el log.

## Botones principales

- **Nueva tarea**: crea una tarea.
- **Editar**: modifica la tarea seleccionada.
- **Eliminar**: borra la configuracion de la tarea.
- **Ejecutar ahora**: inicia la copia.
- **Prueba sin copiar**: simula la copia.
- **Cancelar**: detiene la ejecucion seleccionada.
- **Pausar / Reanudar**: controla la automatizacion de la tarea.
- **Ultimo log**: abre el ultimo archivo de log.
- **Historial**: muestra las ejecuciones registradas.
- **Salir**: cierra completamente la aplicacion.

Cerrar la ventana con la X solo la oculta. La aplicacion sigue activa en la bandeja.

## Estados

- **Lista**: preparada para ejecutarse.
- **Programada**: esperando turno.
- **En ejecucion**: copia activa.
- **Esperando red**: falta la red, el destino o los permisos.
- **Correcta**: ultima ejecucion completada.
- **Advertencia**: `robocopy` encontro diferencias o archivos extra.
- **Error**: la ejecucion fallo.
- **Pausada**: no se ejecutara automaticamente.
- **Desactivada**: tarea deshabilitada.

## Preferencias

En **Herramientas > Preferencias** se configura:

- Inicio con Windows.
- Inicio minimizado.
- Numero maximo de tareas paralelas.
- Notificaciones.
- Espera tras detectar cambios.
- Retencion de logs.
- Comprobacion automatica de actualizaciones.

La comprobacion se realiza al iniciar la aplicacion y, mientras permanece abierta,
como maximo una vez al dia. Tambien puede ejecutarse manualmente desde
**Herramientas > Buscar actualizaciones**.

## Exportar e importar

Usa el menu **Archivo** para exportar o importar tareas y preferencias en JSON.

Los logs y el historial no se incluyen en la exportacion.

## Copia al detectar cambios

Para activarla:

1. Edita la tarea.
2. Selecciona **Cuando haya cambios** o **Ambas**.
3. Guarda la tarea.

La aplicacion observa de forma recursiva la carpeta origen. Al crear, modificar, mover o eliminar un archivo, reinicia un contador corto y ejecuta la tarea cuando dejan de llegar cambios.

La espera predeterminada es de 60 segundos y se modifica en **Herramientas > Preferencias**. Esto evita iniciar una copia distinta por cada archivo cuando un programa guarda varios elementos a la vez.

Si se detectan cambios durante una copia, se programa otra ejecucion al terminar. Si el NAS no esta disponible, la tarea se reintenta automaticamente.
