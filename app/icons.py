from __future__ import annotations

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


ICON_COLOR = QColor("#f1f5f9")


def create_icon(name: str, color: QColor = ICON_COLOR, size: int = 24) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    draw = _DRAWERS.get(name)
    if draw:
        draw(painter, size)

    painter.end()
    return QIcon(pixmap)


def _plus(painter: QPainter, size: int) -> None:
    center = size / 2
    painter.drawLine(QPointF(center, 5), QPointF(center, size - 5))
    painter.drawLine(QPointF(5, center), QPointF(size - 5, center))


def _edit(painter: QPainter, size: int) -> None:
    painter.drawLine(QPointF(6, size - 6), QPointF(size - 6, 6))
    painter.drawLine(QPointF(5, size - 5), QPointF(10, size - 6))
    painter.drawLine(QPointF(size - 8, 5), QPointF(size - 5, 8))


def _trash(painter: QPainter, size: int) -> None:
    painter.drawRect(QRectF(7, 8, size - 14, size - 14))
    painter.drawLine(QPointF(5, 7), QPointF(size - 5, 7))
    painter.drawLine(QPointF(9, 4), QPointF(size - 9, 4))
    painter.drawLine(QPointF(10, 11), QPointF(10, size - 8))
    painter.drawLine(QPointF(size - 10, 11), QPointF(size - 10, size - 8))


def _play(painter: QPainter, size: int) -> None:
    path = QPainterPath()
    path.moveTo(7, 5)
    path.lineTo(size - 5, size / 2)
    path.lineTo(7, size - 5)
    path.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(path)


def _check(painter: QPainter, size: int) -> None:
    painter.drawLine(QPointF(5, size / 2), QPointF(10, size - 6))
    painter.drawLine(QPointF(10, size - 6), QPointF(size - 5, 6))


def _close(painter: QPainter, size: int) -> None:
    painter.drawLine(QPointF(6, 6), QPointF(size - 6, size - 6))
    painter.drawLine(QPointF(size - 6, 6), QPointF(6, size - 6))


def _pause(painter: QPainter, size: int) -> None:
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawRoundedRect(QRectF(6, 5, 4, size - 10), 1, 1)
    painter.drawRoundedRect(QRectF(size - 10, 5, 4, size - 10), 1, 1)


def _document(painter: QPainter, size: int) -> None:
    path = QPainterPath()
    path.moveTo(6, 4)
    path.lineTo(size - 10, 4)
    path.lineTo(size - 5, 9)
    path.lineTo(size - 5, size - 4)
    path.lineTo(6, size - 4)
    path.closeSubpath()
    painter.drawPath(path)
    painter.drawLine(QPointF(size - 10, 4), QPointF(size - 10, 9))
    painter.drawLine(QPointF(size - 10, 9), QPointF(size - 5, 9))


def _history(painter: QPainter, size: int) -> None:
    painter.drawArc(QRectF(5, 5, size - 10, size - 10), 35 * 16, 300 * 16)
    painter.drawLine(QPointF(5, 6), QPointF(5, 11))
    painter.drawLine(QPointF(5, 6), QPointF(10, 6))
    painter.drawLine(QPointF(size / 2, 8), QPointF(size / 2, size / 2))
    painter.drawLine(QPointF(size / 2, size / 2), QPointF(size - 8, size / 2))


def _exit(painter: QPainter, size: int) -> None:
    painter.drawRect(QRectF(5, 4, 9, size - 8))
    painter.drawLine(QPointF(10, size / 2), QPointF(size - 4, size / 2))
    painter.drawLine(QPointF(size - 8, size / 2 - 4), QPointF(size - 4, size / 2))
    painter.drawLine(QPointF(size - 8, size / 2 + 4), QPointF(size - 4, size / 2))


def _folder(painter: QPainter, size: int) -> None:
    path = QPainterPath()
    path.moveTo(4, 7)
    path.lineTo(10, 7)
    path.lineTo(12, 10)
    path.lineTo(size - 4, 10)
    path.lineTo(size - 6, size - 5)
    path.lineTo(4, size - 5)
    path.closeSubpath()
    painter.drawPath(path)


def _refresh(painter: QPainter, size: int) -> None:
    painter.drawArc(QRectF(5, 5, size - 10, size - 10), 45 * 16, 275 * 16)
    painter.drawLine(QPointF(size - 5, 6), QPointF(size - 5, 11))
    painter.drawLine(QPointF(size - 5, 6), QPointF(size - 10, 6))


def _save(painter: QPainter, size: int) -> None:
    painter.drawRect(QRectF(5, 4, size - 10, size - 8))
    painter.drawRect(QRectF(8, 5, size - 16, 6))
    painter.drawRect(QRectF(8, 14, size - 16, size - 19))


_DRAWERS = {
    "add": _plus,
    "edit": _edit,
    "delete": _trash,
    "run": _play,
    "test": _check,
    "cancel": _close,
    "pause": _pause,
    "log": _document,
    "history": _history,
    "exit": _exit,
    "folder": _folder,
    "refresh": _refresh,
    "save": _save,
}
