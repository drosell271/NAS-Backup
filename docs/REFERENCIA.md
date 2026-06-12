# Funcionamiento y solucion de problemas

## Flujo de una ejecucion

Antes de copiar, la aplicacion comprueba:

1. La tarea esta habilitada.
2. La red requerida esta activa.
3. El destino existe.
4. El usuario puede escribir en el destino.
5. Hay espacio libre suficiente cuando Windows puede calcularlo.

El ping al servidor se usa como informacion adicional. Si el destino es accesible pero el servidor bloquea ping, la copia puede continuar.

## Comando de copia

La base del comando es:

```text
robocopy ORIGEN DESTINO /E /Z /R:2 /W:5 /MT:8 /FFT /XJ
```

Opciones adicionales:

- `/L`: prueba sin copiar.
- `/MIR`: espejo con eliminacion en destino.
- `/XD`: excluir carpetas.
- `/XF`: excluir archivos.

Codigos de salida:

- `0-1`: correcto.
- `2-7`: advertencia.
- `8 o superior`: error.

## Logs e historial

Cada ejecucion crea un log con:

- Datos de la tarea.
- Comando ejecutado.
- Salida completa de `robocopy`.
- Codigo de salida.
- Fechas de inicio y fin.

Los logs instalados estan en:

```text
%LOCALAPPDATA%\NAS Backup\logs\
```

## La aplicacion sigue abierta al pulsar X

Es el comportamiento esperado. La X oculta la ventana y mantiene las tareas automaticas activas.

Usa **Salir** en la ventana o en la bandeja para cerrar el proceso.

## Destino no accesible

Comprueba:

- Que la ruta UNC existe, por ejemplo `\\SERVIDOR\Carpeta`.
- Que el NAS esta encendido.
- Que Windows tiene credenciales validas.
- Que la red seleccionada esta activa.

Abre primero la ruta desde el Explorador de archivos para que Windows solicite las credenciales.

## Sin permiso de escritura

La carpeta puede ser visible pero estar configurada como solo lectura para el usuario.

Prueba a crear y borrar manualmente un archivo dentro del destino con el mismo usuario de Windows.

## El ping no responde

Algunos servidores bloquean ICMP. Si la ruta destino es accesible y permite escritura, la tarea puede ejecutarse aunque el ping no responda.

## Robocopy devuelve advertencia

Los codigos `2-7` no siempre indican un fallo. Pueden significar que existen archivos extra o diferencias entre origen y destino.

Consulta **Ultimo log** para ver el detalle.

## No se detectan cambios

Comprueba:

- Que el modo sea **Cuando haya cambios** o **Ambas**.
- Que la tarea este habilitada y no pausada.
- Que el archivo no coincida con una exclusion.
- Que la carpeta origen siga existiendo.

La copia no empieza inmediatamente: espera el tiempo configurado para agrupar cambios consecutivos.

El valor predeterminado es de 5 segundos. El observador funciona mientras la aplicacion permanece abierta, incluida la bandeja del sistema.

## Aparecen ventanas de consola

La aplicacion ejecuta `robocopy`, `ping`, `netsh` y PowerShell como procesos ocultos mediante `CREATE_NO_WINDOW`.

Si aparecen consolas, comprueba que estas usando el instalador mas reciente y no una compilacion anterior.

## Inicio con Windows

La opcion usa:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
```

No necesita permisos de administrador y solo afecta al usuario actual.

## Copias simultaneas

La aplicacion permite varias tareas diferentes en paralelo, hasta el limite configurado.

Una misma tarea nunca se ejecuta dos veces simultaneamente. Si no hay capacidad disponible, queda programada hasta que termine otra tarea.
