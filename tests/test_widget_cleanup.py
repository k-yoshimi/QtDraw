"""
Regression tests for widgets left behind after closing a window.

Remaining widgets made every new window slower, because QApplication.setStyle and
setStyleSheet re-apply the style to all existing widgets.
"""

import os
import subprocess
import sys
import textwrap

import pytest
import shiboken6
from PySide6.QtWidgets import QApplication, QMessageBox

from gui_helpers import process_deleted


def n_widgets():
    process_deleted()
    return len(QApplication.allWidgets())


# ==================================================
def test_closed_qtdraw_is_deleted(qapp, tmp_path, monkeypatch):
    from qtdraw.core.qtdraw_app import QtDraw

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Ok)
    before = n_widgets()

    for _ in range(2):
        window = QtDraw()
        assert n_widgets() > before
        window.close()
        assert n_widgets() == before  # the window and its dialogs are deleted.


# ==================================================
def test_cancelled_close_keeps_qtdraw(qapp, tmp_path, monkeypatch):
    from qtdraw.core.qtdraw_app import QtDraw

    monkeypatch.chdir(tmp_path)
    window = QtDraw()
    opened = n_widgets()

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Cancel)
    window.close()
    assert n_widgets() == opened
    window.pyvista_widget.add_site()  # still usable.
    assert len(window.pyvista_widget._data["site"].tolist()) == 1

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Ok)
    window.close()


# ==================================================
def test_closed_standalone_widget_is_deleted(qapp, tmp_path, monkeypatch):
    from qtdraw.core.pyvista_widget import PyVistaWidget

    monkeypatch.chdir(tmp_path)
    before = n_widgets()

    for _ in range(2):
        w = PyVistaWidget(off_screen=True)
        w.add_site()
        w.open_tab_group_view()
        assert n_widgets() > before
        w.close()
        assert n_widgets() == before  # the widget and its data table are deleted.


# ==================================================
def test_closed_window_stops_logging(qapp, tmp_path, monkeypatch):
    import logging

    from qtdraw.core.qtdraw_app import QtDraw

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Ok)
    before = list(logging.getLogger().handlers)

    window = QtDraw()
    assert len(logging.getLogger().handlers) > len(before)
    window.close()
    n_widgets()

    assert logging.getLogger().handlers == before
    logging.getLogger().warning("after close")  # no handler writes to a deleted widget.


# ==================================================
def test_closing_twice_deletes_once(qapp, tmp_path, monkeypatch):
    from qtdraw.core.qtdraw_app import QtDraw

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Ok)
    before = n_widgets()

    window = QtDraw()
    window.close()
    window.close()  # before the deferred deletion.
    assert n_widgets() == before
    assert not shiboken6.isValid(window)


# ==================================================
def test_widget_is_deleted_when_closing_fails(qapp, tmp_path, monkeypatch):
    from qtdraw.core.pyvista_widget import PyVistaWidget

    monkeypatch.chdir(tmp_path)
    before = n_widgets()
    w = PyVistaWidget(off_screen=True)

    mathjax = w._mathjax

    def fail():
        raise OSError("cannot write cache")

    monkeypatch.setattr(mathjax, "close", fail)
    closed = []
    monkeypatch.setattr(w._tab_group_view, "close", lambda: closed.append(True))
    with pytest.raises(OSError, match="cannot write cache"):  # the error is not hidden.
        w.close()
    assert closed  # the data table is closed anyway.
    monkeypatch.setattr(mathjax, "close", type(mathjax).close.__get__(mathjax))
    mathjax.close()

    assert n_widgets() == before  # but the widget is still deleted.


# ==================================================
def test_last_window_closed_in_event_loop():
    code = textwrap.dedent("""
        import logging
        import sys
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication, QMessageBox
        from qtdraw.widget.qt_event_util import get_qt_application
        from qtdraw.core.qtdraw_app import QtDraw

        app = get_qt_application()
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.Ok
        window = QtDraw()
        window.show()
        destroyed = []
        window.destroyed.connect(lambda: destroyed.append(True))
        errors, timeout = [], []
        sys.excepthook = lambda *exc: errors.append(exc)
        QTimer.singleShot(500, window.close)
        QTimer.singleShot(30000, lambda: (timeout.append(True), app.quit()))  # safety net.
        app.exec()
        app.sendPostedEvents()
        assert not errors, errors
        assert not timeout, "closing the last window did not quit the application"
        assert destroyed, "window is not deleted"
        assert not logging.getLogger().handlers, logging.getLogger().handlers
        print("OK")
        """)
    ret = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    assert ret.returncode == 0 and "OK" in ret.stdout, ret.stdout + ret.stderr


# ==================================================
def test_failing_close_in_event_loop_is_reported():
    code = textwrap.dedent("""
        import sys
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QMessageBox
        from qtdraw.widget.qt_event_util import get_qt_application
        from qtdraw.core.qtdraw_app import QtDraw

        app = get_qt_application()
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.Ok
        window = QtDraw()
        window.show()
        mathjax = window.pyvista_widget._mathjax
        real_close = mathjax.close

        def fail():
            real_close()
            raise OSError("cannot write cache")

        mathjax.close = fail
        destroyed, errors, timeout = [], [], []
        window.destroyed.connect(lambda: destroyed.append(True))
        window.pyvista_widget._tab_group_view.destroyed.connect(lambda: destroyed.append(True))
        sys.excepthook = lambda *exc: errors.append(exc[1])
        QTimer.singleShot(500, window.close)
        QTimer.singleShot(30000, lambda: (timeout.append(True), app.quit()))  # safety net.
        app.exec()
        app.sendPostedEvents()
        assert len(errors) == 1 and "cannot write cache" in str(errors[0]), errors
        assert not timeout, "closing the last window did not quit the application"
        assert len(destroyed) == 2, "window or data table is not deleted"
        print("OK")
        """)
    ret = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    assert ret.returncode == 0 and "OK" in ret.stdout, ret.stdout + ret.stderr
