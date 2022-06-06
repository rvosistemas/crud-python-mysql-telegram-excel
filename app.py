from tkinter import *
import logging
from core.clases.contabilidad import Contabilidad

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


if __name__ == "__main__":
    window = Tk()
    application = Contabilidad(window)
    window.mainloop()
