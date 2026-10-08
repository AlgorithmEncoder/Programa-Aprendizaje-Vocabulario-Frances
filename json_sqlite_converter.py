"""
Herramienta gráfica independiente para convertir JSON → SQLite.

La lógica de conversión se encuentra en:
    logic.json_sqlite_converter

Este módulo contiene únicamente la interfaz gráfica.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable

from logic.json_sqlite_converter import (
    ConversionResult,
    get_database_path,
    json_to_sqlite,
    load_json,
    validate_words,
)


class JSONtoSQLiteApp:
    """
    Interfaz gráfica del conversor JSON → SQLite.
    """

    def __init__(
        self,
        root: tk.Misc,
        *,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self.root = root
        self.on_close = on_close

        self.root.title(
            "Conversor JSON → SQLite"
        )
        self.root.geometry(
            "700x550"
        )
        self.root.minsize(
            600,
            450,
        )

        self.json_files: list[Path] = []
        self.output_folder: Path | None = None
        self.closed = False

        self.select_button: ttk.Button
        self.folder_button: ttk.Button
        self.convert_button: ttk.Button
        self.progress: ttk.Progressbar
        self.log: tk.Text

        self._create_widgets()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._close,
        )

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """
        Construye la interfaz.
        """
        main = ttk.Frame(
            self.root,
            padding=15,
        )
        main.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            main,
            text="Conversor JSON → SQLite",
            font=("Arial", 18, "bold"),
        ).pack(
            pady=(0, 15),
        )

        ttk.Label(
            main,
            text=(
                "Convierte bases de vocabulario JSON "
                "al formato SQLite utilizado por la aplicación."
            ),
            wraplength=620,
            justify="center",
        ).pack(
            pady=(0, 15),
        )

        button_frame = ttk.Frame(main)
        button_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        self.select_button = ttk.Button(
            button_frame,
            text="Seleccionar JSON",
            command=self.select_json,
        )
        self.select_button.pack(
            side="left",
            padx=(0, 5),
        )

        self.folder_button = ttk.Button(
            button_frame,
            text="Carpeta destino",
            command=self.select_folder,
        )
        self.folder_button.pack(
            side="left",
            padx=5,
        )

        self.convert_button = ttk.Button(
            button_frame,
            text="Convertir",
            command=self.convert_all,
        )
        self.convert_button.pack(
            side="left",
            padx=5,
        )

        ttk.Label(
            main,
            text="Progreso:",
        ).pack(
            anchor="w",
            pady=(5, 3),
        )

        self.progress = ttk.Progressbar(
            main,
            orient="horizontal",
            mode="determinate",
        )
        self.progress.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            main,
            text="Registro:",
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.log = tk.Text(
            main,
            height=20,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.log.pack(
            fill="both",
            expand=True,
        )

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------

    def write_log(
        self,
        text: str,
    ) -> None:
        """
        Añade una línea al registro.
        """
        self.log.config(
            state="normal",
        )

        self.log.insert(
            tk.END,
            text + "\n",
        )

        self.log.see(
            tk.END,
        )

        self.log.config(
            state="disabled",
        )

        self.root.update_idletasks()

    # ------------------------------------------------------------------
    # Selección
    # ------------------------------------------------------------------

    def select_json(self) -> None:
        """
        Selecciona uno o varios JSON.
        """
        files = filedialog.askopenfilenames(
            parent=self.root,
            title="Selecciona archivos JSON",
            filetypes=[
                ("Archivos JSON", "*.json"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not files:
            return

        self.json_files = [
            Path(file)
            for file in files
        ]

        self.write_log(
            (
                "📂 "
                f"{len(self.json_files)} "
                "archivo(s) seleccionado(s)."
            )
        )

    def select_folder(self) -> None:
        """
        Selecciona la carpeta de destino.
        """
        folder = filedialog.askdirectory(
            parent=self.root,
            title="Selecciona carpeta destino",
        )

        if not folder:
            return

        self.output_folder = Path(folder)

        self.write_log(
            f"📁 Carpeta destino: {self.output_folder}"
        )

    # ------------------------------------------------------------------
    # Conversión
    # ------------------------------------------------------------------

    def convert_all(self) -> None:
        """
        Convierte todos los archivos seleccionados.
        """
        if not self.json_files:
            messagebox.showwarning(
                "Aviso",
                (
                    "Selecciona primero uno o varios "
                    "archivos JSON."
                ),
                parent=self.root,
            )
            return

        if self.output_folder is None:
            messagebox.showwarning(
                "Aviso",
                "Selecciona primero una carpeta de destino.",
                parent=self.root,
            )
            return

        self._set_controls_enabled(
            False
        )

        try:
            results = self._convert_selected_files()
            self._show_summary(results)

        finally:
            self._set_controls_enabled(
                True
            )

    def _convert_selected_files(
        self,
    ) -> list[ConversionResult]:
        """
        Realiza las conversiones seleccionadas.
        """
        results: list[ConversionResult] = []

        total_words = 0

        valid_files: list[tuple[Path, int]] = []

        # --------------------------------------------------------------
        # Validación previa
        # --------------------------------------------------------------

        for path in self.json_files:
            try:
                data = load_json(path)
                words = validate_words(data)

                valid_files.append(
                    (
                        path,
                        len(words),
                    )
                )

                total_words += len(words)

            except Exception as error:
                output = get_database_path(
                    path,
                    self.output_folder,
                )

                result = ConversionResult(
                    source=path,
                    output=output,
                    success=False,
                    error=str(error),
                )

                results.append(result)

                self.write_log(
                    (
                        f"❌ {path.name}: "
                        f"{error}"
                    )
                )

        self.progress["value"] = 0
        self.progress["maximum"] = max(
            1,
            total_words,
        )

        if total_words == 0:
            return results

        # --------------------------------------------------------------
        # Conversión
        # --------------------------------------------------------------

        processed_before = 0

        for path, word_count in valid_files:

            output = get_database_path(
                path,
                self.output_folder,
            )

            overwrite = False

            if output.exists():
                overwrite = messagebox.askyesno(
                    "Base existente",
                    (
                        f"La base '{output.name}' ya existe.\n\n"
                        "¿Quieres sobrescribirla?"
                    ),
                    parent=self.root,
                )

                if not overwrite:
                    results.append(
                        ConversionResult(
                            source=path,
                            output=output,
                            success=False,
                            words=0,
                            error=(
                                "Conversión cancelada "
                                "por el usuario."
                            ),
                        )
                    )

                    self.write_log(
                        f"⏭️ Saltada: {path.name}"
                    )

                    # Aunque se haya omitido el archivo,
                    # debemos avanzar visualmente por sus palabras.
                    processed_before += word_count
                    self.progress["value"] = (
                        processed_before
                    )

                    continue

            def progress_callback(
                processed: int,
                total: int,
                base: int = processed_before,
            ) -> None:
                self.progress["value"] = (
                    base + processed
                )
                self.root.update_idletasks()

            result = json_to_sqlite(
                path,
                self.output_folder,
                overwrite=overwrite,
                progress_callback=progress_callback,
            )

            results.append(result)

            if result.success:
                self.write_log(
                    (
                        f"✅ {path.name} → "
                        f"{result.output.name} "
                        f"({result.words} palabras)"
                    )
                )

                processed_before += word_count

            else:
                self.write_log(
                    (
                        f"❌ {path.name}: "
                        f"{result.error}"
                    )
                )

                processed_before += word_count

            self.progress["value"] = (
                processed_before
            )

        return results

    # ------------------------------------------------------------------
    # Resultados
    # ------------------------------------------------------------------

    def _show_summary(
        self,
        results: list[ConversionResult],
    ) -> None:
        """
        Muestra el resultado global.
        """
        successful = [
            result
            for result in results
            if result.success
        ]

        failed = [
            result
            for result in results
            if not result.success
        ]

        converted_words = sum(
            result.words
            for result in successful
        )

        self.write_log("")
        self.write_log(
            "🎉 Proceso finalizado"
        )
        self.write_log(
            f"Archivos procesados: {len(results)}"
        )
        self.write_log(
            f"✅ Correctos: {len(successful)}"
        )
        self.write_log(
            f"❌ Incidencias: {len(failed)}"
        )
        self.write_log(
            f"📚 Palabras convertidas: {converted_words}"
        )

        if failed:
            messagebox.showwarning(
                "Proceso finalizado",
                (
                    "El proceso ha terminado con incidencias.\n\n"
                    f"Correctos: {len(successful)}\n"
                    f"Incidencias: {len(failed)}\n"
                    f"Palabras convertidas: {converted_words}"
                ),
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "Proceso finalizado",
                (
                    "Todos los archivos se han convertido "
                    "correctamente.\n\n"
                    f"Archivos: {len(successful)}\n"
                    f"Palabras: {converted_words}"
                ),
                parent=self.root,
            )

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def _set_controls_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        Activa o desactiva los controles.
        """
        state = (
            "normal"
            if enabled
            else "disabled"
        )

        self.select_button.config(
            state=state
        )
        self.folder_button.config(
            state=state
        )
        self.convert_button.config(
            state=state
        )

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def _close(self) -> None:
        """
        Cierra el conversor y notifica al llamador.
        """
        if self.closed:
            return

        self.closed = True

        if self.on_close is not None:
            self.on_close()

        self.root.destroy()


def open_converter(
    parent: tk.Misc,
    *,
    on_close: Callable[[], None] | None = None,
) -> JSONtoSQLiteApp:
    """
    Abre el conversor como ventana secundaria.

    Esta función es la que utilizará la aplicación principal.
    """
    window = tk.Toplevel(parent)

    return JSONtoSQLiteApp(
        window,
        on_close=on_close,
    )


def main() -> None:
    """
    Ejecuta el conversor como aplicación independiente.
    """
    root = tk.Tk()

    JSONtoSQLiteApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()