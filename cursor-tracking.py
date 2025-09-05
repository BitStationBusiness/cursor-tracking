# cursor_demo.py
# DEMO: captura global de clics y muestra coordenadas en consola (ESC para salir).

from pynput import mouse, keyboard

print("Escucha de clics iniciada. Haz clic donde quieras medir.")
print("Pulsa ESC para salir.\n")

# Mantendremos referencias globales para poder detener ambos listeners desde ESC
m_listener = None
k_listener = None

def on_click(x, y, button, pressed):
    if pressed:
        print(f"[CLICK] x={x}  y={y}  button={button}")

def on_press(key):
    global m_listener, k_listener
    try:
        if key == keyboard.Key.esc:
            print("Saliendo…")
            # Detiene el listener de mouse; devolver False detiene el de teclado
            if m_listener is not None:
                m_listener.stop()
            return False
    except Exception:
        # Si algo falla, detenemos todo por seguridad
        if m_listener is not None:
            m_listener.stop()
        return False

if __name__ == "__main__":
    # Iniciar listeners SIN usar 'with' para controlar el ciclo de vida manualmente
    m_listener = mouse.Listener(on_click=on_click)
    k_listener = keyboard.Listener(on_press=on_press)

    m_listener.start()
    k_listener.start()

    # Esperar a que se detengan (ESC detiene ambos)
    try:
        m_listener.join()
        k_listener.join()
    except KeyboardInterrupt:
        # Permite salir con Ctrl+C en consola
        if m_listener is not None:
            m_listener.stop()
        if k_listener is not None:
            k_listener.stop()
        print("Interrumpido por el usuario.")
