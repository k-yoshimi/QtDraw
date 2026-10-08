"""
Regression tests for widgets left behind after closing a window.

Remaining widgets made every new window slower, because QApplication.setStyle and
setStyleSheet re-apply the style to all existing widgets.
"""

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QMessageBox


def n_widgets():
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
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
