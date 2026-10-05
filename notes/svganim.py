"""Turn a matplotlib figure + per-frame update function into a self-contained animated SVG (SMIL).

Every frame is rendered to SVG; the first frame is the base document. Attributes that change
across frames (path ``d``, marker ``x``/``y``, ``transform``) get an ``<animate>`` child with
one value per frame. Only elements whose attributes actually change are animated, so static
parts (the data cloud, axes) cost nothing.

Limitations: the element structure must be identical in every frame (same number of vertices
per path, same number of markers); text is rendered as glyphs and cannot be animated.
"""
import io
import xml.etree.ElementTree as ET

import matplotlib as mpl

SVG = "http://www.w3.org/2000/svg"
ANIMATED = ("d", "x", "y", "transform")
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def _render(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", transparent=True)
    return ET.fromstring(buf.getvalue())


def anim_to_svg(fig, update, n_frames, fps=20, hold=1.0, path=None):
    """Render ``update(i)`` for ``i in range(n_frames)`` into one looping SVG; return its text."""
    with mpl.rc_context({"svg.hashsalt": "svganim", "svg.fonttype": "path"}):
        roots = []
        for i in range(n_frames):
            update(i)
            roots.append(_render(fig))

    base = roots[0]
    walks = [list(r.iter()) for r in roots]
    if len({len(w) for w in walks}) != 1:
        raise ValueError("frames have different element structures; cannot animate")

    n_hold = round(hold * fps)
    dur = f"{(n_frames + n_hold) / fps:.3f}s"
    for elems in zip(*walks):
        for attr in ANIMATED:
            values = [e.get(attr) for e in elems]
            if values[0] is None or len(set(values)) == 1:
                continue
            values += [values[-1]] * n_hold
            anim = ET.SubElement(elems[0], f"{{{SVG}}}animate")
            anim.set("attributeName", attr)
            anim.set("values", ";".join(values))
            anim.set("dur", dur)
            anim.set("repeatCount", "indefinite")

    for el in base.iter(f"{{{SVG}}}metadata"):  # drop the timestamp so output is reproducible
        el.clear()
    svg = ET.tostring(base, encoding="unicode")
    if path:
        with open(path, "w") as f:
            f.write(svg)
    return svg
