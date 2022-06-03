import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkcalendar import Calendar

from os import remove

import mysql.connector
from mysql.connector import Error

import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class Contabilidad:

    db_name = "mysql-python-telegram-excel"

    def __init__(self, window):

        # borrando archivos
        try:
            pdf = open("REPORTE.pdf")
            pdf.close()
            remove("REPORTE.pdf")
        except FileNotFoundError:
            pass
        try:
            imagen_barras = open("barras.png")
            imagen_barras.close()
            remove("barras.png")
        except FileNotFoundError:
            pass
        try:
            imagen_torta = open("torta.png")
            imagen_torta.close()
            remove("torta.png")
        except FileNotFoundError:
            pass

        # Creando ventana principal
        self.wind = window
        self.wind.title("Contabilidad")

        frame = LabelFrame(self.wind, text="Registrar movimiento (ingreso o gasto)")
        frame.grid(row=0, column=0, columnspan=7, pady=20)

        # ------   Descripcion ------
        Label(frame, text="Descripcion: ").grid(row=1, column=0)
        self.description = Entry(frame)
        self.description.focus()
        self.description.grid(row=1, column=1)

        # ------   tipo ------
        Label(frame, text="Tipo: ").grid(row=3, column=0)
        self.type = ttk.Combobox(frame, state="readonly", values=["ingreso", "gasto"])
        self.type.grid(row=3, column=1)

        # ------   valor ------
        Label(frame, text="Valor: ").grid(row=5, column=0)
        self.price = Entry(frame)
        self.price.grid(row=5, column=1)

        # ------   fecha ------
        Label(frame, text="Fecha: ").grid(row=7, column=0)
        self.date = Calendar(frame, selectmode="day", year=2020, month=5, day=22)
        self.date.grid(row=7, column=1)

        # ------   mensaje de salida ------
        self.mensaje = Label(frame, text="", fg="red")
        self.mensaje.grid(row=8, column=0, columnspan=2, sticky=W + E)

        # ------   tabla de movimientos ------
        self.tree = ttk.Treeview(height=10, columns=("#1", "#2", "#3", "#4"))
        self.tree.grid(row=4, column=0, columnspan=5)
        self.tree.heading("#0", text="Codigo", anchor=CENTER)
        self.tree.heading("#1", text="Descripcion", anchor=CENTER)
        self.tree.heading("#2", text="Tipo", anchor=CENTER)
        self.tree.heading("#3", text="Valor", anchor=CENTER)
        self.tree.heading("#4", text="Fecha", anchor=CENTER)

        # ------   botones ------
        ttk.Button(frame, text="Guardar", command=self.agregar_movimiento).grid(
            row=9, columnspan=2, sticky=W + E
        )
        ttk.Button(text="Editar", command=self.editar_movimiento).grid(
            row=9, column=0, columnspan=2, sticky=W + E
        )
        ttk.Button(text="Eliminar", command=self.borrar_movimiento).grid(
            row=9, column=3, columnspan=2, sticky=E + W
        )
        ttk.Button(text="Torta", command=self.reporte_torta).grid(
            row=10, column=0, columnspan=1, sticky=W + E
        )
        ttk.Button(text="Barras", command=self.reporte_barras).grid(
            row=10, column=2, columnspan=1, sticky=E + W
        )
        ttk.Button(text="Pdf", command=self.reporte_pdf).grid(
            row=10, column=4, columnspan=1, sticky=E + W
        )
        # ------   llenado de filas ------
        self.obtener_movimientos()

    def correr_consulta(self, consulta, parameteros=()):
        try:
            result = ""
            connection = mysql.connector.connect(
                host="localhost", database=self.db_name, user="root", password="1234"
            )
            if connection.is_connected():
                db_Info = connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                cursor = connection.cursor(buffered=True, dictionary=True)
                cursor.execute(consulta, parameteros)
                result = cursor.fetchall()
        except Error as e:
            print("Error Mientras conectabas con la bases de datos MySQL", e)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")
                return result

    def obtener_movimientos(self):
        # limpiando la tabla
        registros = self.tree.get_children()
        for elemento in registros:
            self.tree.delete(elemento)

        # consultando datos
        consulta = "SELECT * FROM movimientos ORDER BY fecha DESC"
        movimientos = self.correr_consulta(consulta)

        # llenando la tabla
        if movimientos:
            for movimiento in movimientos:
                self.tree.insert(
                    "",
                    tk.END,
                    text=movimiento["id"],
                    values=(
                        movimiento["descripcion"],
                        movimiento["tipo"],
                        movimiento["valor"],
                        movimiento["fecha"],
                    ),
                )

    def validaciones(self):
        return (
            len(self.descripcion.get()) != 0
            and len(self.tipo.get()) != 0
            and len(self.fecha.get()) != 0
            and len(self.valor.get()) != 0
        )

    def limpiar_formulario(self):
        self.descripcion.delete(0, END)
        self.tipo.delete(0, END)
        self.valor.delete(0, END)
        self.fecha.delete(0, END)

    def agregar_movimiento(self):
        if self.validaciones():
            consulta = "INSERT INTO movimientos VALUES(NULL, ?, ?, ?, ?)"
            parametros = (
                self.descripcion.get(),
                self.tipo.get(),
                self.valor.get(),
                self.fecha.get(),
            )
            self.correr_consulta(consulta, parametros)
            self.mensaje[
                "text"
            ] = f"El {self.tipo.get()} se ha GUARDADO satisfactoriamente."
            self.limpiar_formulario()
        else:
            self.mensaje["text"] = "TODOS LOS CAMPOS SON REQUERIDOS"
        self.obtener_movimientos()

    def borrar_movimiento(self):
        self.mensaje["text"] = ""
        try:
            id = self.tree.item(self.tree.selection())["text"][0]
        except IndexError:
            self.mensaje["text"] = "Por favor SELECCIONA un movimiento"
            return
        self.mensaje["text"] = ""
        consulta = "DELETE FROM movimiento WHERE id = ?"
        self.correr_consulta(consulta, (id,))
        self.mensaje[
            "text"
        ] = f"El movimiento seleccionado ha sido BORRADO satisfactoriamente"
        self.obtener_movimientos()

    def editar_movimiento(self):
        self.mensaje["text"] = ""
        try:
            item = self.tree.item(self.tree.selection())
        except IndexError:
            self.mensaje["text"] = "Por favor SELECCIONA un movimiento"
            return
        self.mensaje["text"] = ""
        id = item["text"]
        descripcion = item["values"][0]
        tipo = item["values"][1]
        valor = item["values"][2]
        fecha = item["values"][3]

        # ventana para editar movimiento
        self.ventana_editar = Toplevel()
        self.ventana_editar.title("Editar movimiento")

        # datos
        # ------   Descripcion antigua ------
        Label(self.ventana_editar, text="descripcion anterior").grid(row=0, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=descripcion),
            state="readonly",
        ).grid(row=0, column=1)
        # ------   Descripcion nueva ------
        Label(self.ventana_editar, text="Descripcion: ").grid(row=1, column=0)
        description = Entry(self.ventana_editar)
        description.focus()
        description.grid(row=1, column=1)

        # ------   tipo antiguo ------
        Label(self.ventana_editar, text="tipo anterior").grid(row=2, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=tipo),
            state="readonly",
        ).grid(row=2, column=1)
        # ------   tipo nuevo ------
        Label(self.ventana_editar, text="Tipo: ").grid(row=3, column=0)
        type = ttk.Combobox(
            self.ventana_editar, state="readonly", values=["Ingreso", "Gasto"]
        )
        type.grid(row=3, column=1)

        # ------   valor antiguo ------
        Label(self.ventana_editar, text="valor anterior").grid(row=4, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=valor),
            state="readonly",
        ).grid(row=4, column=1)
        # ------   valor nuevo ------
        Label(self.ventana_editar, text="Valor: ").grid(row=5, column=0)
        price = Entry(self.ventana_editar)
        price.grid(row=5, column=1)

        # ------   fecha antigua ------
        Label(self.ventana_editar, text="fecha anterior").grid(row=6, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=fecha),
            state="readonly",
        ).grid(row=6, column=1)
        # ------   fecha nueva ------
        Label(self.ventana_editar, text="Fecha: ").grid(row=7, column=0)
        date = Calendar(
            self.ventana_editar, selectmode="day", year=2020, month=5, day=22
        )
        date.grid(row=7, column=1)

        if len(description.get()) == 0:
            description = descripcion
        if len(type.get()) == 0:
            type = tipo
        if len(price.get()) == 0:
            price = valor
        if str(date.get()) == "22/5/20":
            date = fecha

        datos_nuevos = {
            "descripcion": description,
            "tipo": type,
            "valor": price,
            "fecha": date,
        }

        Button(
            self.ventana_editar,
            text="Actualizar",
            command=lambda: self.actualizar(datos_nuevos, id),
        ).grid(row=8, column=0, sticky=W)

    def actualizar(self, datos_nuevos, id):
        consulta = "UPDATE movimientos SET descripcion = ?, tipo = ?, valor = ?, fecha = ? WHERE id = ?"
        parametros = (
            datos_nuevos["descripcion"],
            datos_nuevos["tipo"],
            datos_nuevos["valor"],
            datos_nuevos["fecha"],
            id,
        )
        self.correr_consulta(consulta, parametros)
        self.ventana_editar.destroy()
        self.mensaje["text"] = f"El movimiento ha sido ACTUALIZADO satisfactoriamente"
        self.obtener_movimientos()

    # ------   REPORTES ------
    def consulta_ingresos(self):
        consulta_ingresos = "SELECT SUM(valor) FROM movimientos WHERE tipo = 'ingreso'"
        ingresos = self.correr_consulta(consulta_ingresos)
        ingresos = ingresos[0]["SUM(valor)"]
        if not ingresos:
            ingresos = 0
        return ingresos

    def consulta_gastos(self):
        consulta_gastos = "SELECT SUM(valor) FROM movimientos WHERE tipo = 'gasto'"
        gastos = self.correr_consulta(consulta_gastos)
        gastos = gastos[0]["SUM(valor)"]
        if not gastos:
            gastos = 0
        return gastos

    def reporte_torta(self):
        ingresos = self.consulta_ingresos()
        gastos = self.consulta_gastos()

        # Creating dataset
        movimientos = ["Ingresos", "Gastos"]

        datos = [ingresos, gastos]

        # Creating plot
        fig = plt.figure(figsize=(10, 7))
        plt.pie(datos, labels=movimientos, autopct="%1.1f%%")
        plt.legend(title="Movimientos", loc="upper left")

        ## Guardar imagen del grafico
        plt.savefig("torta.png", bbox_inches="tight")

        # show plot
        plt.show()

    def reporte_barras(self):
        ingresos = self.consulta_ingresos()
        gastos = self.consulta_gastos()

        ## Declaramos valores para el eje x
        eje_x = ["Ingresos", "Gastos"]

        ## Declaramos valores para el eje y
        eje_y = [ingresos, gastos]

        ## Creamos Gráfica
        plt.bar(eje_x, eje_y)

        ## Legenda en el eje y
        plt.ylabel("Cantidad")

        ## Legenda en el eje x
        plt.xlabel("movimientos")

        ## Título de Gráfica
        plt.title("Grafico de gastos e ingresos")

        ## Guardar imagen del grafico
        plt.savefig("barras.png", bbox_inches="tight")

        ## Mostramos Gráfica
        plt.show()

    def reporte_pdf(self):
        my_canvas = canvas.Canvas("REPORTE.pdf", pagesize=letter)
        try:
            imagen_barras = open("barras.png")
            my_canvas.drawString(100, 760, "GRAFICO BARRAS")
            my_canvas.drawImage("barras.png", 100, 500, width=250, height=250)
            imagen_barras.close()
        except FileNotFoundError:
            my_canvas.drawString(100, 760, "GRAFICO BARRAS NO HA SIDO GENERADO")
        try:
            imagen_torta = open("torta.png")
            my_canvas.drawString(100, 460, "GRAFICO TORTA")
            my_canvas.drawImage("torta.png", 100, 200, width=250, height=250)
            imagen_torta.close()
        except FileNotFoundError:
            my_canvas.drawString(100, 460, "GRAFICO TORTA NO HA SIDO GENERADO")
        self.mensaje["text"] = "EL REPORTE PDF HA SIDO GENERADO"
        my_canvas.save()


if __name__ == "__main__":
    window = Tk()
    application = Contabilidad(window)
    window.mainloop()
