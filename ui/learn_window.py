import tkinter as tk
from tkinter import messagebox
import random
from datetime import date
from config.config_loader import cargar_config
from data.sqlite_db import SQLiteDB

class ModoAprender(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Aprender vocabulario")
        self.geometry("500x400")

        self.config_data = cargar_config()

        tk.Label(self, text="Seleccionar base:", font=("Arial", 12)).pack()

        self.db_var = tk.StringVar(self)
        dbs = SQLiteDB.list_databases()
        if not dbs:
            messagebox.showerror("Error", "No hay bases creadas.")
            self.destroy()
            return

        self.db_var.set(dbs[0])
        tk.OptionMenu(self, self.db_var, *dbs).pack(pady=5)

        tk.Button(self, text="Cargar", command=self.cargar_base).pack(pady=10)

        self.frame = tk.Frame(self)
        self.frame.pack(fill="both", expand=True)

    def cargar_base(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.db_name = self.db_var.get()
        self.db = SQLiteDB(self.db_name)

        all_words = self.db.get_all_words()
        self.palabras = []

        for palabra, translation in all_words.items():
            info = self.db.get_word(palabra)
            # Campos extra si no existen
            info.setdefault("estado", "nuevo")
            info.setdefault("aciertos_aprendizaje", 0)
            info.setdefault("intentos_aprendizaje", 0)
            info.setdefault("sesiones_superadas", 0)
            info["mot"] = palabra
            info["traduction"] = info["translation"]
            self.palabras.append(info)

        total = len(self.palabras)
        aprendidas = len([p for p in self.palabras if p["estado"] == "aprendido"])

        tk.Label(self.frame, text=f"Progreso: {aprendidas}/{total}",
                 font=("Arial", 12, "bold")).pack(pady=10)

        self.label = tk.Label(self.frame, text="", font=("Arial", 16))
        self.label.pack(pady=20)

        self.entry = None
        self.botones_opciones = []

        self.boton_accion = tk.Button(self.frame, text="Siguiente", command=self.siguiente)
        self.boton_accion.pack(pady=10)

        self.indice = 0
        self.fase = "mostrar"
        self.seleccion = self.seleccionar_palabras()
        self.mostrar_palabra()

    def seleccionar_palabras(self):
        total = 10
        nuevas = [p for p in self.palabras if p["estado"] == "nuevo"]
        repaso = [p for p in self.palabras if p["estado"] == "aprendiendo"]

        n_nuevas = int(total * self.config_data["porcentaje_nuevas"])
        n_repaso = int(total * self.config_data["porcentaje_repaso"])

        seleccion = []
        if nuevas:
            seleccion += random.sample(nuevas, min(len(nuevas), n_nuevas))
        if repaso:
            seleccion += random.sample(repaso, min(len(repaso), n_repaso))

        resto = total - len(seleccion)
        todas = [p for p in self.palabras if p not in seleccion]
        if todas:
            seleccion += random.sample(todas, min(len(todas), resto))

        random.shuffle(seleccion)
        return seleccion

    def mostrar_palabra(self):
        if self.indice >= len(self.seleccion):
            self.finalizar()
            return

        self.fase = "mostrar"
        self.palabra_actual = self.seleccion[self.indice]

        self.label.config(
            text=f"{self.palabra_actual['mot']} → {self.palabra_actual['traduction']}",
            fg=self.color_estado(self.palabra_actual["estado"])
        )
        self.limpiar_widgets()

    def color_estado(self, estado):
        return {"nuevo": "gray", "aprendiendo": "orange", "aprendido": "green"}.get(estado, "black")

    def mostrar_opciones(self):
        self.fase = "opciones"
        self.label.config(text=f"Selecciona: {self.palabra_actual['mot']}")

        opciones = [self.palabra_actual["traduction"]]
        distractores = [p["traduction"] for p in self.palabras if p != self.palabra_actual]

        opciones += random.sample(distractores, min(len(distractores), self.config_data["opciones_multiple"] - 1))
        random.shuffle(opciones)

        for op in opciones:
            btn = tk.Button(self.frame, text=op, command=lambda o=op: self.respuesta_opcion(o))
            btn.pack()
            self.botones_opciones.append(btn)

    def mostrar_escritura(self):
        self.fase = "escritura"
        self.label.config(text=f"Escribe: {self.palabra_actual['mot']}")
        self.entry = tk.Entry(self.frame)
        self.entry.pack()

    def respuesta_opcion(self, opcion):
        correcto = opcion == self.palabra_actual["traduction"]
        if correcto:
            messagebox.showinfo("Bien", "Correcto ✅")
        else:
            messagebox.showerror("Error", f"Correcta: {self.palabra_actual['traduction']}")
        self.registrar_intento(correcto)
        self.limpiar_widgets()
        self.mostrar_escritura()

    def comprobar_escritura(self):
        texto = self.entry.get().strip().lower()
        correcta = self.palabra_actual["traduction"].lower()
        acierto = texto == correcta
        self.registrar_intento(acierto)
        self.indice += 1
        self.mostrar_palabra()

    def registrar_intento(self, acierto):
        p = self.palabra_actual
        p["intentos_aprendizaje"] += 1
        if acierto:
            p["aciertos_aprendizaje"] += 1

    def siguiente(self):
        if self.fase == "mostrar":
            self.limpiar_widgets()
            self.mostrar_opciones()
        elif self.fase == "escritura":
            self.comprobar_escritura()

    def limpiar_widgets(self):
        for btn in self.botones_opciones:
            btn.destroy()
        self.botones_opciones = []
        if self.entry:
            self.entry.destroy()
            self.entry = None

    def finalizar(self):
        for p in self.seleccion:
            if p["intentos_aprendizaje"] == 0:
                continue

            ratio = p["aciertos_aprendizaje"] / p["intentos_aprendizaje"]

            if ratio >= self.config_data["porcentaje_acierto_minimo"]:
                p["sesiones_superadas"] += 1
                if p["estado"] == "nuevo":
                    p["estado"] = "aprendiendo"
                elif p["estado"] == "aprendiendo":
                    if p["sesiones_superadas"] >= self.config_data["sesiones_para_aprender"]:
                        p["estado"] = "aprendido"

            p["aciertos_aprendizaje"] = 0
            p["intentos_aprendizaje"] = 0

            # Guardar directamente en SQLite
            self.db.update_word(p['mot'],
                                estado=p['estado'],
                                aciertos_aprendizaje=p['aciertos_aprendizaje'],
                                intentos_aprendizaje=p['intentos_aprendizaje'],
                                sesiones_superadas=p['sesiones_superadas'],
                                correct=p.get('correct', 0),
                                incorrect=p.get('incorrect', 0),
                                streak=p.get('streak', 0),
                                interval=p.get('interval', 1),
                                last_seen=p.get('last_seen'))

        self.db.close()
        messagebox.showinfo("Fin", "Sesión completada")
        self.destroy()