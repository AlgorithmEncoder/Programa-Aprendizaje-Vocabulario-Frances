import tkinter as tk
from tkinter import messagebox
from data.sqlite_db import SQLiteDB
from utils.helpers import get_level

class StatsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Estadísticas Globales")
        self.geometry("550x550")
        self.configure(bg="#FFFFFF")

        tk.Label(self, text="📊 Estadísticas de tu base", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#333").pack(pady=10)

        # Selector de base
        tk.Label(self, text="Seleccionar base:", font=("Arial", 12), bg="#FFFFFF", fg="#333").pack(pady=5)
        self.db_var = tk.StringVar(self)
        dbs = SQLiteDB.list_databases()
        if not dbs:
            messagebox.showerror("Error", "No hay bases creadas.")
            self.destroy()
            return
        self.db_var.set(dbs[0])
        tk.OptionMenu(self, self.db_var, *dbs).pack(pady=5)

        # Botones
        button_frame = tk.Frame(self, bg="#FFFFFF")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Mostrar estadísticas", font=("Arial", 12, "bold"),
                    bg="#4CAF50", fg="white", activebackground="#45A049",
                    width=20, height=2, command=self.show_stats).pack(side="left", padx=5)

        tk.Button(button_frame, text="Gráfica de progreso", font=("Arial", 12, "bold"),
                    bg="#2196F3", fg="white", activebackground="#1976D2",
                    width=20, height=2, command=self.show_progress_graph).pack(side="left", padx=5)

        # Área de texto para resultados
        self.text_area = tk.Text(self, height=20, width=65, bg="#F0F0F0", fg="#333",
                                bd=2, relief="groove", font=("Arial", 11))
        self.text_area.pack(pady=10)
        self.text_area.config(state="disabled")
    
    def show_stats(self):
        db_name = self.db_var.get()
        db = SQLiteDB(db_name)
        words = db.get_all_words()  # Esto devuelve solo word: translation
        # Para las estadísticas necesitamos todos los campos
        # Alternativa: obtener cada palabra con get_word
        full_words = {}
        for w in words:
            full_words[w] = db.get_word(w)

        if not full_words:
            messagebox.showinfo("Info", "La base está vacía.")
            db.close()
            return

        total_words = len(full_words)
        total_correct = 0
        total_incorrect = 0
        word_stats = []

        for word, info in full_words.items():
            correct = info.get("correct", 0)
            incorrect = info.get("incorrect", 0)
            total_correct += correct
            total_incorrect += incorrect
            word_stats.append((word, correct, incorrect))

        total_attempts = total_correct + total_incorrect
        global_accuracy = (total_correct / total_attempts) * 100 if total_attempts > 0 else 0

        most_failed = sorted(word_stats, key=lambda x: x[2], reverse=True)
        best_mastered = sorted(word_stats, key=lambda x: (x[1], -x[2]), reverse=True)

        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)

        self.text_area.insert(tk.END, "📊 ESTADÍSTICAS GLOBALES\n")
        self.text_area.insert(tk.END, "="*40 + "\n\n")
        self.text_area.insert(tk.END, f"Total palabras: {total_words}\n")
        self.text_area.insert(tk.END, f"Aciertos acumulados: {total_correct}\n")
        self.text_area.insert(tk.END, f"Fallos acumulados: {total_incorrect}\n")
        self.text_area.insert(tk.END, f"Precisión global: {global_accuracy:.2f}%\n\n")

        self.text_area.insert(tk.END, "🔥 Palabras más falladas:\n")
        for word, c, i in most_failed[:5]:
            info = full_words[word]
            interval = info.get("interval", 1)
            level = get_level(interval)
            total = c + i
            precision = (c / total) * 100 if total > 0 else 0
            if i > 0:
                self.text_area.insert(tk.END, f"- {word} | {level} | Precisión: {precision:.1f}% | Intervalo: {interval}\n")

        self.text_area.insert(tk.END, "\n🏆 Palabras mejor dominadas:\n")
        for word, c, i in best_mastered[:5]:
            info = full_words[word]
            interval = info.get("interval", 1)
            level = get_level(interval)
            total = c + i
            precision = (c / total) * 100 if total > 0 else 0
            if c > 0:
                self.text_area.insert(tk.END, f"- {word} | {level} | Precisión: {precision:.1f}% | Intervalo: {interval}\n")

        self.text_area.config(state="disabled")
        db.close()
    
    def show_progress_graph(self):
        db_name = self.db_var.get()
        db = SQLiteDB(db_name)
        words = db.get_all_words()
        full_words = {w: db.get_word(w) for w in words}

        level_counts = {"Nivel 1":0, "Nivel 2":0, "Nivel 3":0, "Nivel 4":0, "Nivel 5":0}
        for info in full_words.values():
            interval = info.get("interval", 1)
            if interval <= 1:
                level_counts["Nivel 1"] += 1
            elif interval <= 3:
                level_counts["Nivel 2"] += 1
            elif interval <= 6:
                level_counts["Nivel 3"] += 1
            elif interval <= 12:
                level_counts["Nivel 4"] += 1
            else:
                level_counts["Nivel 5"] += 1

        win = tk.Toplevel(self)
        win.title("Distribución de Progreso")
        canvas_width, canvas_height = 500, 350
        c = tk.Canvas(win, width=canvas_width, height=canvas_height, bg="white")
        c.pack()

        levels = list(level_counts.keys())
        values = list(level_counts.values())
        max_value = max(values) if values else 1

        bar_width = 60
        gap = 25
        left_margin = 60
        bottom_margin = 50
        colors = ["#ff4d4d", "#ff9933", "#ffdd33", "#66cc66", "#3399ff"]

        for i, val in enumerate(values):
            x0 = left_margin + i * (bar_width + gap)
            y0 = canvas_height - bottom_margin
            x1 = x0 + bar_width
            y1 = y0 - (val / max_value) * (canvas_height - bottom_margin - 20)
            c.create_rectangle(x0, y1, x1, y0, fill=colors[i], outline="black", width=1)
            c.create_text((x0 + x1)//2, y1 - 10, text=str(val), font=("Arial", 10, "bold"), anchor="s")
            c.create_text((x0 + x1)//2, y0 + 15, text=levels[i], font=("Arial", 10, "bold"), anchor="n")

        c.create_line(left_margin-10, 10, left_margin-10, canvas_height - bottom_margin, width=2)
        c.create_line(left_margin-10, canvas_height - bottom_margin, canvas_width - 10, canvas_height - bottom_margin, width=2)
        c.create_text(canvas_width//2, 20, text="📊 Distribución de palabras por nivel", font=("Arial", 14, "bold"), fill="black")
        db.close()