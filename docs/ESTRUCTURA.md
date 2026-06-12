# Estructura del repositorio

## Carpetas

```text
app/                    codigo de la aplicacion
  assets/               icono y logo
  services/             copia, red, tareas, scheduler y bandeja
  storage/              migraciones
  ui/                   archivos editables de Qt Designer
  views/                ventanas y dialogos PyQt5

data/                   datos locales de desarrollo
docs/                   documentacion
packaging/windows/      configuracion de PyInstaller e Inno Setup
scripts/                scripts de automatizacion
release/                ejecutables generados

main.py                 punto de entrada
requirements.txt        dependencias de ejecucion
README.md               introduccion y acceso rapido
.gitignore              archivos locales y generados
```

## Archivos versionables

Se deben incluir en Git:

- Codigo dentro de `app/`.
- Archivos `.ui`.
- Recursos de `app/assets/`.
- Documentacion.
- `main.py` y `requirements.txt`.
- `scripts/build_installer.ps1`.
- Archivos de `packaging/windows/`.
- `data/logs/.gitkeep`.

## Archivos ignorados

No se deben incluir:

- Entornos virtuales.
- Base de datos y logs locales.
- Cachés de Python.
- Archivos `*_ui.py` generados.
- Carpetas de build.
- Aplicacion portable e instalador.

Los binarios de `release/` se publican como artefactos o releases del repositorio, no como codigo fuente.

## Datos locales

En desarrollo, la aplicacion utiliza:

```text
data\app.db
data\logs\
```

Estos archivos contienen configuracion e historial local y estan ignorados por Git.

## Empaquetado

```text
packaging\windows\NAS Backup.spec
```

Define los modulos, recursos y opciones de PyInstaller.

```text
packaging\windows\installer.iss
```

Define la instalacion, accesos directos, version y desinstalador de Windows.

```text
scripts\build_installer.ps1
```

Coordina ambos procesos y deja los resultados en `release/`.
