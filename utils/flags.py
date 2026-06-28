"""
Flags de runtime (no persistentes).

`post_mvp` controla la visibilidad de funcionalidades que NO forman parte del
MVP documentado (p. ej. el agente Quirón de captura de conocimiento). Está
APAGADO por defecto, de modo que la app desplegada coincide con lo entregado.

Se activa/desactiva como atajo de desarrollo escribiendo el código secreto en
el selector de idiomas. La bandera es global al proceso del servidor (afecta a
todas las sesiones) y se reinicia a False en cada redeploy/reinicio.
"""

# Código que se escribe en el buscador del selector de idiomas para alternar el modo.
SECRET_CODE = "modopostMVP"

_post_mvp_enabled = False


def is_post_mvp() -> bool:
    return _post_mvp_enabled


def toggle_post_mvp() -> bool:
    global _post_mvp_enabled
    _post_mvp_enabled = not _post_mvp_enabled
    return _post_mvp_enabled
