# cursor_demo.py
# DEMO (Windows): ventana PyQt6 con "consola" integrada que muestra coordenadas de clics (ESC para salir)

import os
import sys
import subprocess
import threading

try:
    from pynput import mouse, keyboard
except ImportError:
    print("Falta 'pynput'. Instálalo con: pip install pynput")
    sys.exit(1)

# ─────────────────────────────── NUEVO: PyQt6 UI ───────────────────────────────
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPlainTextEdit, QPushButton, QHBoxLayout, QLabel
)

m_listener = None
k_listener = None

# ===== Mantengo tu lógica de impresión; ahora se redirige a la UI =====
def on_click(x, y, button, pressed):
    if pressed:
        print(f"[CLICK] x={x}  y={y}  button={button}", flush=True)

def on_press(key):
    global m_listener
    if key == keyboard.Key.esc:
        print("Saliendo…", flush=True)
        if m_listener is not None:
            m_listener.stop()
        return False  # Detiene el listener de teclado

# ────────────────────────── Pequeña mejora: callback opcional ──────────────────────────
def run_listeners(on_done_callback=None):
    """
    Inicia listeners de mouse/teclado, bloqueando hasta que terminen.
    Al terminar, ejecuta on_done_callback() si se proporcionó.
    """
    global m_listener, k_listener
    print("Escucha de clics iniciada. Haz clic donde quieras medir.", flush=True)
    print("Pulsa ESC para salir.\n", flush=True)

    # Iniciar listeners manualmente (evita 'threads can only be started once')
    m_listener = mouse.Listener(on_click=on_click)
    k_listener = keyboard.Listener(on_press=on_press)

    m_listener.start()
    k_listener.start()

    try:
        m_listener.join()
        k_listener.join()
    except KeyboardInterrupt:
        if m_listener is not None:
            m_listener.stop()
        if k_listener is not None:
            k_listener.stop()
        print("Interrumpido por el usuario.", flush=True)

    if callable(on_done_callback):
        on_done_callback()

# ─────────────────────────────── Utilidades PyQt6 ───────────────────────────────
class EmittingStream(QObject):
    """Redirige stdout/stderr a la UI con señales (thread-safe)."""
    text_written = pyqtSignal(str)

    def write(self, text):
        if text:
            self.text_written.emit(str(text))

    def flush(self):
        # Necesario para ser un drop-in replacement de sys.stdout/sys.stderr
        pass


class ConsoleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cursor Demo - Coordenadas")
        self.setMinimumSize(720, 420)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Cabecera ligera
        header = QHBoxLayout()
        label = QLabel("Consola / Log de clics (ESC para salir)")
        label.setStyleSheet("color:#555;")
        header.addWidget(label)
        header.addStretch(1)
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.clicked.connect(self.clear_console)
        self.btn_exit = QPushButton("Salir")
        self.btn_exit.clicked.connect(self.close)
        header.addWidget(self.btn_clear)
        header.addWidget(self.btn_exit)
        layout.addLayout(header)

        # Consola (QPlainTextEdit) en monospace
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "font-family: Consolas, 'Courier New', monospace; font-size: 12px;"
        )
        layout.addWidget(self.console, 1)

        # Stream emisor y redirección
        self.stdout_stream = EmittingStream()
        self.stderr_stream = EmittingStream()
        self.stdout_stream.text_written.connect(self.append_text)
        self.stderr_stream.text_written.connect(self.append_text)

        # Redirigir stdout/stderr a la ventana
        sys.stdout = self.stdout_stream  # <-- clave: todos tus print() van a la UI
        sys.stderr = self.stderr_stream

        # Hilo para no bloquear la UI con los listeners
        self._listeners_thread = threading.Thread(
            target=run_listeners, kwargs={"on_done_callback": self.on_listeners_done},
            daemon=True
        )
        self._listeners_thread.start()

    def append_text(self, text: str):
        # Añade y hace scroll al final
        self.console.moveCursor(self.console.textCursor().MoveOperation.End)
        self.console.insertPlainText(text)
        self.console.moveCursor(self.console.textCursor().MoveOperation.End)

    def clear_console(self):
        self.console.clear()

    def on_listeners_done(self):
        print("\n[INFO] Listeners detenidos. Cerrando ventana…", flush=True)
        # Cierra la ventana al terminar (señal cruzada con el hilo UI usando singleShot)
        QApplication.instance().postEvent(self, CloseEventRequest())

    def closeEvent(self, event):
        # Intenta detener cualquier listener aún activo
        global m_listener, k_listener
        try:
            if m_listener is not None:
                m_listener.stop()
        except Exception:
            pass
        try:
            if k_listener is not None:
                k_listener.stop()
        except Exception:
            pass
        # Restaura stdout/stderr para no dejarlo enganchado
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        except Exception:
            pass
        super().closeEvent(event)


# Evento simple para pedir cierre desde otro hilo
from PyQt6.QtCore import QEvent
class CloseEventRequest(QEvent):
    TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self):
        super().__init__(CloseEventRequest.TYPE)

def eventFilter_close_on_custom(obj, event):
    return False  # no lo usamos; QMainWindow procesa el evento en event()

def main():
    # Anteriormente abríamos una nueva consola con CREATE_NEW_CONSOLE; ahora
    # mostramos la consola dentro de PyQt6 como pediste.
    app = QApplication(sys.argv)
    win = ConsoleWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
