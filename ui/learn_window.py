"""
Ventana del modo de aprendizaje.

La interfaz se ocupa de mostrar la sesión y recoger las respuestas.
Las reglas de aprendizaje se encuentran en ``logic.learning``.
La persistencia se gestiona mediante ``SQLiteDB``.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from config.config_loader import cargar_config
from data.sqlite_db import SQLiteDB
from logic.learning import (
    evaluate_word_session,
    get_session_size,
    select_learning_words,
)


class ModoAprender(tk.Toplevel):
    """
    Ventana para realizar una sesión de aprendizaje.
    """

    def __init__(
        self,
        master: tk.Misc,
    ) -> None:
        super().__init__(master)

        self.title("Aprender vocabulario")
        self.geometry("600x500")
        self.minsize(500, 400)

        self.config_data = cargar_config()

        self.db_var = tk.StringVar(self)
        self.status_var = tk.StringVar(
            self,
            value="Selecciona una base de datos.",
        )

        self.db: SQLiteDB | None = None
        self.db_name: str | None = None

        self.palabras: list[dict[str, Any]] = []
        self.seleccion: list[dict[str, Any]] = []

        self.palabra_actual: dict[str, Any] | None = None

        self.indice = 0
        self.fase = "idle"

        self.entry: ttk.Entry | None = None
        self.botones_opciones: list[ttk.Button] = []
        self.boton_accion: ttk.Button | None = None

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
        """Construye la interfaz."""
        main = ttk.Frame(
            self,
            padding=20,
        )
        main.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            main,
            text="Modo de aprendizaje",
            font=("Arial", 18, "bold"),
        ).pack(
            pady=(0, 15),
        )

        selection_frame = ttk.Frame(main)
        selection_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Label(
            selection_frame,
            text="Base de datos:",
        ).pack(
            side="left",
            padx=(0, 8),
        )

        self.db_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.db_var,
            state="readonly",
            width=30,
        )
        self.db_combo.pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            selection_frame,
            text="Cargar",
            command=self.cargar_base,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Label(
            main,
            textvariable=self.status_var,
            anchor="center",
        ).pack(
            fill="x",
            pady=(0, 10),
        )

        self.question_frame = ttk.Frame(main)
        self.question_frame.pack(
            fill="both",
            expand=True,
        )

        self.label = ttk.Label(
            self.question_frame,
            text="Carga una base para comenzar.",
            anchor="center",
            justify="center",
            font=("Arial", 18),
        )
        self.label.pack(
            fill="x",
            pady=30,
        )

        self.feedback_var = tk.StringVar(
            self,
            value="",
        )

        ttk.Label(
            self.question_frame,
            textvariable=self.feedback_var,
            anchor="center",
            justify="center",
        ).pack(
            fill="x",
            pady=10,
        )

        self.content_frame = ttk.Frame(
            self.question_frame,
        )
        self.content_frame.pack(
            fill="both",
            expand=True,
        )

        self.boton_accion = ttk.Button(
            self.question_frame,
            text="Siguiente",
            command=self.siguiente,
            state="disabled",
        )
        self.boton_accion.pack(
            pady=10,
        )

    # ------------------------------------------------------------------
    # Bases
    # ------------------------------------------------------------------

    def _load_databases(self) -> None:
        """Carga las bases disponibles."""
        try:
            databases = SQLiteDB.list_databases()

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar las bases:\n\n{error}",
                parent=self,
            )
            return

        self.db_combo["values"] = databases

        if not databases:
            messagebox.showwarning(
                "Sin bases",
                "No hay bases de datos disponibles.",
                parent=self,
            )
            self.destroy()
            return

        self.db_var.set(databases[0])

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def cargar_base(self) -> None:
        """Carga la base seleccionada y prepara una sesión."""
        db_name = self.db_var.get().strip()

        if not db_name:
            messagebox.showwarning(
                "Sin base",
                "Selecciona una base de datos.",
                parent=self,
            )
            return

        self._close_database()

        try:
            self.db = SQLiteDB(
                db_name=db_name,
            )
            self.db_name = db_name

            rows = self.db.get_all_words()

        except Exception as error:
            self.db = None

            messagebox.showerror(
                "Error",
                f"No se pudo cargar la base:\n\n{error}",
                parent=self,
            )
            return

        self.palabras = [
            dict(row)
            for row in rows
        ]

        if not self.palabras:
            self.status_var.set(
                "La base de datos no contiene palabras."
            )
            self.label.config(
                text="No hay palabras disponibles."
            )
            self._set_action_enabled(False)
            return

        self._normalize_word_data()

        self.seleccion = [
            dict(word)
            for word in select_learning_words(
                self.palabras,
                self.config_data,
                total=get_session_size(
                    self.config_data,
                ),
            )
        ]

        if not self.seleccion:
            self.status_var.set(
                "No hay palabras disponibles para aprender."
            )
            self._set_action_enabled(False)
            return

        self.indice = 0

        learned = sum(
            1
            for word in self.palabras
            if word.get("estado") == "aprendido"
        )

        self.status_var.set(
            f"Progreso general: "
            f"{learned}/{len(self.palabras)} aprendidas"
        )

        self._set_action_enabled(True)
        self.mostrar_palabra()

    def _normalize_word_data(self) -> None:
        """Completa registros procedentes de bases antiguas."""
        defaults = {
            "estado": "nuevo",
            "aciertos_aprendizaje": 0,
            "intentos_aprendizaje": 0,
            "sesiones_superadas": 0,
            "correct": 0,
            "incorrect": 0,
            "streak": 0,
            "interval": 0,
            "last_seen": None,
        }

        for word in self.palabras:
            for key, default in defaults.items():
                word.setdefault(
                    key,
                    default,
                )

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------

    def mostrar_palabra(self) -> None:
        """Muestra la palabra actual."""
        self.limpiar_widgets()
        self.feedback_var.set("")

        if self.indice >= len(self.seleccion):
            self.finalizar()
            return

        self.palabra_actual = self.seleccion[
            self.indice
        ]

        word = self.palabra_actual["word"]
        translation = self.palabra_actual["translation"]

        self.fase = "mostrar"

        self.label.config(
            text=f"{word} → {translation}",
        )

        self.boton_accion.config(
            text="Continuar",
            state="normal",
        )

    def mostrar_opciones(self) -> None:
        """Muestra las opciones de traducción."""
        if self.palabra_actual is None:
            return

        self.fase = "opciones"
        self.limpiar_widgets()

        word = self.palabra_actual["word"]
        correct_translation = (
            self.palabra_actual["translation"]
        )

        self.label.config(
            text=f"¿Cuál es la traducción de «{word}»?",
        )

        options = [
            correct_translation,
        ]

        distractors = [
            item["translation"]
            for item in self.palabras
            if item is not self.palabra_actual
            and item.get("translation")
            and item["translation"] != correct_translation
        ]

        desired_options = max(
            2,
            int(
                self.config_data.get(
                    "opciones_multiple",
                    4,
                )
            ),
        )

        options.extend(
            random.sample(
                distractors,
                min(
                    len(distractors),
                    desired_options - 1,
                ),
            )
        )

        random.shuffle(options)

        for option in options:
            button = ttk.Button(
                self.content_frame,
                text=option,
                command=lambda value=option: (
                    self.respuesta_opcion(value)
                ),
            )

            button.pack(
                fill="x",
                padx=40,
                pady=4,
            )

            self.botones_opciones.append(button)

        self.boton_accion.config(
            state="disabled",
        )

    def mostrar_escritura(self) -> None:
        """Muestra la fase de respuesta escrita."""
        if self.palabra_actual is None:
            return

        self.fase = "escritura"
        self.limpiar_widgets()
        self.feedback_var.set("")

        word = self.palabra_actual["word"]

        self.label.config(
            text=f"Escribe la traducción de «{word}»",
        )

        self.entry = ttk.Entry(
            self.content_frame,
            width=40,
        )
        self.entry.pack(
            pady=20,
        )

        self.entry.focus_set()

        self.entry.bind(
            "<Return>",
            lambda _event: self.comprobar_escritura(),
        )

        self.boton_accion.config(
            text="Comprobar",
            state="normal",
        )

    # ------------------------------------------------------------------
    # Respuestas
    # ------------------------------------------------------------------

    def respuesta_opcion(
        self,
        opcion: str,
    ) -> None:
        """Registra una respuesta de selección múltiple."""
        if self.palabra_actual is None:
            return

        correcto = (
            opcion
            == self.palabra_actual["translation"]
        )

        self._registrar_intento(
            correcto
        )

        if correcto:
            self.feedback_var.set(
                "Correcto ✅"
            )
        else:
            self.feedback_var.set(
                "Incorrecto ❌\n"
                f"Respuesta correcta: "
                f"{self.palabra_actual['translation']}"
            )

        self.mostrar_escritura()

    def comprobar_escritura(self) -> None:
        """Comprueba la respuesta escrita."""
        if self.entry is None:
            return

        if self.palabra_actual is None:
            return

        answer = (
            self.entry
            .get()
            .strip()
            .casefold()
        )

        correct_answer = (
            str(
                self.palabra_actual["translation"]
            )
            .strip()
            .casefold()
        )

        if not answer:
            self.feedback_var.set(
                "Escribe una respuesta antes de continuar."
            )
            return

        correct = (
            answer == correct_answer
        )

        self._registrar_intento(
            correct
        )

        if correct:
            self.feedback_var.set(
                "Correcto ✅"
            )
        else:
            self.feedback_var.set(
                "Incorrecto ❌\n"
                f"Respuesta correcta: {correct_answer}"
            )

        self.indice += 1

        self.after(
            500,
            self.mostrar_palabra,
        )

    def _registrar_intento(
        self,
        correct: bool,
    ) -> None:
        """
        Registra un intento de aprendizaje.

        Importante: esta operación NO modifica las estadísticas históricas
        del quiz. Solo modifica los contadores específicos del aprendizaje.
        """
        if self.db is None:
            return

        if self.palabra_actual is None:
            return

        word = self.palabra_actual["word"]

        try:
            saved = self.db.register_learning_attempt(
                word,
                correct,
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo guardar el intento:\n\n"
                    f"{error}"
                ),
                parent=self,
            )
            return

        if not saved:
            return

        self.palabra_actual["intentos_aprendizaje"] = (
            int(
                self.palabra_actual.get(
                    "intentos_aprendizaje",
                    0,
                )
            )
            + 1
        )

        if correct:
            self.palabra_actual["aciertos_aprendizaje"] = (
                int(
                    self.palabra_actual.get(
                        "aciertos_aprendizaje",
                        0,
                    )
                )
                + 1
            )

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def siguiente(self) -> None:
        """Ejecuta la acción correspondiente a la fase."""
        if self.fase == "mostrar":
            self.mostrar_opciones()
            return

        if self.fase == "escritura":
            self.comprobar_escritura()

    def limpiar_widgets(self) -> None:
        """Elimina los controles dinámicos."""
        for button in self.botones_opciones:
            button.destroy()

        self.botones_opciones.clear()

        if self.entry is not None:
            self.entry.destroy()
            self.entry = None

    # ------------------------------------------------------------------
    # Finalización
    # ------------------------------------------------------------------

    def finalizar(self) -> None:
        """Evalúa y guarda la sesión."""
        if self.db is None:
            self._on_close()
            return

        try:
            for word_data in self.seleccion:
                evaluation = evaluate_word_session(
                    word_data,
                    self.config_data,
                )

                word = word_data["word"]

                # La evaluación de la sesión decide el nuevo estado.
                # Los contadores específicos de esta sesión se reinician.
                self.db.update_word(
                    word,
                    estado=evaluation.new_state,
                    sesiones_superadas=(
                        evaluation.sessions_completed
                    ),
                    aciertos_aprendizaje=0,
                    intentos_aprendizaje=0,
                )

            messagebox.showinfo(
                "Sesión completada",
                (
                    "La sesión de aprendizaje ha terminado.\n\n"
                    f"Palabras: {len(self.seleccion)}"
                ),
                parent=self,
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "La sesión terminó, pero no se pudieron "
                    "guardar todos los cambios:\n\n"
                    f"{error}"
                ),
                parent=self,
            )

        finally:
            self._on_close()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _set_action_enabled(
        self,
        enabled: bool,
    ) -> None:
        """Activa o desactiva el botón principal."""
        if self.boton_accion is None:
            return

        self.boton_accion.config(
            state=(
                "normal"
                if enabled
                else "disabled"
            )
        )

    def _close_database(self) -> None:
        """Cierra la conexión activa."""
        if self.db is not None:
            try:
                self.db.close()
            finally:
                self.db = None

    def _on_close(self) -> None:
        """Cierra la ventana."""
        self.limpiar_widgets()
        self._close_database()
        self.destroy()