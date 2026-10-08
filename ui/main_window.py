import tkinter as tk
from ui.learn_window import ModoAprender
from ui.quiz_window import QuizWindow
from ui.stats_window import StatsWindow
from ui.database_window import ManageDatabaseWindow

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎓 Gestor de Vocabulario Francés")
        self.geometry("350x400")
        self.configure(bg="#F5F5F5")  # Fondo suave

        title = tk.Label(self, text="📚 Aprende Francés (Vocabulario)", font=("Arial", 16, "bold"), bg="#F5F5F5", fg="#333")
        title.pack(pady=20)

        # Contenedor de botones
        frame = tk.Frame(self, bg="#F5F5F5")
        frame.pack(pady=10)
        
        def abrir_modo_aprender():
            ModoAprender(self)

        # Botones estilizados
        btn_style = {"width": 25, "height": 2, "font": ("Arial", 12, "bold")}

        tk.Button(frame, text="Bases de Datos", bg="#4CAF50", fg="white",
                  activebackground="#45A049", **btn_style,
                command=lambda: ManageDatabaseWindow(self)).pack(pady=5)
        
        tk.Button(frame, text="Aprender Vocabulario", bg="#1976D2", fg="white",
                  activebackground="#1976D2", **btn_style,
                command=abrir_modo_aprender).pack(pady=5)

        tk.Button(frame, text="Quizes", bg="#FF9800", fg="white",
                  activebackground="#FB8C00", **btn_style,
                command=lambda: QuizWindow(self)).pack(pady=5)

        tk.Button(frame, text="Estadísticas", bg="#9C27B0", fg="white",
                  activebackground="#7B1FA2", **btn_style,
                command=lambda: StatsWindow(self)).pack(pady=5)