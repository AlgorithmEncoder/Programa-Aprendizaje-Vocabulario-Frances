import os
import sys

# Detectar si está empaquetado (exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "AprenderFrances")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FOLDER = os.path.join(BASE_DIR, "databases")
RESULT_FOLDER = os.path.join(BASE_DIR, "results")

# Crear carpetas si no existen
os.makedirs(DB_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)