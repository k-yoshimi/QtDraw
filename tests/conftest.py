"""
Common fixtures for automated tests.
"""

import os
import sys
import traceback

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import shiboken6

from qtdraw.widget.qt_event_util import get_qt_application


# ==================================================
@pytest.fixture(autouse=True)
def process_deleted_widgets():
    """
    Delete widgets scheduled for deletion by a test.

    Tests run without an event loop, so windows deleted on close (deleteLater) are
    deleted here. Errors are reported instead of being shown in a (blocking) message box.
    """
    from PySide6.QtCore import QCoreApplication, QEvent

    yield
    if QCoreApplication.instance() is None:
        return

    errors = []
    hook = sys.excepthook
    sys.excepthook = lambda *exc: errors.append("".join(traceback.format_exception(*exc)))
    try:
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    finally:
        sys.excepthook = hook
    if errors:
        pytest.fail("error while deleting widgets:\n" + "\n".join(errors))


# ==================================================
@pytest.fixture(scope="session")
def qapp():
    return get_qt_application()


# ==================================================
@pytest.fixture
def widget(qapp, tmp_path, monkeypatch):
    from qtdraw.core.pyvista_widget import PyVistaWidget

    monkeypatch.chdir(tmp_path)
    w = PyVistaWidget(off_screen=True)
    yield w
    if shiboken6.isValid(w):  # not yet closed (and deleted) by the test.
        w.close()
