from __future__ import annotations

import os

from app.models import TASK_MODES, Task


def is_dangerous_mirror_destination(destination: str) -> bool:
    raw_destination = destination.strip()
    if not raw_destination:
        return True
    try:
        normalized = os.path.realpath(os.path.abspath(raw_destination))
    except OSError:
        normalized = raw_destination
    dest = normalized.replace("/", "\\").rstrip("\\")
    drive, tail = os.path.splitdrive(dest)
    if drive and not tail.strip("\\"):
        return True
    if dest.startswith("\\\\"):
        parts = [part for part in dest.split("\\") if part]
        return len(parts) <= 2
    return False


def paths_overlap(source_path: str, destination_path: str) -> bool:
    try:
        source = os.path.normcase(os.path.realpath(os.path.abspath(source_path)))
        destination = os.path.normcase(os.path.realpath(os.path.abspath(destination_path)))
        common = os.path.commonpath((source, destination))
    except (OSError, ValueError):
        return False
    return common in {source, destination}


def validate_task_data(task: Task, require_existing_source: bool = True) -> str | None:
    if not task.name:
        return "El nombre no puede estar vacio."
    if not task.source_path:
        return "La carpeta origen no puede estar vacia."
    if require_existing_source and not os.path.isdir(task.source_path):
        return "La carpeta origen no existe."
    if not task.destination_path:
        return "La carpeta destino no puede estar vacia."
    if task.mode not in TASK_MODES:
        return "Modo de ejecucion no valido."
    if task.mode in ("interval", "both") and (not task.interval_minutes or task.interval_minutes < 1):
        return "El intervalo debe ser mayor que 0."
    if paths_overlap(task.source_path, task.destination_path):
        return "Origen y destino no pueden ser iguales ni estar uno dentro del otro."
    if int(task.mirror_delete) and is_dangerous_mirror_destination(task.destination_path):
        return "El destino es demasiado general para usar borrado espejo."
    return None
