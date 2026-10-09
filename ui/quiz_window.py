"""
Ventana de quizzes de vocabulario.

La interfaz permite seleccionar una base, un modo de quiz y el número
de preguntas.

La lógica de selección se encuentra en ``logic.quiz_logic`` y la
persistencia de resultados en ``data.sqlite_db``.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from data.sqlite_db import SQLiteDB
from logic.quiz_logic import (
    get_adaptive_words,
    get_review_words,
)


class QuizWindow(tk.Toplevel):
    """
    Ventana principal del sistema de quizzes.
    """

    MODES = (
        ("Francés → Español", "normal"),
        ("Español → Francés", "inverse"),
        ("🧠 Repaso mixto inteligente", "smart_review"),
        ("🔥 Palabras problemáticas", "review"),
        ("🚀 Modo adaptativo inteligente", "adaptive"),
    )

    QUESTION_COUNTS = (10, 15, 20)

    def __init__(
        self,
        parent: tk.Misc,
    ) -> None:
        super().__init__(parent)

        self.title("Quiz de Francés")
        self.geometry("600x600")
        self.minsize(500, 500)

        self.db: SQLiteDB | None = None
        self.db_name: str | None = None

        self.words: dict[str, dict[str, Any]] = {}
        self.questions: list[tuple[str, dict[str, Any]]] = []

        self.index = 0
        self.correct = 0
        self.incorrect_words: list[str] = []

        self.current_word = ""
        self.current_data: dict[str, Any] | None = None
        self.current_direction = "forward"
        self.answer_entry: ttk.Entry | None = None
        self.answer_checked = False

        self.db_var = tk.StringVar(self)
        self.mode = tk.StringVar(
            self,
            value="normal",
        )
        self.question_count = tk.IntVar(
            self,
            value=10,
        )

        self.status_var = tk.StringVar(
            self,
            value="Selecciona una base y comienza el quiz.",
        )

        self._create_widgets()
        self._load_databases()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

    # ------------------------------------------------------------------
    # Interfaz inicial
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """
        Construye la interfaz inicial.
        """
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
            text="📝 Quiz de vocabulario",
            font=("Arial", 18, "bold"),
        ).pack(
            pady=(0, 15),
        )

        # --------------------------------------------------------------
        # Base
        # --------------------------------------------------------------

        database_frame = ttk.Frame(main)
        database_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Label(
            database_frame,
            text="Base de datos:",
        ).pack(
            side="left",
            padx=(0, 8),
        )

        self.database_combo = ttk.Combobox(
            database_frame,
            textvariable=self.db_var,
            state="readonly",
        )
        self.database_combo.pack(
            side="left",
            fill="x",
            expand=True,
        )

        # --------------------------------------------------------------
        # Modo
        # --------------------------------------------------------------

        ttk.Label(
            main,
            text="Modo de juego:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        mode_frame = ttk.Frame(main)
        mode_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        for text, value in self.MODES:
            ttk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.mode,
                value=value,
            ).pack(
                fill="x",
                pady=2,
            )

        # --------------------------------------------------------------
        # Número de preguntas
        # --------------------------------------------------------------

        count_frame = ttk.Frame(main)
        count_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Label(
            count_frame,
            text="Cantidad de palabras:",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        for number in self.QUESTION_COUNTS:
            ttk.Radiobutton(
                count_frame,
                text=str(number),
                variable=self.question_count,
                value=number,
            ).pack(
                side="left",
                padx=5,
            )

        # --------------------------------------------------------------
        # Inicio
        # --------------------------------------------------------------

        ttk.Button(
            main,
            text="Iniciar quiz",
            command=self.start_quiz,
        ).pack(
            pady=10,
        )

        ttk.Label(
            main,
            textvariable=self.status_var,
            anchor="center",
            justify="center",
        ).pack(
            fill="x",
            pady=10,
        )

        # --------------------------------------------------------------
        # Área del quiz
        # --------------------------------------------------------------

        self.quiz_frame = ttk.Frame(main)
        self.quiz_frame.pack(
            fill="both",
            expand=True,
            pady=10,
        )

    # ------------------------------------------------------------------
    # Bases
    # ------------------------------------------------------------------

    def _load_databases(self) -> None:
        """
        Carga las bases disponibles.
        """
        try:
            databases = SQLiteDB.list_databases()

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar las bases:\n\n{error}",
                parent=self,
            )
            return

        self.database_combo["values"] = databases

        if not databases:
            messagebox.showwarning(
                "Sin bases",
                "No hay bases de datos creadas.",
                parent=self,
            )
            self.destroy()
            return

        self.db_var.set(databases[0])

    # ------------------------------------------------------------------
    # Inicio del quiz
    # ------------------------------------------------------------------

    def start_quiz(self) -> None:
        """
        Inicializa una nueva sesión de quiz.
        """
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
            self.db = SQLiteDB(db_name=db_name)
            self.db_name = db_name

            rows = self.db.get_all_words()

            all_words = {
                row["word"]: dict(row)
                for row in rows
                if row.get("estado") == "aprendido"
            }

        except Exception as error:
            self.db = None

            messagebox.showerror(
                "Error",
                f"No se pudo abrir la base:\n\n{error}",
                parent=self,
            )
            return

        if not all_words:
            messagebox.showwarning(
                "Sin palabras",
                "Primero debes aprender algunas palabras.",
                parent=self,
            )
            self._close_database()
            return

        self.words = all_words

        try:
            self.questions = self._select_questions()

        except ValueError as error:
            messagebox.showwarning(
                "Quiz no disponible",
                str(error),
                parent=self,
            )
            return

        if not self.questions:
            messagebox.showwarning(
                "Sin preguntas",
                "No hay suficientes palabras para iniciar el quiz.",
                parent=self,
            )
            return

        self.index = 0
        self.correct = 0
        self.incorrect_words = []

        self.status_var.set(
            f"Pregunta 1 de {len(self.questions)}"
        )

        self._disable_setup()
        self.ask_question()

    def _select_questions(
        self,
    ) -> list[tuple[str, dict[str, Any]]]:
        """
        Selecciona las preguntas según el modo configurado.
        """
        count = self.question_count.get()
        mode = self.mode.get()

        if mode == "adaptive":
            questions = get_adaptive_words(
                self.words,
            )
            questions = questions[:count]

        elif mode in ("review", "smart_review"):
            questions = get_review_words(
                self.words,
                count,
            )

        else:
            questions = list(
                self.words.items()
            )

            random.shuffle(questions)
            questions = questions[:count]

        return questions

    # ------------------------------------------------------------------
    # Pregunta
    # ------------------------------------------------------------------

    def ask_question(self) -> None:
        """
        Muestra la pregunta actual.
        """
        if self.index >= len(self.questions):
            self.finish_quiz()
            return

        self._clear_quiz_frame()

        self.current_word, self.current_data = (
            self.questions[self.index]
        )

        mode = self.mode.get()

        if mode in ("normal", "review", "adaptive"):
            self.current_direction = "forward"
            question_text = self.current_word

        elif mode == "inverse":
            self.current_direction = "inverse"
            question_text = self.current_data["translation"]

        else:
            self.current_direction = random.choice(
                ("forward", "inverse")
            )

            if self.current_direction == "forward":
                question_text = self.current_word
            else:
                question_text = self.current_data["translation"]

        ttk.Label(
            self.quiz_frame,
            text=(
                f"Pregunta {self.index + 1} "
                f"de {len(self.questions)}"
            ),
            font=("Arial", 10),
        ).pack(
            pady=(0, 20),
        )

        ttk.Label(
            self.quiz_frame,
            text=f"Traduce: {question_text}",
            font=("Arial", 18, "bold"),
            anchor="center",
            justify="center",
        ).pack(
            pady=20,
        )

        self.answer_entry = ttk.Entry(
            self.quiz_frame,
            width=40,
            justify="center",
        )
        self.answer_entry.pack(
            pady=10,
        )

        self.answer_entry.focus_set()

        self.answer_entry.bind(
            "<Return>",
            lambda _event: self.check_answer(),
        )

        ttk.Button(
            self.quiz_frame,
            text="Responder",
            command=self.check_answer,
        ).pack(
            pady=10,
        )

        self.answer_checked = False

    def check_answer(self) -> None:
        """
        Comprueba la respuesta y guarda el resultado.
        """
        if self.answer_checked:
            return

        if self.answer_entry is None:
            return

        if self.current_data is None:
            return

        user_answer = (
            self.answer_entry
            .get()
            .strip()
            .casefold()
        )

        if not user_answer:
            messagebox.showwarning(
                "Respuesta vacía",
                "Escribe una respuesta antes de continuar.",
                parent=self,
            )
            return

        if self.current_direction == "forward":
            correct_answer = str(
                self.current_data["translation"]
            ).strip().casefold()
        else:
            correct_answer = (
                self.current_word
                .strip()
                .casefold()
            )

        is_correct = user_answer == correct_answer

        self.answer_checked = True

        try:
            if self.db is None:
                raise RuntimeError(
                    "No hay una base de datos abierta."
                )

            self.db.register_answer(
                self.current_word,
                is_correct,
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                (
                    "No se pudo guardar el resultado:\n\n"
                    f"{error}"
                ),
                parent=self,
            )
            return

        if is_correct:
            self.correct += 1
            feedback = "Correcto ✅"

        else:
            self.incorrect_words.append(
                self.current_word
            )

            feedback = (
                "Incorrecto ❌\n\n"
                f"Respuesta correcta: {correct_answer}"
            )

        self._clear_quiz_frame()

        ttk.Label(
            self.quiz_frame,
            text=feedback,
            font=("Arial", 16, "bold"),
            justify="center",
            anchor="center",
        ).pack(
            expand=True,
            pady=40,
        )

        self.index += 1

        if self.index < len(self.questions):
            ttk.Button(
                self.quiz_frame,
                text="Siguiente",
                command=self.ask_question,
            ).pack(
                pady=20,
            )

            self.status_var.set(
                f"Pregunta {self.index + 1} "
                f"de {len(self.questions)}"
            )

        else:
            ttk.Button(
                self.quiz_frame,
                text="Ver resultados",
                command=self.finish_quiz,
            ).pack(
                pady=20,
            )

            self.status_var.set(
                "Quiz completado."
            )

    # ------------------------------------------------------------------
    # Finalización
    # ------------------------------------------------------------------

    def finish_quiz(self) -> None:
        """
        Muestra el resultado final del quiz.
        """
        total = len(self.questions)

        percentage = (
            (self.correct / total) * 100
            if total > 0
            else 0.0
        )

        lines = [
            "📊 Resultados finales",
            "",
            f"Aciertos: {self.correct}/{total}",
            f"Precisión: {percentage:.2f} %",
        ]

        if self.incorrect_words:
            lines.extend(
                [
                    "",
                    "Palabras falladas:",
                    *(
                        f"• {word}"
                        for word in self.incorrect_words
                    ),
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "¡No has fallado ninguna palabra! 🎉",
                ]
            )

        messagebox.showinfo(
            "Quiz finalizado",
            "\n".join(lines),
            parent=self,
        )

        self._clear_quiz_frame()
        self._enable_setup()

    # ------------------------------------------------------------------
    # Interfaz auxiliar
    # ------------------------------------------------------------------

    def _clear_quiz_frame(self) -> None:
        """
        Elimina únicamente los widgets del área del quiz.
        """
        for widget in self.quiz_frame.winfo_children():
            widget.destroy()

    def _disable_setup(self) -> None:
        """
        Desactiva temporalmente la configuración durante el quiz.
        """
        self.database_combo.config(
            state="disabled",
        )

    def _enable_setup(self) -> None:
        """
        Reactiva la configuración.
        """
        self.database_combo.config(
            state="readonly",
        )

        self.status_var.set(
            "Puedes iniciar otro quiz."
        )

    def _close_database(self) -> None:
        """
        Cierra la conexión activa.
        """
        if self.db is not None:
            try:
                self.db.close()
            finally:
                self.db = None

    def _on_close(self) -> None:
        """
        Cierra correctamente la ventana.
        """
        self._close_database()
        self.destroy()