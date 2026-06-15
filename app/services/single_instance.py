from __future__ import annotations

import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from app.config import RUN_REGISTRY_NAME


class SingleInstance(QObject):
    activation_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.server_name = f"{RUN_REGISTRY_NAME}.SingleInstance"
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._on_new_connection)
        self.mutex = None

    def acquire(self) -> bool:
        if os.name == "nt":
            import win32api
            import win32event
            import winerror

            mutex_name = f"Local\\{self.server_name}.Mutex"
            self.mutex = win32event.CreateMutex(None, False, mutex_name)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                self._request_activation()
                win32api.CloseHandle(self.mutex)
                self.mutex = None
                return False

            QLocalServer.removeServer(self.server_name)
            self.server.listen(self.server_name)
            return True

        if self.server.listen(self.server_name):
            return True
        if self._request_activation():
            return False
        QLocalServer.removeServer(self.server_name)
        return self.server.listen(self.server_name)

    def _request_activation(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if socket.waitForConnected(500):
            socket.write(b"show")
            socket.flush()
            socket.waitForBytesWritten(500)
            socket.disconnectFromServer()
            return True
        return False

    def _on_new_connection(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.waitForReadyRead(100)
            socket.readAll()
            socket.disconnectFromServer()
            socket.deleteLater()
            self.activation_requested.emit()
