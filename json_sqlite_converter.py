import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from data.sqlite_db import SQLiteDB
from config.app_config import DB_FOLDER


class JSONtoSQLiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor JSON → SQLite")
        self.root.geometry("600x500")

        self.json_files = []
        self.output_folder = ""

        # === BOTONES ===
        frame_top = tk.Frame(root)
        frame_top.pack(pady=10)

        tk.Button(frame_top, text="Seleccionar JSON",
                  command=self.select_json).pack(side="left", padx=5)

        tk.Button(frame_top, text="Carpeta destino",
                  command=self.select_folder).pack(side="left", padx=5)

        tk.Button(frame_top, text="Convertir",
                  command=self.convert_all,
                  bg="#4CAF50", fg="white").pack(side="left", padx=5)

        # === PROGRESS BAR ===
        self.progress = ttk.Progressbar(root, orient="horizontal",
                                        length=500, mode="determinate")
        self.progress.pack(pady=10)

        # === LOG ===
        self.log = tk.Text(root, height=20, width=70, bg="#F0F0F0")
        self.log.pack(pady=10)
        self.log.config(state="disabled")

    # =========================
    # UI HELPERS
    # =========================
    def write_log(self, text):
        self.log.config(state="normal")
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")
        self.root.update()

    def select_json(self):
        files = filedialog.askopenfilenames(
            title="Selecciona archivos JSON",
            filetypes=[("JSON files", "*.json")]
        )
        if files:
            self.json_files = files
            self.write_log(f"📂 {len(files)} archivo(s) seleccionado(s)")

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Selecciona carpeta destino"
        )
        if folder:
            self.output_folder = folder
            self.write_log(f"📁 Carpeta destino: {folder}")

    # =========================
    # CONVERSIÓN
    # =========================
    def convert_one(self, json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        base_name = os.path.splitext(os.path.basename(json_path))[0]

        # ⚠️ IMPORTANTE:
        # SQLiteDB usa DB_FOLDER, así que temporalmente lo cambiamos
        # si quieres guardar en otra carpeta
        from config import app_config
        original_folder = app_config.DB_FOLDER
        app_config.DB_FOLDER = self.output_folder

        try:
            if SQLiteDB.exists(base_name):
                respuesta = messagebox.askyesno(
                    "Base existente",
                    f"La base '{base_name}' ya existe.\n¿Quieres sobrescribirla?"
                )
                if not respuesta:
                    self.write_log(f"⏭️ Saltada: {base_name}")
                    return
                else:
                    # borrar archivo existente
                    os.remove(os.path.join(DB_FOLDER, f"{base_name}.sqlite"))

            db = SQLiteDB(base_name)

            words = data.get("words", {})
            total = len(words)

            for i, (word, info) in enumerate(words.items(), 1):
                db.add_word(word, info.get("translation", ""))

                # Actualizar resto de campos
                db.update_word(
                    word,
                    correct=info.get("correct", 0),
                    incorrect=info.get("incorrect", 0),
                    streak=info.get("streak", 0),
                    interval=info.get("interval", 1),
                    last_seen=info.get("last_seen")
                )

                # progreso interno
                self.progress["value"] += 1
                self.root.update()

            db.close()
            self.write_log(f"✅ {base_name} convertido ({total} palabras)")

        except Exception as e:
            self.write_log(f"❌ Error en {base_name}: {e}")

        finally:
            # Restaurar carpeta original
            app_config.DB_FOLDER = original_folder

    def convert_all(self):
        if not self.json_files:
            messagebox.showwarning("Aviso", "Selecciona archivos JSON.")
            return

        if not self.output_folder:
            messagebox.showwarning("Aviso", "Selecciona carpeta destino.")
            return

        total_words = 0

        # Contar total para barra progreso
        for path in self.json_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_words += len(data.get("words", {}))
            except:
                pass

        if total_words == 0:
            messagebox.showerror("Error", "No hay palabras para convertir.")
            return

        self.progress["value"] = 0
        self.progress["maximum"] = total_words

        self.write_log("🚀 Iniciando conversión...\n")

        for json_file in self.json_files:
            self.convert_one(json_file)

        self.write_log("\n🎉 Conversión finalizada")
        messagebox.showinfo("Finalizado", "Todos los archivos han sido convertidos.")


if __name__ == "__main__":
    root = tk.Tk()
    app = JSONtoSQLiteApp(root)
    root.mainloop()