import tkinter as tk
from tkinter import messagebox
from data.sqlite_db import SQLiteDB  # módulo que vamos a crear
from logic import json_sqlite_converter

class ManageDatabaseWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestionar Bases")
        self.geometry("600x500")
        self.configure(bg="#FFFFFF")

        # =========================
        # VARIABLES
        # =========================
        self.db_var = tk.StringVar(self)
        self.db_instance = None  # instancia de SQLiteDB actual

        # =========================
        # UI: SELECTOR BASE
        # =========================
        tk.Label(self, text="Base de datos:", bg="#FFFFFF", font=("Arial", 12, "bold")).pack(pady=5)

        self.option_menu = tk.OptionMenu(self, self.db_var, "")
        self.option_menu.pack(pady=5)

        tk.Button(self, text="➕ Nueva Base", command=self.create_db_popup).pack(pady=5)
        tk.Button(self, text="Import JSON", command=json_sqlite_converter.main).pack(pady=5)

        # =========================
        # UI: LISTA DE PALABRAS
        # =========================
        tk.Label(self, text="📚 Palabras:", bg="#FFFFFF", font=("Arial", 12, "bold")).pack(pady=10)

        self.listbox = tk.Listbox(self, width=60, height=12)
        self.listbox.pack(pady=5)

        # =========================
        # UI: FORMULARIO NUEVA PALABRA
        # =========================
        tk.Label(self, text="Nueva palabra", bg="#FFFFFF", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(self, text="Francés:", bg="#FFFFFF").pack()
        self.word_entry = tk.Entry(self)
        self.word_entry.pack(pady=5)

        tk.Label(self, text="Español:", bg="#FFFFFF").pack()
        self.translation_entry = tk.Entry(self)
        self.translation_entry.pack(pady=5)

        tk.Button(self, text="Guardar palabra", command=self.add_word_ui).pack(pady=10)

        tk.Button(self, text="Eliminar palabra seleccionada", command=self.delete_word_ui, fg="white", bg="#E53935").pack(pady=5)

        # =========================
        # REFRESH UI
        # =========================
        self.refresh_ui()

    # =========================
    # MÉTODOS PRINCIPALES
    # =========================
    def refresh_ui(self):
        """Refresca la lista de bases y la lista de palabras."""
        dbs = SQLiteDB.list_databases()
        menu = self.option_menu["menu"]
        menu.delete(0, "end")
        if not dbs:
            self.db_var.set("")
        else:
            for db in dbs:
                menu.add_command(label=db, command=lambda value=db: self.change_db(value))
            if not self.db_var.get():
                self.change_db(dbs[0])

    def change_db(self, db_name):
        """Cambia la base activa."""
        self.db_var.set(db_name)
        self.db_instance = SQLiteDB(db_name)
        self.load_words()

    def load_words(self):
        """Carga todas las palabras de la base en la listbox."""
        self.listbox.delete(0, tk.END)
        if not self.db_instance:
            return
        words = self.db_instance.get_all_words()
        for w, t in words.items():
            self.listbox.insert(tk.END, f"{w} → {t}")

    # =========================
    # CREAR BASE
    # =========================
    def create_db_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Crear Base")
        popup.geometry("300x150")
        tk.Label(popup, text="Nombre de la base:", font=("Arial", 12)).pack(pady=10)
        entry = tk.Entry(popup)
        entry.pack(pady=5)
        tk.Button(popup, text="Crear", command=lambda: self.create_db(entry.get(), popup)).pack(pady=10)

    def create_db(self, name, popup):
        name = name.strip().lower()
        if not name:
            messagebox.showerror("Error", "El nombre no puede estar vacío.")
            return
        if SQLiteDB.exists(name):
            messagebox.showerror("Error", "La base ya existe.")
            return
        SQLiteDB.create_database(name)
        messagebox.showinfo("Éxito", f"Base '{name}' creada correctamente.")
        popup.destroy()
        self.refresh_ui()

    # =========================
    # AGREGAR PALABRA
    # =========================
    def add_word_ui(self):
        if not self.db_instance:
            return
        word = self.word_entry.get().strip().lower()
        translation = self.translation_entry.get().strip().lower()
        if not word or not translation:
            return
        self.db_instance.add_word(word, translation)
        self.word_entry.delete(0, tk.END)
        self.translation_entry.delete(0, tk.END)
        self.load_words()

    # =========================
    # ELIMINAR PALABRA
    # =========================
    def delete_word_ui(self):
        if not self.db_instance:
            return
        selection = self.listbox.curselection()
        if not selection:
            return
        word_line = self.listbox.get(selection[0])
        word = word_line.split(" → ")[0]
        self.db_instance.delete_word(word)
        self.load_words()