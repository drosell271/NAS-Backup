from __future__ import annotations

import os

from app.models import TASK_MODES, Task


def validate_task_data(task: Task, require_existing_source: bool = True) -> str | None:
    if not task.name:
        return "El nombre no puede estar vacio."
    if not task.source_path:
        return "La carpeta origen no puede estar vacia."
    if require_existing_source and not os.path.isdir(task.source_path):
        return "La carpeta origen no existe."
    if not task.destination_path:
        return "La carpeta destino no puede estar vacia."
    if not task.server_ip:
        return "La IP del servidor no puede estar vacia."
    if task.mode not in TASK_MODES:
        return "Modo de ejecucion no valido."
    if task.mode in ("interval", "both") and (not task.interval_minutes or task.interval_minutes < 1):
        return "El intervalo debe ser mayor que 0."
    try:
        source = os.path.normcase(os.path.abspath(task.source_path))
        destination = os.path.normcase(os.path.abspath(task.destination_path))
    except OSError:
        source = task.source_path.strip().lower()
        destination = task.destination_path.strip().lower()
    if source == destination:
        return "Origen y destino no pueden ser iguales."
    return None
