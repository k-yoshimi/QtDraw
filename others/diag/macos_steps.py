"""Time each startup step; dump Python stacks if a step hangs."""

import faulthandler
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
faulthandler.dump_traceback_later(60, repeat=True, file=sys.__stdout__)
T0 = time.time()


def step(name):
    print(f"[{time.time() - T0:8.1f}s] {name}", flush=True)


step("start")
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
step("QApplication created")

from PySide6.QtGui import QFontDatabase, QFont, QImage, QPainter, QColor

fams = QFontDatabase.families()
step(f"QFontDatabase.families: {len(fams)}")

img = QImage(200, 50, QImage.Format_ARGB32)
img.fill(0)
p = QPainter(img)
p.setFont(QFont("Helvetica", 12))
p.drawText(10, 30, "Hello")
p.end()
step("QPainter.drawText done")

from qtdraw.widget.qt_event_util import get_qt_application

get_qt_application()
step("get_qt_application done")

from qtdraw.widget.mathjax import MathJaxSVG

m = MathJaxSVG()
step(f"MathJaxSVG created, available={m.available}")
svg, wh = m.convert("$x^2$", "black", 12)
step(f"MathJax convert done {wh}")

from qtdraw.core.pyvista_widget import PyVistaWidget

step("pyvista_widget imported")
w = PyVistaWidget(off_screen=True)
step("PyVistaWidget #1 created")
w.add_site()
step("add_site done")
w.close()
step("PyVistaWidget #1 closed")
w = PyVistaWidget(off_screen=True)
step("PyVistaWidget #2 created")
w.close()
m.close()
step("end")
