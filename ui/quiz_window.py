import tkinter as tk
from tkinter import messagebox
import random
from datetime import datetime, date
from data.sqlite_db import SQLiteDB
from logic.quiz_logic import get_adaptive_words, get_review_words

class QuizWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Quiz de Francés")
        self.geometry("500x500")
        self.configure(bg="#F5F5F5")

        tk.Label(self, text="📝 Quiz de Vocabulario", font=("Arial", 16, "bold"),
                 bg="#F5F5F5", fg="#333").pack(pady=15)

        tk.Label(self, text="Seleccionar base:", font=("Arial", 12), bg="#F5F5F5", fg="#333").pack(pady=5)
        self.db_var = tk.StringVar(self)
        dbs = SQLiteDB.list_databases()
        if not dbs:
            messagebox.showerror("Error", "No hay bases creadas.")
            self.destroy()
            return
        self.db_var.set(dbs[0])
        tk.OptionMenu(self, self.db_var, *dbs).pack(pady=5)

        tk.Label(self, text="Modo de juego:", font=("Arial", 12), bg="#F5F5F5", fg="#333").pack(pady=10)
        self.mode = tk.StringVar(value="normal")
        modes = [
            ("Francés → Español", "normal"),
            ("Español → Francés", "inverse"),
            ("🧠 Repaso Mixto Inteligente", "smart_review"),
            ("🔥 Palabras problemáticas", "review"),
            ("🚀 Modo Adaptativo Inteligente", "adaptive")
        ]
        for text, value in modes:
            tk.Radiobutton(self, text=text, variable=self.mode, value=value,
                           font=("Arial", 12), bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x", padx=20)

        self.review_count = tk.IntVar(value=10)
        count_frame = tk.Frame(self, bg="#F5F5F5")
        count_frame.pack(pady=10)
        tk.Label(count_frame, text="Cantidad de palabras:", font=("Arial", 12), bg="#F5F5F5", fg="#333").pack(side="left", padx=5)
        for n in [10, 15, 20]:
            tk.Radiobutton(count_frame, text=str(n), variable=self.review_count, value=n,
                           font=("Arial", 12), bg="#F5F5F5", fg="#333").pack(side="left", padx=5)

        tk.Button(self, text="Iniciar Quiz", font=("Arial", 12, "bold"),
                  bg="#4CAF50", fg="white", activebackground="#45A049",
                  width=20, height=2, command=self.start_quiz).pack(pady=15)

        self.question_frame = tk.Frame(self, bg="#F5F5F5")
        self.question_frame.pack(pady=10, fill="both", expand=True)

    def start_quiz(self):
        self.db_name = self.db_var.get()
        self.db = SQLiteDB(self.db_name)
        all_words = self.db.get_all_words()
        self.words = {w: self.db.get_word(w) for w in all_words}

        palabras_aprendidas = [(w, info) for w, info in self.words.items() if info.get("estado") == "aprendido"]
        if not palabras_aprendidas:
            messagebox.showwarning("Aviso", "Primero debes aprender palabras.")
            return

        self.words = dict(palabras_aprendidas)

        if self.mode.get() == "adaptive":
            self.questions = get_adaptive_words(self.words)
        elif self.mode.get() in ("review", "smart_review"):
            self.questions = get_review_words(self.words, self.review_count.get())
        else:
            self.questions = list(self.words.items())
            random.shuffle(self.questions)

        self.index = 0
        self.correct = 0
        self.incorrect_words = []

        self.ask_question()

    def ask_question(self):
        if self.index >= len(self.questions):
            self.finish_quiz()
            return

        self.clear_window()
        self.current_word, self.current_data = self.questions[self.index]

        if self.mode.get() in ("normal", "review"):
            question_text = self.current_word
            self.current_direction = "forward"
        elif self.mode.get() == "inverse":
            question_text = self.current_data["translation"]
            self.current_direction = "inverse"
        elif self.mode.get() == "smart_review":
            self.current_direction = random.choice(["forward", "inverse"])
            question_text = self.current_word if self.current_direction == "forward" else self.current_data["translation"]

        tk.Label(self, text=f"Traduce: {question_text}", font=("Arial", 14)).pack(pady=20)

        self.answer_entry = tk.Entry(self)
        self.answer_entry.pack()
        self.answer_entry.focus()
        self.answer_entry.bind("<Return>", lambda e: self.check_answer())
        tk.Button(self, text="Responder", command=self.check_answer).pack(pady=5)

    def check_answer(self):
        user_answer = self.answer_entry.get().strip().lower()
        correct_answer = (self.current_data["translation"].lower() if self.current_direction == "forward"
                        else self.current_word.lower())
        info = self.current_data

        if user_answer == correct_answer:
            self.correct += 1
            info['correct'] += 1
            info['streak'] += 1
            info['interval'] = max(1, int(info['interval'] * 1.8))
        else:
            info['incorrect'] += 1
            info['streak'] = 0
            info['interval'] = 1
            self.incorrect_words.append(self.current_word)

        info['last_seen'] = str(date.today())

        # Corregido: eliminamos 'word' de los kwargs para evitar TypeError
        info_to_update = info.copy()
        info_to_update.pop("word", None)

        self.db.update_word(self.current_word, **info_to_update)

        self.index += 1
        self.ask_question()

    def finish_quiz(self):
        total = len(self.questions)
        percentage = (self.correct / total) * 100 if total > 0 else 0
        resumen = f"📊 RESULTADOS FINALES\n\nAciertos: {self.correct}/{total}\nPrecisión: {percentage:.2f}%\n\n"

        if self.incorrect_words:
            resumen += "Palabras falladas:\n" + "\n".join(f"- {w}" for w in self.incorrect_words)

        messagebox.showinfo("Quiz Finalizado", resumen)
        self.db.close()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()