"""
Ventana de gestión de bases de datos y vocabulario.

Permite:

- seleccionar una base;
- crear nuevas bases;
- importar vocabulario desde JSON;
- consultar palabras;
- añadir palabras;
- eliminar palabras.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from data.sqlite_db import SQLiteDB
from json_sqlite_converter import open_converter


class ManageDatabaseWindow(tk.Toplevel):
    """
    Ventana para gestionar las bases de vocabulario.
    """

    def __init__(
        self,
        parent: tk.Misc,
    ) -> None:
        super().__init__(parent)

        self.title(
            "Gestionar bases de datos"
        )
        self.geometry(
            "700x550"
        )
        self.minsize(
            600,
            450,
        )

        self.db_var = tk.StringVar(
            self
        )
        self.word_var = tk.StringVar(
            self
        )
        self.translation_var = tk.StringVar(
            self
        )

        self.db_instance: SQLiteDB | None = None
        self.converter: object | None = None

        self._create_widgets()
        self._load_databases()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """
        Construye la interfaz.
        """
        main = ttk.Frame(
            self,
            padding=15,
        )
        main.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            main,
            text="Gestión de vocabulario",
            font=("Arial", 18, "bold"),
        ).pack(
            pady=(0, 15),
        )

        # --------------------------------------------------------------
        # Base
        # --------------------------------------------------------------

        database_frame = ttk.LabelFrame(
            main,
            text="Base de datos",
            padding=10,
        )
        database_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            database_frame,
            text="Base activa:",
        ).grid(
            row=0,
            column=0,
            padx=(0, 8),
            pady=5,
        )

        self.database_combo = ttk.Combobox(
            database_frame,
            textvariable=self.db_var,
            state="readonly",
        )
        self.database_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        self.database_combo.bind(
            "<<ComboboxSelected>>",
            self._on_database_selected,
        )

        ttk.Button(
            database_frame,
            text="Nueva base",
            command=self.create_db_popup,
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
        )

        ttk.Button(
            database_frame,
            text="Importar JSON",
            command=self._import_json,
        ).grid(
            row=0,
            column=3,
            padx=(5, 0),
            pady=5,
        )

        database_frame.columnconfigure(
            1,
            weight=1,
        )

        # --------------------------------------------------------------
        # Palabras
        # --------------------------------------------------------------

        words_frame = ttk.LabelFrame(
            main,
            text="Vocabulario",
            padding=10,
        )
        words_frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10),
        )

        columns = (
            "word",
            "translation",
            "state",
        )

        self.words_tree = ttk.Treeview(
            words_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.words_tree.heading(
            "word",
            text="Francés",
        )
        self.words_tree.heading(
            "translation",
            text="Español",
        )
        self.words_tree.heading(
            "state",
            text="Estado",
        )

        self.words_tree.column(
            "word",
            width=180,
            anchor="w",
        )
        self.words_tree.column(
            "translation",
            width=220,
            anchor="w",
        )
        self.words_tree.column(
            "state",
            width=120,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            words_frame,
            orient="vertical",
            command=self.words_tree.yview,
        )

        self.words_tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self.words_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        # --------------------------------------------------------------
        # Añadir palabra
        # --------------------------------------------------------------

        form_frame = ttk.LabelFrame(
            main,
            text="Añadir palabra",
            padding=10,
        )
        form_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            form_frame,
            text="Francés:",
        ).grid(
            row=0,
            column=0,
            padx=(0, 5),
            pady=5,
        )

        ttk.Entry(
            form_frame,
            textvariable=self.word_var,
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ttk.Label(
            form_frame,
            text="Español:",
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
        )

        ttk.Entry(
            form_frame,
            textvariable=self.translation_var,
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ttk.Button(
            form_frame,
            text="Guardar",
            command=self.add_word_ui,
        ).grid(
            row=0,
            column=4,
            padx=(10, 0),
            pady=5,
        )

        form_frame.columnconfigure(
            1,
            weight=1,
        )
        form_frame.columnconfigure(
            3,
            weight=1,
        )

        # --------------------------------------------------------------
        # Acciones
        # --------------------------------------------------------------

        ttk.Button(
            main,
            text="Eliminar seleccionada",
            command=self.delete_word_ui,
        ).pack(
            anchor="e",
        )

    # ------------------------------------------------------------------
    # Bases
    # ------------------------------------------------------------------

    def _load_databases(self) -> None:
        """
        Carga las bases existentes.
        """
        try:
            databases = SQLiteDB.list_databases()

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudieron cargar las bases:\n\n"
                    f"{error}"
                ),
                parent=self,
            )
            return

        self.database_combo["values"] = databases

        if not databases:
            self.db_var.set("")
            self._close_current_database()
            self._clear_words()
            return

        current = self.db_var.get()

        if current not in databases:
            current = databases[0]
            self.db_var.set(current)

        self.change_db(current)

    def refresh_ui(self) -> None:
        """
        Refresca toda la ventana.
        """
        self._load_databases()

    def _on_database_selected(
        self,
        _event: tk.Event,
    ) -> None:
        """
        Gestiona el cambio de base.
        """
        self.change_db(
            self.db_var.get()
        )

    def change_db(
        self,
        db_name: str,
    ) -> None:
        """
        Cambia la base activa.
        """
        db_name = db_name.strip()

        if not db_name:
            return

        self._close_current_database()

        try:
            self.db_instance = SQLiteDB(
                db_name=db_name
            )
            self.load_words()

        except Exception as error:
            self.db_instance = None

            messagebox.showerror(
                "Error",
                (
                    "No se pudo abrir la base:\n\n"
                    f"{error}"
                ),
                parent=self,
            )

    # ------------------------------------------------------------------
    # Crear base
    # ------------------------------------------------------------------

    def create_db_popup(self) -> None:
        """
        Muestra el formulario de creación.
        """
        popup = tk.Toplevel(
            self
        )
        popup.title(
            "Nueva base de datos"
        )
        popup.resizable(
            False,
            False,
        )

        frame = ttk.Frame(
            popup,
            padding=20,
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            frame,
            text="Nombre de la base:",
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        name_var = tk.StringVar()

        entry = ttk.Entry(
            frame,
            textvariable=name_var,
            width=35,
        )
        entry.pack(
            fill="x",
            pady=(0, 10),
        )

        entry.focus_set()

        ttk.Button(
            frame,
            text="Crear",
            command=lambda: self.create_db(
                name_var.get(),
                popup,
            ),
        ).pack(
            anchor="e",
        )

        popup.bind(
            "<Return>",
            lambda _event: self.create_db(
                name_var.get(),
                popup,
            ),
        )

    def create_db(
        self,
        name: str,
        popup: tk.Toplevel,
    ) -> None:
        """
        Crea una nueva base.
        """
        name = name.strip().lower()

        if not name:
            messagebox.showerror(
                "Error",
                "El nombre no puede estar vacío.",
                parent=popup,
            )
            return

        try:
            if SQLiteDB.exists(name):
                messagebox.showerror(
                    "Error",
                    "Ya existe una base con ese nombre.",
                    parent=popup,
                )
                return

            SQLiteDB.create_database(
                name
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo crear la base:\n\n"
                    f"{error}"
                ),
                parent=popup,
            )
            return

        popup.destroy()

        self._load_databases()

        self.db_var.set(name)
        self.change_db(name)

        messagebox.showinfo(
            "Base creada",
            (
                f"La base '{name}' "
                "se ha creado correctamente."
            ),
            parent=self,
        )

    # ------------------------------------------------------------------
    # Palabras
    # ------------------------------------------------------------------

    def load_words(self) -> None:
        """
        Carga el vocabulario de la base activa.
        """
        self._clear_words()

        if self.db_instance is None:
            return

        try:
            words = self.db_instance.get_all_words()

            for info in words:
                self.words_tree.insert(
                    "",
                    tk.END,
                    values=(
                        info.get("word", ""),
                        info.get("translation", ""),
                        info.get("estado", ""),
                    ),
                )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudieron cargar las palabras:\n\n"
                    f"{error}"
                ),
                parent=self,
            )

    def _clear_words(self) -> None:
        """
        Vacía la lista.
        """
        for item in self.words_tree.get_children():
            self.words_tree.delete(
                item
            )

    def add_word_ui(self) -> None:
        """
        Añade una palabra.
        """
        if self.db_instance is None:
            messagebox.showwarning(
                "Sin base",
                "Selecciona primero una base.",
                parent=self,
            )
            return

        word = (
            self.word_var
            .get()
            .strip()
            .lower()
        )

        translation = (
            self.translation_var
            .get()
            .strip()
            .lower()
        )

        if not word or not translation:
            messagebox.showwarning(
                "Datos incompletos",
                (
                    "Debes introducir tanto "
                    "la palabra como su traducción."
                ),
                parent=self,
            )
            return

        try:
            added = self.db_instance.add_word(
                word,
                translation,
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            messagebox.showerror(
                "Datos no válidos",
                str(error),
                parent=self,
            )
            return

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo guardar la palabra:\n\n"
                    f"{error}"
                ),
                parent=self,
            )
            return

        if not added:
            messagebox.showwarning(
                "Palabra existente",
                (
                    f"La palabra '{word}' "
                    "ya existe en esta base."
                ),
                parent=self,
            )
            return

        self.word_var.set("")
        self.translation_var.set("")

        self.load_words()

    def delete_word_ui(self) -> None:
        """
        Elimina la palabra seleccionada.
        """
        if self.db_instance is None:
            return

        selection = self.words_tree.selection()

        if not selection:
            messagebox.showwarning(
                "Sin selección",
                "Selecciona una palabra.",
                parent=self,
            )
            return

        item = self.words_tree.item(
            selection[0]
        )

        values = item.get(
            "values",
            [],
        )

        if not values:
            return

        word = str(
            values[0]
        )

        confirmed = messagebox.askyesno(
            "Confirmar eliminación",
            (
                f"¿Eliminar '{word}'?\n\n"
                "También se eliminará todo su "
                "progreso de aprendizaje."
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            deleted = self.db_instance.delete_word(
                word
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo eliminar la palabra:\n\n"
                    f"{error}"
                ),
                parent=self,
            )
            return

        if deleted:
            self.load_words()

    # ------------------------------------------------------------------
    # Importación
    # ------------------------------------------------------------------

    def _import_json(self) -> None:
        """
        Abre el conversor JSON → SQLite.
        """
        try:
            self.converter = open_converter(
                self,
                on_close=self._on_converter_closed,
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo abrir el conversor:\n\n"
                    f"{error}"
                ),
                parent=self,
            )

    def _on_converter_closed(self) -> None:
        """
        Actualiza las bases después de cerrar el conversor.
        """
        self.converter = None
        self._load_databases()

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def _close_current_database(self) -> None:
        """
        Cierra la conexión activa.
        """
        if self.db_instance is not None:
            try:
                self.db_instance.close()
            finally:
                self.db_instance = None

    def _on_close(self) -> None:
        """
        Cierra correctamente la ventana.
        """
        self._close_current_database()
        self.destroy()