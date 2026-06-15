# Instalacion y actualizacion

## Instalar

Ejecuta:

```text
release\installer\NAS_Backup_Setup.exe
```

El instalador:

- No requiere permisos de administrador.
- Instala para el usuario actual.
- Crea accesos en el menu Inicio.
- Puede crear un acceso directo en el escritorio.
- Registra el desinstalador en Windows.

Ruta de instalacion:

```text
%LOCALAPPDATA%\Programs\NAS Backup\
```

## Actualizar

Cierra NAS Backup y ejecuta una version nueva del instalador.

La actualizacion reemplaza los archivos del programa y conserva tareas, preferencias, historial y logs.

NAS Backup puede avisar cuando exista una release estable de GitHub con una
version superior a la instalada. La descarga e instalacion siguen siendo
manuales.

## Desinstalar

Se puede desinstalar desde:

```text
Menu Inicio\NAS Backup\Desinstalar NAS Backup
```

O desde:

```text
Configuracion de Windows > Aplicaciones instaladas
```

La desinstalacion conserva los datos del usuario para evitar perdidas accidentales.

Para eliminarlos manualmente despues de desinstalar:

```text
%LOCALAPPDATA%\NAS Backup\
```

## Datos de usuario

La aplicacion instalada guarda:

```text
%LOCALAPPDATA%\NAS Backup\app.db
%LOCALAPPDATA%\NAS Backup\logs\
```

En desarrollo se usan:

```text
data\app.db
data\logs\
```

## Version portable

El resultado de PyInstaller se encuentra en:

```text
release\portable\NAS Backup\
```

Hay que copiar la carpeta completa. `NAS Backup.exe` necesita el contenido de `_internal`.

## Permisos

La aplicacion no necesita ejecutarse como administrador. El usuario de Windows debe tener:

- Lectura en la carpeta origen.
- Lectura y escritura en la carpeta destino.
- Acceso a la red o credenciales del NAS.

Las credenciales de red se administran desde Windows. NAS Backup no almacena contrasenas del NAS.
