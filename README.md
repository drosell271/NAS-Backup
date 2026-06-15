# NAS Backup

Aplicacion de escritorio para Windows que sincroniza carpetas locales hacia una carpeta de red o NAS mediante `robocopy`.

## Captura de pantalla

![Interfaz principal de NAS Backup](docs/Captura%20de%20pantalla.png)

## Instalar

Ejecuta:

```text
release\installer\NAS_Backup_Setup.exe
```

La instalacion se realiza para el usuario actual y no requiere permisos de administrador.

## Uso rapido

1. Pulsa **Nueva tarea**.
2. Selecciona la carpeta local y el destino de red.
3. Selecciona, si es necesario, la red requerida.
4. Guarda la tarea.
5. Usa **Prueba sin copiar** antes del primer backup.
6. Pulsa **Ejecutar ahora**.

La sincronizacion es unidireccional:

```text
Carpeta local -> NAS
```

## Funciones principales

- Ejecucion manual, por intervalo o en tiempo real al detectar cambios.
- Varias tareas en paralelo.
- Comprobacion de red, destino, permisos y espacio libre.
- Modo de prueba sin copiar archivos.
- Historial y logs por ejecucion.
- Bandeja del sistema y arranque con Windows.
- Importacion y exportacion de configuracion.
- Aviso de nuevas versiones publicadas en GitHub.

## Documentacion

- [Indice de documentacion](docs/README.md)
- [Guia de uso](docs/USO.md)
- [Instalacion y actualizacion](docs/INSTALACION.md)
- [Desarrollo y compilacion](docs/DESARROLLO.md)
- [Estructura del repositorio](docs/ESTRUCTURA.md)
- [Funcionamiento y solucion de problemas](docs/REFERENCIA.md)

## Requisitos

- Windows 10 u 11.
- Acceso de escritura a la carpeta de destino.
- `robocopy`, incluido en Windows.

Version del instalador: `1.1.0`.
