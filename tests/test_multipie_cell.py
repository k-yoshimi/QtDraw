"""
The cell follows the crystal of the MultiPie group, also without the main window (#228).
"""

import pytest
from PySide6.QtWidgets import QMessageBox

from gui_helpers import app, answer  # noqa: F401  (fixture and helper)
from qtdraw.util.util import check_multipie

pytestmark = pytest.mark.skipif(not check_multipie(), reason="MultiPie is not installed.")


def cell(widget):
    return widget._status["crystal"], widget._status["cell"]["gamma"]


# ==================================================
@pytest.mark.parametrize(
    "group, crystal, gamma", [("D6h", "hexagonal", 120.0), ("D3^4", "trigonal", 120.0), ("Oh", "cubic", 90.0)]
)
def test_group_sets_crystal(widget, group, crystal, gamma):
    widget.mp_set_group(group)
    assert cell(widget) == (crystal, gamma)


# ==================================================
def test_group_sets_crystal_as_main_window(widget, app):
    widget.mp_set_group("D6h")
    app.mp_set_group("D6h")
    assert cell(widget) == cell(app.pyvista_widget)


# ==================================================
def test_opened_file_keeps_its_cell(widget, app, tmp_path, monkeypatch):
    widget.mp_set_group("D3^4")
    widget.set_unit_cell({"a": 4.458, "c": 5.925})
    widget.add_site(position="[1/3,0,0]")
    widget.save(str(tmp_path / "a.qtdw"))
    saved = dict(widget._status["cell"])

    widget.load(str(tmp_path / "a.qtdw"))
    assert widget._status["cell"] == saved

    answer(monkeypatch, QMessageBox.Discard)
    app.load_file(str(tmp_path / "a.qtdw"))
    assert app.pyvista_widget._status["crystal"] == "trigonal"
    assert app.pyvista_widget._status["cell"] == saved
