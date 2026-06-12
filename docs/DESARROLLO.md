# Desarrollo y compilacion

## Requisitos

- Windows 10 u 11.
- Python 3.11 o superior.
- PyQt5.
- Qt Designer para editar los archivos `.ui`.
- PyInstaller para generar la aplicacion portable.
- Inno Setup para generar el instalador.

Dependencias de ejecucion:

```text
PyQt5
watchdog
pywin32
```

## Preparar el entorno

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

Los entornos `.venv/` y `venv/` estan ignorados por Git.

## Ejecutar desde el codigo

```powershell
python main.py
```

Arranque minimizado:

```powershell
python main.py --minimized
```

## Editar la interfaz

Los archivos editables con Qt Designer son:

```text
app\ui\main_window.ui
app\ui\task_dialog.ui
app\ui\settings_dialog.ui
```

La aplicacion los carga directamente mediante `uic.loadUi`. Los archivos `app/ui/*_ui.py` no son necesarios y estan ignorados.

## Generar portable e instalador

Desde la raiz del proyecto:

```powershell
.\scripts\build_installer.ps1
```

El script:

1. Elimina archivos `*_ui.py` generados por el IDE.
2. Ejecuta PyInstaller con `packaging/windows/NAS Backup.spec`.
3. Crea la aplicacion portable.
4. Busca Inno Setup.
5. Compila `packaging/windows/installer.iss`.

Resultados:

```text
release\portable\NAS Backup\NAS Backup.exe
release\installer\NAS_Backup_Setup.exe
```

Si Inno Setup no esta instalado, el script conserva la version portable y muestra una advertencia.

## Instalar Inno Setup

```powershell
winget install --id JRSoftware.InnoSetup -e
```

## Compilar solo con PyInstaller

```powershell
pyinstaller "packaging\windows\NAS Backup.spec" `
  --clean `
  --noconfirm `
  --distpath "release\portable" `
  --workpath "build\pyinstaller"
```

## Version

La version mostrada por Windows se define en:

```text
packaging\windows\installer.iss
```

Actualiza `MyAppVersion` antes de publicar una nueva version.

## Archivos generados

Estas rutas no deben incluirse en commits:

```text
build\
release\
__pycache__\
data\app.db
data\logs\
```

Consulta [Estructura del repositorio](ESTRUCTURA.md) para mas detalle.
