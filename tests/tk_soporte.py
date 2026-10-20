"""Raíz Tkinter compartida por las pruebas de GUI.

Crear y destruir varias instancias de ``tk.Tk()`` en un mismo proceso es
inestable en algunas instalaciones de Tk (falla al buscar ``init.tcl`` o al
redefinir ``tcl_findLibrary``). Por eso todas las pruebas de GUI usan una sola
raíz oculta para todo el proceso; las ventanas ``AppTacticalGrid`` son
``Toplevel`` y sí se crean/destruyen por prueba.
"""
import unittest

_raiz = None


def raiz_compartida():
    """Devuelve la raíz Tk oculta del proceso, creándola la primera vez.

    Si Tkinter no está disponible (sin pantalla, instalación incompleta), lanza
    unittest.SkipTest para que las pruebas de GUI se omitan limpiamente.
    """
    global _raiz
    if _raiz is None:
        try:
            import tkinter as tk
            _raiz = tk.Tk()
            _raiz.withdraw()
        except Exception as error:
            raise unittest.SkipTest(f"no se puede abrir Tkinter: {error}")
    return _raiz
