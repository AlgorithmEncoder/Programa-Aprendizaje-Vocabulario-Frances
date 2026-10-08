"""
Ventana principal de la aplicación.

Desde esta ventana se accede a las principales funcionalidades:

- gestión de bases de datos;
- aprendizaje de vocabulario;
- quizzes;
- estadísticas.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.database_window import ManageDatabaseWindow
from ui.learn_window import ModoAprender
from ui.quiz_window import QuizWindow
from ui.stats_window import StatsWindow


class MainWindow(tk.Tk):
    """
    Ventana principal de AprenderFrances.
    """

    APP_TITLE = "🎓 Aprender Francés"
    WINDOW_GEOMETRY = "420x500"

    def __init__(self) -> None:
        super().__init__()

        self.title(self.APP_TITLE)
        self.geometry(self.WINDOW_GEOMETRY)
        self.minsize(380, 450)

        self._configure_style()
        self._create_widgets()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

    # ------------------------------------------------------------------
    # Configuración visual
    # ------------------------------------------------------------------

    def _configure_style(self) -> None:
        """
        Configura los estilos principales de la aplicación.
        """
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Arial", 20, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Arial", 11),
        )

        style.configure(
            "Menu.TButton",
            font=("Arial", 12, "bold"),
            padding=(15, 12),
        )

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """
        Construye la interfaz principal.
        """
        main = ttk.Frame(
            self,
            padding=25,
        )
        main.pack(
            fill="both",
            expand=True,
        )

        # --------------------------------------------------------------
        # Cabecera
        # --------------------------------------------------------------

        ttk.Label(
            main,
            text="📚 Aprender Francés",
            style="Title.TLabel",
            anchor="center",
        ).pack(
            fill="x",
            pady=(10, 5),
        )

        ttk.Label(
            main,
            text="Gestor y entrenador de vocabulario",
            style="Subtitle.TLabel",
            anchor="center",
        ).pack(
            fill="x",
            pady=(0, 25),
        )

        # --------------------------------------------------------------
        # Menú principal
        # --------------------------------------------------------------

        menu_frame = ttk.Frame(main)
        menu_frame.pack(
            fill="both",
            expand=True,
        )

        buttons = (
            (
                "📚 Bases de datos",
                self.open_database_window,
            ),
            (
                "🧠 Aprender vocabulario",
                self.open_learning_window,
            ),
            (
                "📝 Quiz de vocabulario",
                self.open_quiz_window,
            ),
            (
                "📊 Estadísticas",
                self.open_stats_window,
            ),
        )

        for text, command in buttons:
            ttk.Button(
                menu_frame,
                text=text,
                style="Menu.TButton",
                command=command,
            ).pack(
                fill="x",
                pady=6,
            )

        # --------------------------------------------------------------
        # Pie
        # --------------------------------------------------------------

        ttk.Separator(
            main,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=(20, 10),
        )

        ttk.Label(
            main,
            text="AprenderFrances",
            anchor="center",
        ).pack(
            fill="x",
        )

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def open_database_window(self) -> None:
        """
        Abre la ventana de gestión de bases de datos.
        """
        ManageDatabaseWindow(self)

    def open_learning_window(self) -> None:
        """
        Abre el modo de aprendizaje.
        """
        ModoAprender(self)

    def open_quiz_window(self) -> None:
        """
        Abre el sistema de quizzes.
        """
        QuizWindow(self)

    def open_stats_window(self) -> None:
        """
        Abre la ventana de estadísticas.
        """
        StatsWindow(self)

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """
        Cierra la aplicación.
        """
        self.destroy()


def main() -> None:
    """
    Punto de entrada de la interfaz principal.
    """
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()