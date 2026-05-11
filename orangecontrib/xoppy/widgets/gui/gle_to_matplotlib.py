"""
gle_to_matplotlib.py
--------------------
A parser/renderer that reads a subset of GLE drawing commands and
reproduces the figure in matplotlib.

Supported GLE commands
-----------------------
  Variable assignment     : name = value  /  name$ = "string"
  size w h                : sets figure size in cm
  set hei h               : default text height (ignored, uses matplotlib default)
  set color <name>        : changes current drawing color
  set lwidth <w>          : changes current line width (0 → hairline → 0.5 pt)
  amove x y              : move to absolute position (with variable substitution)
  rmove dx dy             : move relative
  rline dx dy [arrow end] : draw a line (optionally with an arrowhead)
  tex "string"            : render a LaTeX string at the current position
  box w h                 : draw a filled/outlined rectangle
  ! ...                   : comment (ignored)

Usage
-----
    from gle_to_matplotlib import GLEPlot
    fig, ax = GLEPlot("diff_pat.gle").render()
    fig.savefig("diff_pat.png", dpi=150)
    # or just:
    GLEPlot("diff_pat.gle").show()
"""

import re
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COLOR_MAP = {
    "black": "black",
    "white": "white",
    "red":   "red",
    "green": "green",
    "blue":  "blue",
    "cyan":  "cyan",
    "magenta": "magenta",
    "yellow": "yellow",
    "gray":  "gray",
    "grey":  "grey",
}

def _to_float(token, variables):
    """Evaluate a token that may be a number, variable, or simple expression."""
    # Replace known variable names (longest first to avoid partial matches)
    expr = token
    for name in sorted(variables, key=len, reverse=True):
        expr = re.sub(r'\b' + re.escape(name) + r'\b', str(variables[name]), expr)
    try:
        return float(eval(expr))   # safe enough for numeric-only expressions
    except Exception:
        raise ValueError(f"Cannot evaluate token: {token!r}  (expr={expr!r})")


def _eval_coords(tokens, variables):
    """Return (x, y) from a list of two token strings."""
    return _to_float(tokens[0], variables), _to_float(tokens[1], variables)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class GLEPlot:
    """Parse a GLE script and render it with matplotlib."""

    def __init__(self, filename):
        with open(filename) as fh:
            self.lines = fh.readlines()
        self.variables = {}   # numeric variables
        self.strings   = {}   # string variables  (name$ → value)
        self.size_w    = 10   # cm  (default)
        self.size_h    = 10

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self):
        """Parse the GLE file and return (fig, ax)."""
        cm = 1 / 2.54
        fig, ax = plt.subplots(figsize=(self.size_w * cm * 3,
                                         self.size_h * cm * 3))
        ax.set_aspect("equal")
        ax.axis("off")

        # State
        cx, cy   = 0.0, 0.0   # current position
        color    = "black"
        lwidth   = 1.0        # pt

        for raw in self.lines:
            line = raw.strip()

            # Skip blank lines and comments
            if not line or line.startswith("!"):
                continue

            # ---- variable assignment: name = value  or  name$ = "…" ----
            m = re.match(r'^([A-Za-z_]\w*)\$\s*=\s*"(.*)"$', line)
            if m:
                self.strings[m.group(1)] = m.group(2)
                continue

            m = re.match(r'^([A-Za-z_]\w*)\s*=\s*(.+)$', line)
            if m:
                try:
                    self.variables[m.group(1)] = _to_float(m.group(2).strip(),
                                                            self.variables)
                except Exception:
                    pass
                continue

            tokens = line.split()
            cmd    = tokens[0].lower()

            # ---- size ----
            if cmd == "size":
                self.size_w = float(tokens[1])
                self.size_h = float(tokens[2])
                ax.set_xlim(0, self.size_w)
                ax.set_ylim(0, self.size_h)
                fig.set_size_inches(self.size_w * cm * 3,
                                    self.size_h * cm * 3)
                continue

            # ---- set ----
            if cmd == "set":
                sub = tokens[1].lower()
                if sub == "color":
                    color = COLOR_MAP.get(tokens[2].lower(), tokens[2].lower())
                elif sub == "lwidth":
                    w = float(tokens[2])
                    lwidth = 0.5 if w == 0 else w * 10   # rough cm→pt
                continue

            # ---- amove ----
            if cmd == "amove":
                cx, cy = _eval_coords(tokens[1:3], self.variables)
                continue

            # ---- rmove ----
            if cmd == "rmove":
                dx, dy = _eval_coords(tokens[1:3], self.variables)
                cx += dx
                cy += dy
                continue

            # ---- rline [arrow end] ----
            if cmd == "rline":
                dx, dy   = _eval_coords(tokens[1:3], self.variables)
                has_arrow = "arrow" in line.lower()
                x0, y0   = cx, cy
                x1, y1   = cx + dx, cy + dy

                if has_arrow:
                    ax.annotate(
                        "",
                        xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color=color,
                            lw=lwidth,
                            mutation_scale=10,
                        ),
                    )
                else:
                    ax.plot([x0, x1], [y0, y1],
                            color=color, lw=lwidth, solid_capstyle="butt")

                cx, cy = x1, y1
                continue

            # ---- tex ----
            if cmd == "tex":
                # Collect everything after "tex" (handles spaces in labels)
                rest = line[3:].strip().strip('"')
                # Replace GLE string variables like V$, H$
                for sname, sval in self.strings.items():
                    rest = rest.replace(sname + "$", sval)
                ax.text(cx, cy, rest,
                        color=color,
                        fontsize=7,
                        ha="left", va="bottom",
                        usetex=False)   # uses matplotlib mathtext (no LaTeX install needed)
                continue

            # ---- box w h ----
            if cmd == "box":
                bw = _to_float(tokens[1], self.variables)
                bh = _to_float(tokens[2], self.variables)
                # GLE box grows right and up from current pos;
                # negative width/height means the other direction
                bx = cx + min(0, bw)
                by = cy + min(0, bh)
                rect = mpatches.Rectangle(
                    (bx, by), abs(bw), abs(bh),
                    linewidth=lwidth, edgecolor=color,
                    facecolor=color if color != "black" else "saddlebrown",
                )
                ax.add_patch(rect)
                continue

        plt.tight_layout()
        return fig, ax

    def show(self):
        fig, ax = self.render()
        plt.show()
        return fig, ax

    def save(self, filename, dpi=150, **kwargs):
        fig, ax = self.render()
        fig.savefig(filename, dpi=dpi, **kwargs)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _latex_available():
    """Check if a LaTeX installation is available for matplotlib."""
    try:
        import shutil
        return shutil.which("latex") is not None
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    plot = GLEPlot("diff_pat.gle")
    plot.show()