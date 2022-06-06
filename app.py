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

import pandas as pd
from pandas import ExcelWriter
from IPython.core.display import display, HTML

import telegram
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


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
            pdf = open("REPORTE.xlsx")
            pdf.close()
            remove("REPORTE.xlsx")
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
        ttk.Button(text="REPORTES", command=self.reportes).grid(
            row=10, column=4, columnspan=1, sticky=E + W
        )
        # ------   llenado de filas ------
        self.obtener_movimientos()

    def correr_consulta(self, consulta, parametros=()):
        try:
            result = ""
            connection = mysql.connector.connect(
                host="localhost", database=self.db_name, user="root", password="1234"
            )
            if connection.is_connected():
                db_Info = connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                cursor = connection.cursor(buffered=True, dictionary=True)
                cursor.execute(consulta, parametros)
                if parametros == ():
                    result = cursor.fetchall()
                else:
                    result = connection.commit()
        except Error as e:
            print(
                f"Error Mientras conectabas con la bases de datos MySQL, ERROR -> {e}"
            )
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
            len(self.description.get()) != 0
            and len(self.type.get()) != 0
            and len(self.price.get()) != 0
            and str(self.date.get_date()) != "22/5/20"
        )

    def limpiar_formulario(self):
        self.description.delete(0, END)
        self.type.delete(0, END)
        self.price.delete(0, END)

    def agregar_movimiento(self):
        if self.validaciones():
            consulta = "INSERT INTO movimientos (id, descripcion, tipo, valor, fecha) VALUES (NULL, %s, %s, %s, %s)"
            parametros = (
                self.description.get(),
                self.type.get(),
                float(self.price.get()),
                self.date.get_date(),
            )
            self.correr_consulta(consulta, parametros)
            self.mensaje[
                "text"
            ] = f"El {self.type.get()} se ha GUARDADO satisfactoriamente."
            self.limpiar_formulario()
        else:
            self.mensaje["text"] = "TODOS LOS CAMPOS SON REQUERIDOS"
        self.obtener_movimientos()

    def borrar_movimiento(self):
        self.mensaje["text"] = ""
        try:
            id = self.tree.item(self.tree.selection())["text"]
        except IndexError:
            self.mensaje["text"] = "Por favor SELECCIONA un movimiento"
            return
        self.mensaje["text"] = ""
        consulta = "DELETE FROM movimientos WHERE id = %s"
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
        self.new_description = Entry(self.ventana_editar)
        self.new_description.focus()
        self.new_description.grid(row=1, column=1)

        # ------   tipo antiguo ------
        Label(self.ventana_editar, text="tipo anterior").grid(row=2, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=tipo),
            state="readonly",
        ).grid(row=2, column=1)
        # ------   tipo nuevo ------
        Label(self.ventana_editar, text="Tipo: ").grid(row=3, column=0)
        self.new_type = ttk.Combobox(
            self.ventana_editar, state="readonly", values=["Ingreso", "Gasto"]
        )
        self.new_type.grid(row=3, column=1)

        # ------   valor antiguo ------
        Label(self.ventana_editar, text="valor anterior").grid(row=4, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=valor),
            state="readonly",
        ).grid(row=4, column=1)
        # ------   valor nuevo ------
        Label(self.ventana_editar, text="Valor: ").grid(row=5, column=0)
        self.new_price = Entry(self.ventana_editar)
        self.new_price.grid(row=5, column=1)

        # ------   fecha antigua ------
        Label(self.ventana_editar, text="fecha anterior").grid(row=6, column=0)
        Entry(
            self.ventana_editar,
            textvariable=StringVar(self.ventana_editar, value=fecha),
            state="readonly",
        ).grid(row=6, column=1)
        # ------   fecha nueva ------
        Label(self.ventana_editar, text="Fecha: ").grid(row=7, column=0)
        self.new_date = Calendar(
            self.ventana_editar, selectmode="day", year=2020, month=5, day=22
        )
        self.new_date.grid(row=7, column=1)

        datos_viejos = {
            "descripcion": descripcion,
            "tipo": tipo,
            "valor": valor,
            "fecha": fecha,
        }

        Button(
            self.ventana_editar,
            text="Actualizar",
            command=lambda: self.actualizar(datos_viejos, id),
        ).grid(row=8, column=0, sticky=W)

    def actualizar(self, datos_viejos, id):
        if len(self.new_description.get()) == 0:
            self.new_description = datos_viejos["descripcion"]
        else:
            self.new_description = str(self.new_description.get())
        if len(self.new_type.get()) == 0:
            self.new_type = datos_viejos["tipo"]
        else:
            self.new_type = str(self.new_type.get())
        if len(self.new_price.get()) == 0:
            self.new_price = datos_viejos["valor"]
        else:
            self.new_price = str(self.new_price.get())
        if str(self.new_date.get_date()) == "22/5/20":
            self.new_date = datos_viejos["fecha"]
        else:
            self.new_date = str(self.new_date.get())

        consulta = "UPDATE movimientos SET descripcion = %s, tipo = %s, valor = %s, fecha = %s WHERE id = %s"
        parametros = (
            self.new_description,
            self.new_type,
            self.new_price,
            self.new_date,
            id,
        )
        self.correr_consulta(consulta, parametros)
        print("$" * 20, "parametros: -->  ", parametros)
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

    def reportes(self):
        self.reporte_pdf()
        self.reporte_excel()
        self.mensaje["text"] = "EL REPORTE PDF Y EXCEL HAN SIDO GENERADOS Y ENVIADOS"

    def envio_telegram(self, reporte):
        bot_token = "5541373563:AAG9WL9CpEH1Yi8Cfq_kR9oyVOyYQY0CYyQ"
        chat_id = "@prueba_itp_bot"
        bot = telegram.Bot(token=bot_token)

        with open(reporte, "rb") as photo_file:
            bot.sendPhoto(
                chat_id=chat_id, photo=photo_file, caption="Hola, te envio este reporte"
            )
            photo_file.close()

    def reporte_pdf(self):
        my_canvas = canvas.Canvas("REPORTE.pdf", pagesize=letter)
        try:
            imagen_barras = open("barras.png")
            my_canvas.drawString(100, 760, "GRAFICO BARRAS")
            my_canvas.drawImage("barras.png", 100, 500, width=250, height=250)
            self.envio_telegram("barras.png")
            imagen_barras.close()
        except FileNotFoundError:
            my_canvas.drawString(100, 760, "GRAFICO BARRAS NO HA SIDO GENERADO")
        try:
            imagen_torta = open("torta.png")
            my_canvas.drawString(100, 460, "GRAFICO TORTA")
            my_canvas.drawImage("torta.png", 100, 200, width=250, height=250)
            self.envio_telegram("torta.png")
            imagen_torta.close()
        except FileNotFoundError:
            my_canvas.drawString(100, 460, "GRAFICO TORTA NO HA SIDO GENERADO")
        my_canvas.save()

    def path_to_image_html(path):
        return '<img src="' + path + '" width="200" >'

    def reporte_excel(self):
        df = pd.DataFrame({})
        error = False
        try:
            imagen_barras = open("barras.png")
            imagen_barras.close()
        except FileNotFoundError:
            error = True
        if not error:
            # your images
            imagen_barra = ["barras.png"]

            df["grafico_barras"] = imagen_barra

            # convert your links to html tags
            def path_to_image_html(path):
                return '<img src="' + path + '" width="60" >'

            pd.set_option("display.max_colwidth", None)

            image_cols = ["grafico_barras"]

            # Create the dictionariy to be passed as formatters
            format_dict = {}
            for image_col in image_cols:
                format_dict[image_col] = path_to_image_html

            display(HTML(df.to_html(escape=False, formatters=format_dict)))
        else:
            df["grafico_barras"] = ["NO HA SIDO GENERADO"]

        error = False
        try:
            imagen_torta = open("torta.png")
            imagen_torta.close()
        except FileNotFoundError:
            error = True
        if not error:
            # your images
            imagen_torta = ["torta.png"]

            df["grafico_torta"] = imagen_torta

            # convert your links to html tags
            def path_to_image_html(path):
                return '<img src="' + path + '" width="60" >'

            pd.set_option("display.max_colwidth", None)

            image_cols = ["grafico_torta"]

            # Create the dictionariy to be passed as formatters
            format_dict = {}
            for image_col in image_cols:
                format_dict[image_col] = path_to_image_html

            display(HTML(df.to_html(escape=False, formatters=format_dict)))
        else:
            df["grafico_torta"] = ["NO HA SIDO GENERADO", ""]

        writer = ExcelWriter("REPORTE.xlsx")
        df.to_excel(writer, "Hoja de reportes", index=False)
        writer.save()


if __name__ == "__main__":
    window = Tk()
    application = Contabilidad(window)
    window.mainloop()
