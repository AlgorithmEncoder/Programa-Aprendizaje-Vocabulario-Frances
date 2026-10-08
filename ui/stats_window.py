"""
Ventana de estadísticas del vocabulario.

Muestra:

- estadísticas globales;
- palabras con peor rendimiento;
- palabras mejor dominadas;
- distribución de palabras por nivel.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from data.sqlite_db import SQLiteDB
from logic.stats import (
    calculate_global_statistics,
    calculate_word_statistics,
    count_words_by_level,
    get_best_mastered_words,
    get_most_failed_words,
)
from utils.helpers import get_level


class StatsWindow(tk.Toplevel):
    """
    Ventana de estadísticas de una base de vocabulario.
    """

    def __init__(
        self,
        parent: tk.Misc,
    ) -> None:
        super().__init__(parent)

        self.title("Estadísticas")
        self.geometry("800x650")
        self.minsize(700, 550)

        self.db: SQLiteDB | None = None
        self.words: list[dict[str, Any]] = []

        self.db_var = tk.StringVar(self)

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
        Construye la ventana.
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
            text="📊 Estadísticas",
            font=("Arial", 18, "bold"),
        ).pack(
            pady=(0, 15),
        )

        # --------------------------------------------------------------
        # Selector
        # --------------------------------------------------------------

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

        self.database_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.db_var,
            state="readonly",
        )
        self.database_combo.pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            selection_frame,
            text="Actualizar",
            command=self.show_stats,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Button(
            selection_frame,
            text="Ver distribución",
            command=self.show_progress_graph,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        # --------------------------------------------------------------
        # Resumen
        # --------------------------------------------------------------

        summary_frame = ttk.LabelFrame(
            main,
            text="Resumen",
            padding=10,
        )
        summary_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        self.summary_label = ttk.Label(
            summary_frame,
            text="Selecciona una base.",
            justify="left",
        )
        self.summary_label.pack(
            anchor="w",
        )

        # --------------------------------------------------------------
        # Rendimiento
        # --------------------------------------------------------------

        performance_frame = ttk.PanedWindow(
            main,
            orient="horizontal",
        )
        performance_frame.pack(
            fill="both",
            expand=True,
        )

        failed_frame = ttk.LabelFrame(
            performance_frame,
            text="🔥 Palabras más falladas",
            padding=10,
        )

        mastered_frame = ttk.LabelFrame(
            performance_frame,
            text="🏆 Palabras mejor dominadas",
            padding=10,
        )

        performance_frame.add(
            failed_frame,
            weight=1,
        )
        performance_frame.add(
            mastered_frame,
            weight=1,
        )

        self.failed_tree = self._create_word_tree(
            failed_frame,
        )

        self.mastered_tree = self._create_word_tree(
            mastered_frame,
        )

    # ------------------------------------------------------------------
    # Treeviews
    # ------------------------------------------------------------------

    def _create_word_tree(
        self,
        parent: ttk.Frame,
    ) -> ttk.Treeview:
        """
        Crea un Treeview para mostrar estadísticas de palabras.
        """
        columns = (
            "word",
            "accuracy",
            "level",
            "interval",
        )

        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=12,
        )

        tree.heading(
            "word",
            text="Palabra",
        )
        tree.heading(
            "accuracy",
            text="Precisión",
        )
        tree.heading(
            "level",
            text="Nivel",
        )
        tree.heading(
            "interval",
            text="Intervalo",
        )

        tree.column(
            "word",
            width=130,
            anchor="w",
        )
        tree.column(
            "accuracy",
            width=80,
            anchor="center",
        )
        tree.column(
            "level",
            width=80,
            anchor="center",
        )
        tree.column(
            "interval",
            width=70,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=tree.yview,
        )

        tree.configure(
            yscrollcommand=scrollbar.set,
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        return tree

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
        self.show_stats()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def _load_words(self) -> bool:
        """
        Carga las palabras de la base seleccionada.
        """
        db_name = self.db_var.get().strip()

        if not db_name:
            return False

        if self.db is not None:
            self.db.close()
            self.db = None

        try:
            self.db = SQLiteDB(db_name=db_name)

            self.words = [
                dict(row)
                for row in self.db.get_all_words()
            ]

        except Exception as error:
            self.db = None

            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los datos:\n\n{error}",
                parent=self,
            )
            return False

        return True

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    def show_stats(self) -> None:
        """
        Calcula y muestra las estadísticas.
        """
        if not self._load_words():
            return

        if not self.words:
            self.summary_label.config(
                text="La base de datos está vacía."
            )

            self._clear_tree(
                self.failed_tree,
            )
            self._clear_tree(
                self.mastered_tree,
            )

            return

        global_stats = calculate_global_statistics(
            self.words,
        )

        learned = sum(
            1
            for word in self.words
            if word.get("estado") == "aprendido"
        )

        learning = sum(
            1
            for word in self.words
            if word.get("estado") == "aprendiendo"
        )

        new = sum(
            1
            for word in self.words
            if word.get("estado") == "nuevo"
        )

        self.summary_label.config(
            text=(
                f"Palabras totales: {global_stats.total_words}\n"
                f"  • Nuevas: {new}\n"
                f"  • Aprendiendo: {learning}\n"
                f"  • Aprendidas: {learned}\n\n"
                f"Aciertos acumulados: {global_stats.total_correct}\n"
                f"Fallos acumulados: {global_stats.total_incorrect}\n"
                f"Intentos totales: {global_stats.total_attempts}\n"
                f"Precisión global: {global_stats.accuracy:.2f} %"
            )
        )

        self._fill_word_tree(
            self.failed_tree,
            get_most_failed_words(
                self.words,
                limit=5,
            ),
        )

        self._fill_word_tree(
            self.mastered_tree,
            get_best_mastered_words(
                self.words,
                limit=5,
            ),
        )

    def _fill_word_tree(
        self,
        tree: ttk.Treeview,
        statistics: list[Any],
    ) -> None:
        """
        Rellena un Treeview con estadísticas de palabras.
        """
        self._clear_tree(tree)

        for item in statistics:
            tree.insert(
                "",
                tk.END,
                values=(
                    item.word,
                    f"{item.accuracy:.1f} %",
                    get_level(item.interval),
                    f"{item.interval} días",
                ),
            )

    @staticmethod
    def _clear_tree(
        tree: ttk.Treeview,
    ) -> None:
        """
        Vacía un Treeview.
        """
        for item in tree.get_children():
            tree.delete(item)

    # ------------------------------------------------------------------
    # Gráfica
    # ------------------------------------------------------------------

    def show_progress_graph(self) -> None:
        """
        Muestra una gráfica sencilla de distribución por niveles.

        Se utiliza Canvas para evitar dependencias externas.
        """
        if not self._load_words():
            return

        if not self.words:
            messagebox.showinfo(
                "Sin datos",
                "La base no contiene palabras.",
                parent=self,
            )
            return

        level_counts = count_words_by_level(
            self.words,
        )

        window = tk.Toplevel(self)
        window.title("Distribución de progreso")
        window.geometry("650x450")
        window.minsize(600, 400)

        canvas_width = 620
        canvas_height = 380

        canvas = tk.Canvas(
            window,
            width=canvas_width,
            height=canvas_height,
            background="white",
            highlightthickness=0,
        )
        canvas.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15,
        )

        levels = list(
            level_counts.keys()
        )
        values = list(
            level_counts.values()
        )

        maximum = max(
            values,
            default=1,
        )

        left = 70
        bottom = canvas_height - 60
        chart_height = canvas_height - 110
        bar_width = 65
        gap = 30

        # Ejes
        canvas.create_line(
            left,
            30,
            left,
            bottom,
            width=2,
        )

        canvas.create_line(
            left,
            bottom,
            canvas_width - 20,
            bottom,
            width=2,
        )

        canvas.create_text(
            canvas_width // 2,
            20,
            text="📊 Distribución de palabras por nivel",
            font=("Arial", 14, "bold"),
        )

        for index, level in enumerate(levels):
            value = values[index]

            x0 = left + 25 + index * (
                bar_width + gap
            )
            x1 = x0 + bar_width

            bar_height = (
                (value / maximum) * chart_height
                if maximum > 0
                else 0
            )

            y1 = bottom - bar_height

            canvas.create_rectangle(
                x0,
                y1,
                x1,
                bottom,
                fill=self._get_level_color(level),
                outline="black",
            )

            canvas.create_text(
                (x0 + x1) // 2,
                y1 - 10,
                text=str(value),
                font=("Arial", 10, "bold"),
            )

            canvas.create_text(
                (x0 + x1) // 2,
                bottom + 15,
                text=level,
                font=("Arial", 9, "bold"),
            )

    @staticmethod
    def _get_level_color(
        level: str,
    ) -> str:
        """
        Devuelve el color visual asociado a un nivel.
        """
        return {
            "Nivel 1": "#ff4d4d",
            "Nivel 2": "#ff9933",
            "Nivel 3": "#ffdd33",
            "Nivel 4": "#66cc66",
            "Nivel 5": "#3399ff",
        }.get(
            level,
            "#999999",
        )

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """
        Cierra la conexión y la ventana.
        """
        if self.db is not None:
            self.db.close()
            self.db = None

        self.destroy()