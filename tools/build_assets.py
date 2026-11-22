#!/usr/bin/env python3
"""Build the phosphene-themed SVG assets for the HoGenny profile README.

All text is converted to vector paths (Noto Sans CJK KR), so the SVGs render
identically everywhere without loading any font.

usage: python3 tools/build_assets.py assets

Needs: fonttools, numpy, Pillow, and Noto Sans CJK KR installed under
/usr/share/fonts/opentype/noto/. Brand icon paths in icons.json come from
the simple-icons npm package (CC0).
"""
import json
import math
import os
import random
import sys

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTCollection
from PIL import Image, ImageDraw

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(OUT, "cards"), exist_ok=True)
random.seed(7)

# ---------------------------------------------------------------- fonts ----
FD = "/usr/share/fonts/opentype/noto/"


def _load(fname, family):
    for f in TTCollection(FD + fname).fonts:
        if family in (f["name"].getDebugName(1), f["name"].getDebugName(16)):
            return f
    raise SystemExit(f"font {family} not found in {fname}")


def _ntos(v):
    return f"{v:.0f}" if abs(v - round(v)) < 1e-6 else f"{v:.1f}"


class Font:
    def __init__(self, tt):
        self.cmap = tt.getBestCmap()
        self.gs = tt.getGlyphSet()
        self.hmtx = tt["hmtx"]
        self.upm = tt["head"].unitsPerEm
        self.cache = {}

    def glyph(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            raise KeyError(f"missing glyph {ch!r}")
        if name not in self.cache:
            pen = SVGPathPen(self.gs, ntos=_ntos)
            self.gs[name].draw(pen)
            self.cache[name] = (pen.getCommands(), self.hmtx[name][0])
        return name, self.cache[name]


FONTS = {
    "reg": Font(_load("NotoSansCJK-Regular.ttc", "Noto Sans CJK KR")),
    "med": Font(_load("NotoSansCJK-Medium.ttc", "Noto Sans CJK KR")),
    "bold": Font(_load("NotoSansCJK-Bold.ttc", "Noto Sans CJK KR")),
    "mono": Font(_load("NotoSansCJK-Regular.ttc", "Noto Sans Mono CJK KR")),
}


def measure(s, size, font="reg", ls=0.0):
    f = FONTS[font]
    return sum(f.glyph(c)[1][1] for c in s) * size / f.upm + ls * max(len(s) - 1, 0)


# -------------------------------------------------------------- palette ----
P = dict(
    bg="#0A0F1E", card="#0D1426", stroke="#1D2846", lattice="#1F2844",
    amber="#FFC24D", core="#FFF3D1", text="#EDF1F8", sub="#C3CBDD", muted="#8A94AD",
)
RAINBOW = ["#FF7A93", "#FB923C", "#FFC24D", "#4ADE80", "#22D3EE", "#60A5FA", "#A78BFA"]

BASE_CSS = (
    "@keyframes on{from{opacity:0}to{opacity:1}}"
    ".on{animation:on .8s ease-out both}"
    "@keyframes tw{from{opacity:1}to{opacity:.72}}"
    ".tw{animation:tw 3.4s ease-in-out infinite alternate}"
    "@keyframes tw2{from{opacity:1}to{opacity:.35}}"
    ".tw2{animation:tw2 2.8s ease-in-out infinite alternate}"
    "@keyframes blink{50%{opacity:0}}"
    ".cur{animation:blink 1.05s steps(1) infinite}"
    "@media (prefers-reduced-motion:reduce){.on,.tw,.tw2,.cur,.wv{animation:none}}"
)


def mix(hex_a, hex_b, t):
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


# ------------------------------------------------------------------ doc ----
class Doc:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.body, self.css = [], [], [BASE_CSS]
        self.glyph_ids = {}

    def _gid(self, fk, name, d):
        k = (fk, name)
        if k not in self.glyph_ids:
            gid = f"{fk[0]}{len(self.glyph_ids)}"
            self.glyph_ids[k] = gid
            self.defs.append(f'<path id="{gid}" d="{d}"/>')
        return self.glyph_ids[k]

    def text(self, s, x, y, size, font="reg", fill=None, anchor="start", ls=0.0, attrs=""):
        fill = fill or P["text"]
        f = FONTS[font]
        sc = size / f.upm
        ls_u = ls / sc
        uses, adv = [], 0.0
        for ch in s:
            name, (d, a) = f.glyph(ch)
            if d:
                uses.append(f'<use href="#{self._gid(font, name, d)}" x="{adv:.0f}"/>')
            adv += a + ls_u
        width = (adv - (ls_u if s else 0)) * sc
        x0 = x - width / 2 if anchor == "middle" else x - width if anchor == "end" else x
        extra = f" {attrs}" if attrs else ""
        g = (f'<g transform="translate({x0:.1f} {y:.1f}) scale({sc:.4f} {-sc:.4f})" '
             f'fill="{fill}"{extra}>' + "".join(uses) + "</g>")
        return g, width

    def add(self, *parts):
        self.body.extend(parts)

    def halo(self, gid, color, op=0.55):
        self.defs.append(
            f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset=".45" stop-color="{color}" stop-opacity="{op * .3:.3f}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')

    def lit_symbol(self, sid, color, core, r, halo_r, halo_id):
        self.defs.append(
            f'<g id="{sid}"><circle r="{halo_r}" fill="url(#{halo_id})"/>'
            f'<circle r="{r}" fill="{color}"/><circle r="{r * .42:.2f}" fill="{core}"/></g>')

    def lattice_pattern(self, pid, pitch, r, color, ox=0, oy=0):
        self.defs.append(
            f'<pattern id="{pid}" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse" '
            f'x="{ox}" y="{oy}"><circle cx="{pitch / 2}" cy="{pitch / 2}" r="{r}" fill="{color}"/></pattern>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{self.label}">'
                f'<title>{self.label}</title><style>{"".join(self.css)}</style>'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')

    def save(self, path):
        full = os.path.join(OUT, path)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(self.svg())
        print(f"{path:28s} {os.path.getsize(full) / 1024:6.1f} KB")


def lit_dot(sym, x, y, on_delay, tw_cls="tw", tw_dur=None):
    tw_dur = tw_dur or random.uniform(2.4, 4.8)
    return (f'<g class="on" style="animation-delay:{on_delay:.2f}s"><use class="{tw_cls}" href="#{sym}" '
            f'x="{x:.1f}" y="{y:.1f}" style="animation-duration:{tw_dur:.1f}s;'
            f'animation-delay:-{random.uniform(0, 4):.1f}s"/></g>')


# ------------------------------------------------------------ dot fonts ----
DOT5 = {  # 5x7 uppercase
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}
NAME = {  # 5x8 with descender row, for "HoGenny"
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001", "00000"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110", "00000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111", "00000"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110", "00000"],
    "n": ["00000", "00000", "10110", "11001", "10001", "10001", "10001", "00000"],
    "y": ["00000", "00000", "10001", "10001", "10001", "01111", "00001", "01110"],
}


def dot_word(word, font):
    cells, x = [], 0
    for ch in word:
        rows = font[ch]
        for r, line in enumerate(rows):
            cells += [(x + c, r) for c, v in enumerate(line) if v == "1"]
        x += len(rows[0]) + 1
    return cells, x - 1


# ---------------------------------------------------------------- scene ----
EDGES = [((0, 0), (0.34, 0.28)), ((1, 0), (0.66, 0.28)), ((0, 1), (0.34, 0.60)), ((1, 1), (0.66, 0.60))]
BACK = [(0.34, 0.28), (0.66, 0.28), (0.66, 0.60), (0.34, 0.60)]
DOOR = [(0.898, 0.88), (0.898, 0.307), (0.789, 0.336), (0.789, 0.752)]
PERSON = dict(head=(0.44, 0.402, 0.042), torso=(0.393, 0.452, 0.487, 0.665),
              legs=[(0.400, 0.64, 0.437, 0.82), (0.443, 0.64, 0.480, 0.82)])


def draw_person(dr, S, ox=0.0, oy=0.0, fill=255):
    hx, hy, hr = PERSON["head"]
    dr.ellipse([ox + (hx - hr) * S, oy + (hy - hr) * S, ox + (hx + hr) * S, oy + (hy + hr) * S], fill=fill)
    x1, y1, x2, y2 = PERSON["torso"]
    dr.rounded_rectangle([ox + x1 * S, oy + y1 * S, ox + x2 * S, oy + y2 * S], radius=0.022 * S, fill=fill)
    for x1, y1, x2, y2 in PERSON["legs"]:
        dr.rectangle([ox + x1 * S, oy + y1 * S, ox + x2 * S, oy + y2 * S], fill=fill)


def _bresenham(a, b):
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, out = dx + dy, []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def scene_cells(n, res=12, p_thr=0.3):
    """Person cells by area coverage; walls and door as one-cell-wide lines."""
    S = n * res
    pm = Image.new("L", (S, S), 0)
    draw_person(ImageDraw.Draw(pm), S)
    pc = np.asarray(pm, dtype=float).reshape(n, res, n, res).mean(axis=(1, 3)) / 255
    person = {(i, j) for j in range(n) for i in range(n) if pc[j, i] >= p_thr}

    def cell(p):
        return tuple(min(n - 1, max(0, round(v * n - 0.5))) for v in p)

    edges = set()
    for a, b in EDGES:
        edges.update(_bresenham(cell(a), cell(b)))
    for poly in (BACK, DOOR):
        pts = [cell(p) for p in poly]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            edges.update(_bresenham(a, b))
    return person, edges - person


# --------------------------------------------------------------- header ----
def build_header():
    W, H = 1200, 340
    d = Doc(W, H, "HoGenny · 신호진 · prosthetic vision researcher")
    d.defs.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
                  '<stop offset="0" stop-color="#0C1226"/><stop offset="1" stop-color="#070B16"/></linearGradient>')
    d.defs.append(f'<clipPath id="fr"><rect width="{W}" height="{H}" rx="24"/></clipPath>')
    d.defs.append('<radialGradient id="amb"><stop offset="0" stop-color="#FFB547" stop-opacity=".14"/>'
                  '<stop offset="1" stop-color="#FFB547" stop-opacity="0"/></radialGradient>')
    d.defs.append('<linearGradient id="rb" x1="0" x2="1">' + "".join(
        f'<stop offset="{i / (len(RAINBOW) - 1):.3f}" stop-color="{c}"/>' for i, c in enumerate(RAINBOW))
        + "</linearGradient>")
    d.lattice_pattern("lat", 16, 1.4, P["lattice"], ox=16, oy=16)
    d.halo("h1", "#FFB13B", 0.55)
    d.halo("h2", "#FFB13B", 0.45)
    d.lit_symbol("L", "#FFC85A", "#FFF4D6", 4.6, 12, "h1")
    d.lit_symbol("S", "#FFC85A", "#FFF4D6", 2.7, 7, "h2")
    d.lit_symbol("E", "#E9A94A", "#FBE3B0", 2.1, 5.5, "h2")

    pitch, x0, y0 = 16, 24, 24
    d.add('<g clip-path="url(#fr)">', f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
          '<ellipse cx="410" cy="165" rx="430" ry="150" fill="url(#amb)"/>',
          f'<rect x="16" y="16" width="{W - 32}" height="{H - 28}" fill="url(#lat)"/>')

    # name, lit column by column
    cells, _ = dot_word("HoGenny", NAME)
    nc0, nr0 = 4, 5
    name = []
    for c, r in sorted(cells):
        name.append(lit_dot("L", x0 + (nc0 + c) * pitch, y0 + (nr0 + r) * pitch,
                            0.2 + c * 0.032 + random.uniform(0, 0.1)))
    d.add("<g>", *name, "</g>")

    # right: a small framed "screen" showing the corridor scene as phosphenes.
    # the outline fades in and out, i.e. "object only" vs "object + outline".
    d.css.append("@keyframes cyc{0%,30%{opacity:0}45%,88%{opacity:1}100%{opacity:0}}"
                 ".cyc{animation:cyc 7s ease-in-out 2s infinite both}"
                 "@media (prefers-reduced-motion:reduce){.cyc{animation:none}}")
    d.lattice_pattern("lat7", 7, 0.9, "#1C2542", ox=0, oy=0)
    n, sp = 32, 7
    fw = sp * (n - 1) + 30
    fx, fy = W - 46 - fw, 34
    gx, gy = fx + 15, fy + 15
    d.defs[-1] = (f'<pattern id="lat7" width="{sp}" height="{sp}" patternUnits="userSpaceOnUse" '
                  f'x="{gx - sp / 2}" y="{gy - sp / 2}"><circle cx="{sp / 2}" cy="{sp / 2}" r=".9" '
                  f'fill="#1C2542"/></pattern>')
    d.add(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fw}" rx="14" fill="#060A14" stroke="#2A3558" '
          f'stroke-width="1.5"/>',
          f'<rect x="{fx + 8}" y="{fy + 8}" width="{fw - 16}" height="{fw - 16}" fill="url(#lat7)"/>')
    person, edges = scene_cells(n)
    eg = ['<g class="cyc">'] + [lit_dot("E", gx + i * sp, gy + j * sp, 1.4 + random.uniform(0, 0.6), "tw2")
                                for i, j in sorted(edges)] + ["</g>"]
    pg = ["<g>"] + [lit_dot("S", gx + i * sp, gy + j * sp, 1.0 + random.uniform(0, 0.4))
                    for i, j in sorted(person)] + ["</g>"]
    d.add(*eg, *pg)
    cap, _ = d.text("simulated prosthetic vision", fx + fw / 2, fy + fw + 26, 13, "mono", P["muted"],
                    "middle", ls=1.5)
    d.add(cap)

    # labels on small backdrops so the lattice does not cut through them
    lab, lw = d.text("신호진 · Hojin Shin", 88, 73, 20, "med", P["text"])
    d.add(f'<rect x="78" y="50" width="{lw + 20:.0f}" height="32" rx="8" fill="#0A0F1E" opacity=".92"/>', lab)
    # typing line (SMIL, discrete steps)
    lines = ["undergraduate researcher @ iNES Lab, Gachon Univ.",
             "working on prosthetic vision",
             "building DALM, a photo-matching app"]
    size, ty = 23, 274
    px, pw = d.text("›", 88, ty, size, "mono", P["amber"])
    tx = 88 + pw + 10
    cw = measure("a", size, "mono")
    longest = max(len(s) for s in lines) * cw
    d.add(f'<rect x="78" y="{ty - 28}" width="{longest + pw + 44:.0f}" height="38" rx="9" '
          f'fill="#0A0F1E" opacity=".92"/>', px)
    ev, t = [], 0.0
    for i, s in enumerate(lines):
        for k in range(len(s) + 1):
            ev.append((t, i, k))
            t += 0.058 if k < len(s) else 2.4
        for k in range(len(s) - 1, -1, -1):
            ev.append((t, i, k))
            t += 0.026 if k > 0 else 0.5
    D = t
    kt = ";".join(f"{e[0] / D:.4f}" for e in ev)
    for i, s in enumerate(lines):
        vals = ";".join(f"{(e[2] * cw if e[1] == i else 0):.1f}" for e in ev)
        base = len(s) * cw if i == 0 else 0
        d.defs.append(
            f'<clipPath id="tc{i}"><rect x="{tx - 1:.1f}" y="{ty - 26}" width="{base:.1f}" height="34">'
            f'<animate attributeName="width" dur="{D:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        g, _ = d.text(s, tx, ty, size, "mono", "#FFE6B0" if i == 0 else P["text"])
        d.add(f'<g clip-path="url(#tc{i})">{g}</g>')
    cx_vals = ";".join(f"{tx + e[2] * cw + 2:.1f}" for e in ev)
    d.add(f'<rect class="cur" x="{tx + len(lines[0]) * cw + 2:.1f}" y="{ty - 20}" width="11" height="24" '
          f'rx="2" fill="{P["amber"]}"><animate attributeName="x" dur="{D:.2f}s" repeatCount="indefinite" '
          f'calcMode="discrete" keyTimes="{kt}" values="{cx_vals}"/></rect>')

    d.add(f'<rect y="{H - 4}" width="{W}" height="4" fill="url(#rb)" opacity=".9"/>', "</g>",
          f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="23.5" fill="none" '
          f'stroke="{P["stroke"]}" stroke-width="1.5"/>')
    d.save("header.svg")


# ------------------------------------------------------------- research ----
CAPS = [("① 실제 장면", "복도 끝의 문, 앞에 선 사람"),
        ("② 가장 중요한 것 하나만", "어디에 있는 무엇인지 알기 어려움"),
        ("③ 물체와 주변 윤곽을 함께", "정해진 점 개수 안에서 나눠 담기")]


def build_research():
    """Three panels as separate images so they stack on narrow screens."""
    W, H, S, ox, top = 360, 468, 320, 20, 20
    person, edges = scene_cells(32)
    for k in range(3):
        t1, t2 = CAPS[k]
        d = Doc(W, H, f"{t1}: {t2}")
        d.add(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="22" fill="{P["bg"]}" '
              f'stroke="{P["stroke"]}" stroke-width="1.5"/>')
        d.defs.append(f'<clipPath id="pc"><rect x="{ox}" y="{top}" width="{S}" height="{S}" rx="16"/></clipPath>')
        if k == 0:
            def pt(x, y):
                return f"{ox + x * S:.1f},{top + y * S:.1f}"

            def poly(points, fill, stroke="none", sw=0):
                return (f'<polygon points="{" ".join(pt(x, y) for x, y in points)}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')
            d.defs.append('<linearGradient id="end" x1="0" y1="0" x2="0" y2="1"><stop offset="0" '
                          'stop-color="#2A3A66"/><stop offset="1" stop-color="#1A2547"/></linearGradient>')
            g = ['<g clip-path="url(#pc)">', f'<rect x="{ox}" y="{top}" width="{S}" height="{S}" fill="#0E1527"/>',
                 poly([(0, 0), (1, 0), (0.66, 0.28), (0.34, 0.28)], "#0F172D"),
                 poly([(0, 1), (1, 1), (0.66, 0.6), (0.34, 0.6)], "#152039"),
                 poly([(0, 0), (0.34, 0.28), (0.34, 0.6), (0, 1)], "#111A32"),
                 poly([(1, 0), (1, 1), (0.66, 0.6), (0.66, 0.28)], "#111A32"),
                 poly(BACK, "url(#end)")]
            for a_, b_ in EDGES:
                g.append(f'<line x1="{ox + a_[0] * S}" y1="{top + a_[1] * S}" x2="{ox + b_[0] * S}" '
                         f'y2="{top + b_[1] * S}" stroke="#4B5B88" stroke-width="1.6"/>')
            g += [poly(BACK, "none", "#4B5B88", 1.6), poly(DOOR, "#1E2A4C", "#6A7BB0", 1.6),
                  f'<circle cx="{ox + 0.808 * S:.1f}" cy="{top + 0.56 * S:.1f}" r="2.6" fill="#8C9CCB"/>',
                  f'<ellipse cx="{ox + 0.44 * S:.1f}" cy="{top + 0.822 * S:.1f}" rx="{0.07 * S:.1f}" '
                  f'ry="{0.014 * S:.1f}" fill="#000" opacity=".35"/>']
            hx, hy, hr = PERSON["head"]
            x1, y1, x2, y2 = PERSON["torso"]
            g.append(f'<g fill="#DCE3F5"><circle cx="{ox + hx * S:.1f}" cy="{top + hy * S:.1f}" r="{hr * S:.1f}"/>'
                     f'<rect x="{ox + x1 * S:.1f}" y="{top + y1 * S:.1f}" width="{(x2 - x1) * S:.1f}" '
                     f'height="{(y2 - y1) * S:.1f}" rx="{0.022 * S:.1f}"/>' + "".join(
                         f'<rect x="{ox + a * S:.1f}" y="{top + b * S:.1f}" width="{(c - a) * S:.1f}" '
                         f'height="{(e - b) * S:.1f}"/>' for a, b, c, e in PERSON["legs"]) + "</g></g>")
            d.add(*g)
        else:
            d.halo("hp", "#FFB13B", 0.55)
            d.halo("he", "#FFB13B", 0.4)
            d.lit_symbol("P", "#FFC85A", "#FFF4D6", 3.6, 9, "hp")
            d.lit_symbol("E", "#EDAA4C", "#FBE3B0", 2.7, 7, "he")
            d.lattice_pattern("lat", 10, 1.15, "#222B48")
            g = ['<g clip-path="url(#pc)">', f'<rect x="{ox}" y="{top}" width="{S}" height="{S}" fill="#0B1122"/>',
                 f'<rect x="{ox}" y="{top}" width="{S}" height="{S}" fill="url(#lat)"/>']
            base = 0.3 if k == 1 else 0.6
            for (i, j) in sorted(person):
                g.append(lit_dot("P", ox + 5 + i * 10, top + 5 + j * 10, base + random.uniform(0, 0.5)))
            if k == 2:
                for (i, j) in sorted(edges):
                    g.append(lit_dot("E", ox + 5 + i * 10, top + 5 + j * 10, 1.0 + random.uniform(0, 1.0), "tw2"))
            g.append("</g>")
            d.add(*g)
        d.add(f'<rect x="{ox + .5}" y="{top + .5}" width="{S - 1}" height="{S - 1}" rx="15.5" fill="none" '
              f'stroke="#243055" stroke-width="1"/>')
        a1, w1 = d.text(t1, W / 2, 392, 25, "bold", P["text"], "middle")
        a2, w2 = d.text(t2, W / 2, 428, 18, "reg", P["muted"], "middle")
        assert max(w1, w2) < W - 24, (t1, w1, w2)
        d.add(a1, a2)
        d.save(f"research-{k + 1}.svg")
    return len(person), len(edges)


# ---------------------------------------------------------------- cards ----
ICONS = {
    "envelope": ["11111111", "11000011", "10100101", "10011001", "10000001", "10000001", "11111111", "00000000"],
    "stairs": ["00000000", "00000011", "00000011", "00001111", "00001111", "00111111", "00111111", "11111111"],
    "bubble": ["01111110", "10000001", "10100101", "10000001", "01111110", "00110000", "01000000", "00000000"],
    "cloud": ["00000000", "00001100", "00111110", "01111111", "11111111", "11111111", "01111110", "00000000"],
    "page": ["11111100", "10000110", "10000011", "10111101", "10000001", "10111101", "10000001", "11111111"],
    "ship": ["00011000", "00011000", "00111100", "01111110", "11111111", "11011011", "10011001", "00100100"],
}


def build_card(slug, title, meta, desc, chips, accent, icon):
    W, H = 540, 250
    d = Doc(W, H, f"{title}: {' '.join(desc)}")
    light = mix(accent, "#FFFFFF", 0.35)
    d.defs.append(f'<clipPath id="fr"><rect width="{W}" height="{H}" rx="22"/></clipPath>')
    d.defs.append(f'<radialGradient id="gl"><stop offset="0" stop-color="{accent}" stop-opacity=".30"/>'
                  f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')
    d.halo("ha", accent, 0.6)
    d.lit_symbol("A", accent, mix(accent, "#FFFFFF", 0.7), 3.1, 7.5, "ha")
    d.add('<g clip-path="url(#fr)">', f'<rect width="{W}" height="{H}" fill="{P["card"]}"/>',
          f'<circle cx="{W - 30}" cy="10" r="230" fill="url(#gl)"/>',
          f'<rect y="0" width="{W}" height="3" fill="{accent}" opacity=".85"/>', "</g>",
          f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="21.25" fill="none" '
          f'stroke="{P["stroke"]}" stroke-width="1.5"/>')
    # icon: 8x8 dots
    ix, iy, ip = 40, 36, 8
    g = ['<g>']
    for r, line in enumerate(ICONS[icon]):
        for c, v in enumerate(line):
            x, y = ix + c * ip, iy + r * ip
            if v == "1":
                g.append(lit_dot("A", x, y, 0.15 + (r + c) * 0.03))
            else:
                g.append(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#29345A"/>')
    g.append("</g>")
    d.add(*g)
    t, _ = d.text(title, 124, 66, 29, "bold", P["text"])
    m, _ = d.text(meta, 124, 96, 15, "reg", P["muted"])
    d.add(t, m)
    # arrow (card is a link)
    ax, ay = W - 44, 46
    d.add(f'<g stroke="{P["muted"]}" stroke-width="2.2" stroke-linecap="round" fill="none">'
          f'<path d="M{ax - 8} {ay + 8} L{ax + 8} {ay - 8}"/><path d="M{ax - 4} {ay - 8} H{ax + 8} V{ay + 4}"/></g>')
    for i, line in enumerate(desc):
        s, w = d.text(line, 40, 148 + i * 28, 19, "reg", P["sub"])
        assert 40 + w < W - 30, (slug, line, w)
        d.add(s)
    x = 40
    for c in chips:
        tw_ = measure(c, 14, "med")
        cw = tw_ + 28
        d.add(f'<rect x="{x}" y="196" width="{cw:.1f}" height="30" rx="15" fill="{accent}" fill-opacity=".13" '
              f'stroke="{accent}" stroke-opacity=".45"/>')
        s, _ = d.text(c, x + 14, 216, 14, "med", light)
        d.add(s)
        x += cw + 8
    assert x < W - 30, (slug, x)
    d.save(f"cards/{slug}.svg")


CARDS = [
    ("dalm", "DALM", "2026 · 진행 중  ·  5인 팀  ·  AI 파트",
     ["서로 다른 사람의 사진에서 우연히 닮은 순간을", "찾아 엽서로 주고받는 앱"],
     ["Flutter", "FastAPI", "AI 사진 매칭"], "#FF7A93", "envelope"),
    ("gradroad", "GradRoad", "2026  ·  4인 팀  ·  로드맵 생성",
     ["선수과목 그래프로 졸업까지의", "수강 로드맵을 짜 주는 웹"],
     ["Python", "위상정렬", "백트래킹"], "#4ADE80", "stairs"),
    ("korean-qa", "한국어 QA", "2025  ·  개인  ·  NLP",
     ["KLUE-MRC로 kcbert-base를 파인튜닝한", "한국어 질의응답 데모"],
     ["PyTorch", "Hugging Face", "Gradio"], "#A78BFA", "bubble"),
    ("guestbook", "서버리스 방명록", "2025  ·  개인  ·  클라우드",
     ["부정적인 글은 감정 분석으로 걸러 두는", "AWS 서버리스 방명록"],
     ["Lambda", "DynamoDB", "Comprehend"], "#FB923C", "cloud"),
    ("polioo", "Polioo", "2025  ·  4인 팀  ·  백엔드",
     ["입력한 내용으로 포트폴리오 페이지를 만들어", "S3에 바로 배포해 주는 서비스"],
     ["Node.js", "MongoDB", "S3"], "#60A5FA", "page"),
    ("galaxy-defender", "Galaxy Defender", "2025  ·  개인  ·  게임",
     ["보스 탄막 패턴과 무한 스테이지가 있는", "Java Swing 종스크롤 슈팅 게임"],
     ["Java", "Swing"], "#22D3EE", "ship"),
]


# -------------------------------------------------------------- buttons ----
def build_button(fname, label, accent):
    H = 52
    lw = measure(label, 18, "med")
    W = round(48 + lw + 46)
    d = Doc(W, H, label)
    d.halo("hb", accent, 0.6)
    d.lit_symbol("B", accent, mix(accent, "#FFFFFF", 0.7), 4.2, 11, "hb")
    d.add(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="25.25" fill="{P["card"]}" '
          f'stroke="#2A3558" stroke-width="1.5"/>', f'<use class="tw" href="#B" x="27" y="26"/>')
    t, _ = d.text(label, 48, 33, 18, "med", P["text"])
    ax, ay = W - 26, 26
    d.add(t, f'<g stroke="{P["muted"]}" stroke-width="2" stroke-linecap="round" fill="none">'
             f'<path d="M{ax - 5} {ay + 5} L{ax + 5} {ay - 5}"/><path d="M{ax - 2} {ay - 5} H{ax + 5} V{ay + 2}"/></g>')
    d.save(fname)


# ------------------------------------------------------------- dividers ----
def build_divider(slug, word, ko):
    """Section title capsule: dot-matrix English word + Korean label. Reads on light and dark themes."""
    pitch, H = 6, 60
    cells, wcells = dot_word(word, DOT5)
    x0, y0 = 26, 12
    lx = x0 + (wcells - 1) * pitch + 20
    size = 21
    W = round(lx + measure(ko, size, "bold") + 26)
    d = Doc(W, H, f"{word} · {ko}")
    d.halo("hd", "#FFB13B", 0.5)
    d.lit_symbol("D", "#FFC24D", "#FFF1CC", 2.3, 5.5, "hd")
    d.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{(H - 2) / 2}" fill="{P["card"]}" '
          f'stroke="{P["stroke"]}" stroke-width="1.5"/>')
    d.add("<g>", *[lit_dot("D", x0 + c * pitch, y0 + r * pitch, 0.1 + c * 0.02) for c, r in cells], "</g>")
    t, _ = d.text(ko, lx, 38, size, "bold", P["sub"])
    d.add(t)
    d.save(f"div-{slug}.svg")
    return W, H


# ---------------------------------------------------------------- stack ----
def aws_icon():
    # simple cloud mark (AWS logos are not in simple-icons)
    return "M6.5 19h11a4.5 4.5 0 0 0 .6-8.96A6 6 0 0 0 6.6 9.2 5 5 0 0 0 6.5 19z"


STACK = [("AI · VISION", "#FB923C", ["Python", "PyTorch", "OpenCV", "Hugging Face", "Jupyter", "Gradio"]),
         ("BACKEND · CLOUD", "#4ADE80", ["Node.js", "Express", "MongoDB", "AWS", "Docker", "Linux"]),
         ("APP · TOOLS", "#60A5FA", ["React", "TypeScript", "Java", "Git"])]


def slugify(name):
    return name.lower().replace(" ", "-").replace(".", "")


def build_stack():
    os.makedirs(os.path.join(OUT, "stack"), exist_ok=True)
    icons = json.load(open(os.path.join(HERE, "icons.json")))
    icons["AWS"] = {"path": aws_icon(), "hex": "FF9900"}
    icons["Java"] = {"path": icons["OpenJDK"]["path"], "hex": "F89820"}
    H = 48
    for label, dot, names in STACK:
        w = measure(label, 15, "mono", ls=1.5)
        W = round(w + 30)
        d = Doc(W, H, label)
        t, _ = d.text(label, 22, 29, 15, "mono", "#7D8590", ls=1.5)
        d.add(f'<circle cx="9" cy="24" r="4" fill="{dot}"/>', t)
        d.save(f"stack/_{slugify(label.split(' ')[0])}.svg")
        for name in names:
            ic = icons[name]
            color = "#" + ic["hex"]
            r_, g_, b_ = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            if 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_ < 70:
                color = "#E6EAF2"
            tw_ = measure(name, 17, "med")
            W = round(16 + 22 + 10 + tw_ + 20) + 2
            d = Doc(W, H, name)
            d.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{(H - 2) / 2}" fill="{P["card"]}" '
                  f'stroke="#26314F" stroke-width="1.2"/>',
                  f'<path transform="translate(17 13) scale({22 / 24:.4f})" d="{ic["path"]}" fill="{color}"/>')
            s_, _ = d.text(name, 49, 30, 17, "med", P["text"])
            d.add(s_)
            d.save(f"stack/{slugify(name)}.svg")


# --------------------------------------------------------------- footer ----
RAINBOW_MID = ["#F43F5E", "#F97316", "#EAB308", "#22C55E", "#06B6D4", "#3B82F6", "#8B5CF6"]


def build_footer():
    W, H = 1200, 100
    d = Doc(W, H, "footer")
    d.css.append("@keyframes wv{0%,100%{opacity:.2}50%{opacity:1}}.wv{animation:wv 3.6s ease-in-out infinite}")
    d.defs.append('<linearGradient id="rb" gradientUnits="userSpaceOnUse" x1="0" x2="1200">' + "".join(
        f'<stop offset="{i / (len(RAINBOW_MID) - 1):.3f}" stop-color="{c}"/>' for i, c in enumerate(RAINBOW_MID))
        + "</linearGradient>")
    g = ['<g fill="url(#rb)">']
    n = 100
    for k in range(n):
        x = 12 + k * (W - 24) / (n - 1)
        for row, (amp, ph, r) in enumerate([(18, 0.0, 3.0), (12, 1.9, 1.8)]):
            y = 50 + amp * math.sin(2 * math.pi * x / 540 + ph)
            g.append(f'<circle class="wv" cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
                     f'style="animation-delay:-{(k * 0.05 + row * 0.6) % 3.6:.2f}s"/>')
    g.append("</g>")
    d.add(*g)
    d.save("footer.svg")


if __name__ == "__main__":
    build_header()
    np_, ne = build_research()
    print(f"research lit dots: person={np_} edges={ne} total={np_ + ne} / 1024")
    for c in CARDS:
        build_card(*c)
    build_button("btn-portfolio.svg", "Portfolio", "#FFC24D")
    build_button("btn-email.svg", "tyui3024@icloud.com", "#A78BFA")
    sizes = {}
    for slug, word, ko in [("research", "RESEARCH", "지금 하는 연구"), ("projects", "PROJECTS", "만든 것들"),
                           ("stack", "STACK", "주로 쓰는 도구"), ("more", "MORE", "그 밖에")]:
        sizes[slug] = build_divider(slug, word, ko)
    print("divider sizes:", sizes)
    build_stack()
    build_footer()
