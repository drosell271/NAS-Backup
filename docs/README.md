# Documentacion

## Para usuarios

- [Guia de uso](USO.md): crear tareas, modos de ejecucion, botones y preferencias.
- [Instalacion y actualizacion](INSTALACION.md): instalar, actualizar, desinstalar y localizar los datos.
- [Referencia y problemas frecuentes](REFERENCIA.md): funcionamiento interno, seguridad y errores habituales.

## Para desarrollo

- [Desarrollo y compilacion](DESARROLLO.md): entorno Python, estructura del proyecto, ejecutable e instalador.
- [Estructura del repositorio](ESTRUCTURA.md): organizacion de carpetas y archivos ignorados por Git.

## Resumen

NAS Backup copia en una sola direccion:

```text
Origen local -> Destino NAS o carpeta de red
```

No realiza sincronizacion bidireccional. Los archivos del destino solo se eliminan cuando se activa expresamente el modo espejo.
