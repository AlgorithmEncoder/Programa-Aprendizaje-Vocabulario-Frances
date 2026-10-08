import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from data.sqlite_db import SQLiteDB  # Tu clase de manejo de SQLite
from config.app_config import DB_FOLDER


def json_to_sqlite(json_path, output_folder=DB_FOLDER):
    """Convierte un archivo JSON a SQLite."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Usamos el nombre del archivo JSON como nombre de la DB
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    db_path = os.path.join(output_folder, f"{base_name}.sqlite")

    # Crear la base usando SQLiteDB
    if SQLiteDB.exists(base_name):
        respuesta = messagebox.askyesno(
            "Base existente",
            f"La base '{base_name}' ya existe.\n¿Quieres sobrescribirla?"
        )
        if not respuesta:
            return
        else:
            # borrar archivo existente
            import os
            from config.app_config import DB_FOLDER
            os.remove(os.path.join(DB_FOLDER, f"{base_name}.sqlite"))

    db = SQLiteDB(base_name)

    # Insertar palabras
    words = data.get("words", {})
    for word, info in words.items():
        db.add_word(
            word,
            info.get("translation", "")
        )
        # Actualizamos los demás campos si existen
        db.update_word(
            word,
            correct=info.get("correct", 0),
            incorrect=info.get("incorrect", 0),
            streak=info.get("streak", 0),
            interval=info.get("interval", 1),
            last_seen=info.get("last_seen")
        )

    db.close()


def main():
    root = tk.Toplevel()
    root.withdraw()  # Oculta la ventana principal

    # Selección de archivos JSON
    json_files = filedialog.askopenfilenames(
        title="Selecciona uno o varios archivos JSON",
        filetypes=[("JSON files", "*.json")]
    )
    if not json_files:
        messagebox.showinfo("Info", "No se seleccionaron archivos.")
        return

    # Convertir cada JSON
    for json_file in json_files:
        try:
            json_to_sqlite(json_file)
            print(f"✅ {os.path.basename(json_file)} → convertido correctamente")
        except Exception as e:
            print(f"❌ Error al convertir {json_file}: {e}")

    messagebox.showinfo("Finalizado", "Todos los archivos seleccionados han sido convertidos a SQLite.")
