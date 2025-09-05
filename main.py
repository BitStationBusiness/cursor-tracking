# cursor_demo.py
# DEMO (Windows): abre una nueva CMD y muestra coordenadas de clics (ESC para salir)

import os
import sys
import subprocess

try:
    from pynput import mouse, keyboard
except ImportError:
    print("Falta 'pynput'. Instálalo con: pip install pynput")
    sys.exit(1)

m_listener = None
k_listener = None

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

def run_listeners():
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

def main():
    # Si no somos el proceso hijo, abrimos una NUEVA consola y relanzamos el script con --child
    if os.name == "nt" and "--child" not in sys.argv:
        script = os.path.abspath(__file__)
        python_exe = sys.executable
        try:
            # Preferible: nueva consola propia del intérprete
            subprocess.Popen(
                [python_exe, script, "--child"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception:
            # Respaldo: abrir cmd y ejecutar python
            cmd = f'"{python_exe}" "{script}" --child'
            subprocess.Popen(['cmd', '/k', cmd], shell=False)
        sys.exit(0)

    # Proceso hijo: ya estamos dentro de la nueva CMD
    if os.name == "nt":
        try:
            os.system('title Cursor Demo - Coordenadas')
        except Exception:
            pass
    run_listeners()

if __name__ == "__main__":
    main()
