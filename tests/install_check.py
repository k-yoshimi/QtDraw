"""
Check an installed QtDraw package (not the source tree).

Run it with the Python of an environment where the package is installed, from a directory outside the source tree:

    python -I tests/install_check.py [--mathjax]

With --mathjax, LaTeX must be drawn by MathJax (the browser of playwright is installed), not as plain text.
"""

import os
import sys
import subprocess
import tempfile
from importlib import metadata
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def check(condition, message):
    if not condition:
        sys.exit(f"install check failed: {message}")
    print(f"ok: {message}")


def main():
    mathjax = "--mathjax" in sys.argv[1:]

    import qtdraw

    package = Path(qtdraw.__file__).resolve().parent
    check("site-packages" in package.parts, f"qtdraw is imported from the installed package ({package})")
    check(metadata.version("qtdraw") == qtdraw.__version__, f"version of the package is {qtdraw.__version__}")
    for file in ["core/qtdraw.png", "mathjax/es5/tex-svg-full.js"]:
        check((package / file).is_file(), f"data file {file} is installed")

    bin = Path(sys.executable).parent
    for script in ["qtdraw", "conv_qtdraw3"]:
        ret = subprocess.run([str(bin / script), "--help"], capture_output=True, text=True)
        check(ret.returncode == 0 and "Usage:" in ret.stdout, f"command {script} runs")

    from qtdraw import PyVistaWidget, QtDraw, get_qt_application
    from qtdraw.widget.mathjax import MathJaxSVG

    app = get_qt_application()

    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)

        converter = MathJaxSVG(cache_dir=Path(directory) / "svg_cache")  # no cached SVG from another installation.
        svg, size = converter.convert("$x^2$")
        if mathjax:
            check(converter.available and "<svg" in svg, "LaTeX is drawn by MathJax")
        converter.close()

        widget = PyVistaWidget(off_screen=True)
        for name in [
            "site", "bond", "vector", "orbital", "stream", "line", "plane", "circle", "torus", "ellipsoid",
            "toroid", "box", "polygon", "spline", "spline_t", "text3d", "caption", "text2d",
        ]:  # fmt: skip
            getattr(widget, f"add_{name}")()
        widget.add_text2d("$x^2$")
        widget.mp_set_group("D6h")
        file = Path(directory) / "a.qtdw"
        widget.render()
        check(len(widget.renderer.actors) > 20, "objects are drawn")
        rows = {name: model.rowCount() for name, model in widget._data.items()}
        widget.save(str(file))
        widget.clear_data()
        widget.load(str(file))
        check({name: model.rowCount() for name, model in widget._data.items()} == rows, "a saved drawing is read again")
        widget.close()

        window = QtDraw(filename=str(file))
        app.processEvents()
        check(window.isVisible(), "the main window opens a file")
        window.close()


if __name__ == "__main__":
    main()
