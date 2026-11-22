#!/usr/bin/env python3
"""Build the SVG assets (light + dark) for the HoGenny profile README.

Text is shaped with HarfBuzz and converted to vector paths, so the images look
the same everywhere without loading fonts (GitHub serves SVGs with a CSP that
blocks font loading anyway).

usage: python3 tools/build_assets.py assets
needs: pip install fonttools uharfbuzz
       fonts in tools/fonts (not committed, SIL OFL):
         npm i pretendard geist
         cp node_modules/pretendard/dist/public/static/Pretendard-{Regular,Medium,SemiBold,Bold}.otf tools/fonts/
         cp node_modules/geist/dist/fonts/geist-sans/Geist-Bold.ttf tools/fonts/
         cp node_modules/geist/dist/fonts/geist-mono/GeistMono-Medium.ttf tools/fonts/
       icons: Lucide (ISC) and simple-icons (CC0) paths bundled in tools/icons.json
"""
import json
import math
import os
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
ICONS = json.load(open(os.path.join(HERE, "icons.json"), encoding="utf-8"))


# ---------------------------------------------------------------- fonts ----
def _ntos(v):
    return f"{v:.0f}" if abs(v - round(v)) < 1e-6 else f"{v:.1f}"


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.order = self.tt.getGlyphOrder()
        self.gs = self.tt.getGlyphSet()
        self.upm = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.cache = {}

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            if info.codepoint == 0:
                raise KeyError(f"missing glyph in {text!r}")
            out.append((info.codepoint, pos.x_advance, pos.x_offset, pos.y_offset))
        return out

    def path(self, gid):
        if gid not in self.cache:
            pen = SVGPathPen(self.gs, ntos=_ntos)
            self.gs[self.order[gid]].draw(pen)
            self.cache[gid] = pen.getCommands()
        return self.cache[gid]


FD = os.path.join(HERE, "fonts")
FONTS = {
    "reg": Font(os.path.join(FD, "Pretendard-Regular.otf")),
    "med": Font(os.path.join(FD, "Pretendard-Medium.otf")),
    "semi": Font(os.path.join(FD, "Pretendard-SemiBold.otf")),
    "bold": Font(os.path.join(FD, "Pretendard-Bold.otf")),
    "display": Font(os.path.join(FD, "Geist-Bold.ttf")),
    "mono": Font(os.path.join(FD, "GeistMono-Medium.ttf")),
}


def measure(s, size, font="reg", ls=0.0):
    f = FONTS[font]
    return sum(g[1] for g in f.shape(s)) * size / f.upm + ls * max(len(s) - 1, 0)


# --------------------------------------------------------------- themes ----
T = {
    "light": dict(bg="#FFFFFF", card="#FFFFFF", border="#D8DEE4", fg="#1F2328", fg2="#424A53",
                  muted="#656D76", chip="#F6F8FA", chip_border="#E1E6EB", accent="#4F46E5", tint=0.10,
                  shadow=True, grid="#0F172A", grid_op=0.07,
                  blobs=[("#A5B4FC", 0.55), ("#99F6E4", 0.55), ("#F5D0FE", 0.50)],
                  orb=["#EEF2FF", "#A5B4FC", "#6366F1", "#3730A3"], ring="#6366F1", ring_op=0.30,
                  node2="#14B8A6", node3="#EC4899",
                  primary=("#1F2328", "#FFFFFF")),
    "dark": dict(bg="#0D1117", card="#151B23", border="#30363D", fg="#F0F6FC", fg2="#D1D9E0",
                 muted="#9198A1", chip="#212830", chip_border="#3D444D", accent="#A5B4FC", tint=0.16,
                 shadow=False, grid="#FFFFFF", grid_op=0.06,
                 blobs=[("#4F46E5", 0.45), ("#0891B2", 0.34), ("#A21CAF", 0.26)],
                 orb=["#E0E7FF", "#818CF8", "#4F46E5", "#1E1B4B"], ring="#A5B4FC", ring_op=0.28,
                 node2="#2DD4BF", node3="#F472B6",
                 primary=("#F0F6FC", "#0D1117")),
}
ACC = {"rose": ("#E11D48", "#FB7185"), "emerald": ("#059669", "#34D399"), "violet": ("#7C3AED", "#A78BFA"),
       "orange": ("#EA580C", "#FB923C"), "blue": ("#2563EB", "#60A5FA"), "cyan": ("#0891B2", "#22D3EE")}


def acc(name, theme):
    return ACC[name][0 if theme == "light" else 1]


# ------------------------------------------------------------------ doc ----
class Doc:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.body, self.css = [], [], []
        self.glyph_ids = {}

    def _gid(self, fk, gid, d):
        k = (fk, gid)
        if k not in self.glyph_ids:
            self.glyph_ids[k] = f"gl{len(self.glyph_ids)}"
            self.defs.append(f'<path id="{self.glyph_ids[k]}" d="{d}"/>')
        return self.glyph_ids[k]

    def text(self, s, x, y, size, font, fill, anchor="start", ls=0.0):
        f = FONTS[font]
        sc = size / f.upm
        ls_u = ls / sc
        uses, pen = [], 0.0
        for gid, adv, xo, yo in f.shape(s):
            d = f.path(gid)
            if d:
                yattr = f' y="{yo}"' if yo else ""
                uses.append(f'<use href="#{self._gid(font, gid, d)}" x="{pen + xo:.0f}"{yattr}/>')
            pen += adv + ls_u
        width = (pen - (ls_u if s else 0)) * sc
        x0 = x - width / 2 if anchor == "middle" else x - width if anchor == "end" else x
        return (f'<g transform="translate({x0:.1f} {y:.1f}) scale({sc:.5f} {-sc:.5f})" fill="{fill}">'
                + "".join(uses) + "</g>"), width

    def add(self, *parts):
        self.body.extend(parts)

    def svg(self):
        css = f'<style>{"".join(self.css)}</style>' if self.css else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img" aria-label="{self.label}"><title>{self.label}</title>{css}'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')

    def save(self, name):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(self.svg())


def lucide(name, x, y, size, color, sw=2.0):
    els = ICONS["lucide"][name].replace("currentColor", color)
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{els}</g>')


def shadow_def(d, t):
    if t["shadow"]:
        d.defs.append('<filter id="sh" x="-5%" y="-5%" width="110%" height="120%"><feDropShadow dx="0" dy="1.5" '
                      'stdDeviation="2.5" flood-color="#1F2328" flood-opacity=".07"/></filter>')
        return ' filter="url(#sh)"'
    return ""


# --------------------------------------------------------------- header ----
def build_header(theme):
    t = T[theme]
    W, H = 1200, 400
    d = Doc(W, H, "Hojin Shin (신호진) · Undergraduate Researcher, iNES Lab, Gachon University")
    d.defs.append(f'<clipPath id="fr"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24"/></clipPath>')
    for i, (c, op) in enumerate(t["blobs"]):
        d.defs.append(f'<radialGradient id="m{i}"><stop offset="0" stop-color="{c}" stop-opacity="{op}"/>'
                      f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>')
    d.defs.append(f'<pattern id="gp" width="40" height="40" patternUnits="userSpaceOnUse" x="20" y="20">'
                  f'<path d="M40 0H0V40" fill="none" stroke="{t["grid"]}" stroke-opacity="{t["grid_op"]}"/></pattern>')
    d.defs.append('<linearGradient id="gf" x1="0" x2="1"><stop offset=".38" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".8" stop-color="#fff" stop-opacity="1"/></linearGradient>'
                  f'<mask id="gm"><rect width="{W}" height="{H}" fill="url(#gf)"/></mask>')
    o = t["orb"]
    d.defs.append(f'<radialGradient id="ob" cx=".36" cy=".3" r=".78"><stop offset="0" stop-color="{o[0]}"/>'
                  f'<stop offset=".35" stop-color="{o[1]}"/><stop offset=".75" stop-color="{o[2]}"/>'
                  f'<stop offset="1" stop-color="{o[3]}"/></radialGradient>'
                  f'<radialGradient id="og"><stop offset="0" stop-color="{o[1]}" stop-opacity=".45"/>'
                  f'<stop offset="1" stop-color="{o[1]}" stop-opacity="0"/></radialGradient>')
    cx, cy = 1000, 205
    d.add('<g clip-path="url(#fr)">', f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
          '<ellipse cx="985" cy="105" rx="430" ry="320" fill="url(#m0)"/>',
          '<ellipse cx="1160" cy="370" rx="380" ry="290" fill="url(#m1)"/>',
          '<ellipse cx="740" cy="430" rx="340" ry="230" fill="url(#m2)"/>',
          f'<rect width="{W}" height="{H}" fill="url(#gp)" mask="url(#gm)"/>',
          f'<circle cx="{cx}" cy="{cy}" r="215" fill="url(#og)"/>')
    rings = [(150, 1.0, 70, [(-40, 5.5, t["accent"])]),
             (205, 0.7, 110, [(150, 4.5, t["node2"])]),
             (262, 0.45, 160, [(250, 4, t["node3"]), (35, 3.5, t["ring"])])]
    for r, op, dur, nodes in rings:
        g = [f'<g><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["ring"]}" '
             f'stroke-opacity="{t["ring_op"] * op:.3f}" stroke-width="1.3"/>']
        g += [f'<circle cx="{cx + r * math.cos(math.radians(a)):.1f}" '
              f'cy="{cy + r * math.sin(math.radians(a)):.1f}" r="{nr}" fill="{nc}"/>'
              for a, nr, nc in nodes]
        g.append(f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
                 f'to="360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></g>')
        d.add(*g)
    d.add(f'<circle cx="{cx}" cy="{cy}" r="112" fill="url(#ob)"/>',
          f'<ellipse cx="{cx - 38}" cy="{cy - 46}" rx="36" ry="22" fill="#fff" fill-opacity=".22" '
          f'transform="rotate(-30 {cx - 38} {cy - 46})"/>')

    # text block
    d.add(f'<circle cx="69" cy="91" r="4.5" fill="{t["accent"]}"/>')
    lab, _ = d.text("UNDERGRADUATE RESEARCHER", 84, 97, 15, "mono", t["muted"], ls=2.2)
    name, nw = d.text("Hojin Shin", 60, 194, 86, "display", t["fg"], ls=-3.2)
    ko, kw = d.text("신호진", 60 + nw + 24, 194, 36, "semi", t["muted"])
    aff, _ = d.text("iNES Lab · Gachon University", 64, 248, 26, "med", t["fg2"])
    d.add(lab, name, ko, aff)
    assert 60 + nw + 24 + kw < 740, nw
    x = 64
    for label, dot in [("Prosthetic Vision", t["accent"]), ("Computer Vision", t["node2"]),
                       ("Human-centered AI", t["node3"])]:
        tw = measure(label, 17, "med")
        w = 18 + 8 + 10 + tw + 18
        d.add(f'<rect x="{x}" y="288" width="{w:.1f}" height="40" rx="20" fill="{t["chip"]}" fill-opacity=".85" '
              f'stroke="{t["chip_border"]}"/>', f'<circle cx="{x + 22}" cy="308" r="4" fill="{dot}"/>')
        s, _ = d.text(label, x + 36, 314, 17, "med", t["fg2"])
        d.add(s)
        x += w + 10
    d.add("</g>", f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="none" '
                  f'stroke="{t["border"]}" stroke-width="1.5"/>')
    d.save(f"header-{theme}.svg")


# -------------------------------------------------------------- buttons ----
def build_button(theme, slug, label, icon, primary):
    t = T[theme]
    H = 48
    tw = measure(label, 17, "semi")
    W = round(16 + 20 + 10 + tw + 12 + 14 + 16)
    d = Doc(W, H, label)
    if primary:
        bg, fg = t["primary"]
        d.add(f'<rect width="{W}" height="{H}" rx="12" fill="{bg}"/>')
        ic, arrow_op = fg, 0.7
    else:
        fg = t["fg"]
        d.add(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="11.5" fill="{t["card"]}" '
              f'stroke="{t["border"]}" stroke-width="1.5"/>')
        ic, arrow_op = t["fg2"], 1
    d.add(lucide(icon, 16, 14, 20, ic))
    s, _ = d.text(label, 46, 30, 17, "semi", fg)
    d.add(s, f'<g opacity="{arrow_op}">' + lucide("arrow-up-right", W - 30, 17, 14,
                                                   fg if primary else t["muted"], 2.2) + "</g>")
    d.save(f"btn-{slug}-{theme}.svg")


# ----------------------------------------------------------- step cards ----
STEPS = [("box", "장면 데이터", ["ProcTHOR 실내,", "SANPO 실외 보행"]),
         ("tags", "중요도 라벨", ["사람이 매긴 중요도로", "모델을 학습"]),
         ("sliders-horizontal", "예산 안에서 배분", ["제한된 해상도 안에서", "남길 정보를 선택"]),
         ("scan-eye", "표현과 평가", ["인공 시각으로 그리고", "행동 실험으로 검증"])]


def build_step(theme, i):
    t = T[theme]
    icon, title, sub = STEPS[i]
    M, CW, CH = 6, 260, 200
    W, H = CW + 2 * M, CH + 2 * M
    d = Doc(W, H, f"{i + 1:02d} {title}: {' '.join(sub)}")
    f = shadow_def(d, t)
    d.add(f'<rect x="{M}" y="{M}" width="{CW}" height="{CH}" rx="16" fill="{t["card"]}" stroke="{t["border"]}" '
          f'stroke-width="1.3"{f}/>',
          f'<rect x="{M + 20}" y="{M + 20}" width="42" height="42" rx="11" fill="{t["accent"]}" '
          f'fill-opacity="{t["tint"]}"/>', lucide(icon, M + 30, M + 30, 22, t["accent"]))
    n, _ = d.text(f"{i + 1:02d}", M + CW - 20, M + 46, 16, "mono", t["muted"], "end")
    ti, tw = d.text(title, M + 20, M + 110, 26, "bold", t["fg"])
    d.add(n, ti)
    assert tw < CW - 36, (title, tw)
    for k, line in enumerate(sub):
        s, w = d.text(line, M + 20, M + 144 + k * 27, 19, "reg", t["muted"])
        assert w < CW - 36, (line, w)
        d.add(s)
    d.save(f"step-{i + 1}-{theme}.svg")


# ---------------------------------------------------------------- cards ----
CARDS = [
    ("dalm", "DALM", "2026 · 진행 중 · 5인 팀 · AI 파트",
     ["서로 다른 사람의 사진에서 우연히 닮은 순간을", "찾아 엽서로 주고받는 앱"],
     ["Flutter", "FastAPI", "AI 사진 매칭"], "rose", "images"),
    ("gradroad", "GradRoad", "2026 · 4인 팀 · 로드맵 생성",
     ["선수과목 그래프로 졸업까지의", "수강 로드맵을 짜 주는 웹"],
     ["Python", "위상정렬", "백트래킹"], "emerald", "route"),
    ("korean-qa", "한국어 QA", "2025 · 개인 · NLP",
     ["KLUE-MRC로 kcbert-base를 파인튜닝한", "한국어 질의응답 데모"],
     ["PyTorch", "Hugging Face", "Gradio"], "violet", "message-circle-question-mark"),
    ("guestbook", "서버리스 방명록", "2025 · 개인 · 클라우드",
     ["부정적인 글은 감정 분석으로 걸러 두는", "AWS 서버리스 방명록"],
     ["Lambda", "DynamoDB", "Comprehend"], "orange", "cloud"),
    ("polioo", "Polioo", "2025 · 4인 팀 · 백엔드",
     ["입력한 내용으로 포트폴리오 페이지를 만들어", "S3에 바로 배포해 주는 서비스"],
     ["Node.js", "MongoDB", "S3"], "blue", "layout-template"),
    ("galaxy-defender", "Galaxy Defender", "2025 · 개인 · 게임",
     ["보스 탄막 패턴과 무한 스테이지가 있는", "Java Swing 종스크롤 슈팅 게임"],
     ["Java", "Swing"], "cyan", "rocket"),
]


def build_card(theme, slug, title, meta, desc, tags, accent, icon):
    t = T[theme]
    a = acc(accent, theme)
    M, CW, CH = 8, 540, 236
    W, H = CW + 2 * M, CH + 2 * M
    d = Doc(W, H, f"{title}: {' '.join(desc)}")
    f = shadow_def(d, t)
    d.add(f'<rect x="{M}" y="{M}" width="{CW}" height="{CH}" rx="16" fill="{t["card"]}" stroke="{t["border"]}" '
          f'stroke-width="1.3"{f}/>',
          f'<rect x="{M + 24}" y="{M + 24}" width="50" height="50" rx="13" fill="{a}" fill-opacity="{t["tint"]}"/>',
          lucide(icon, M + 36, M + 36, 26, a),
          lucide("arrow-up-right", M + CW - 44, M + 26, 20, t["muted"], 2))
    ti, _ = d.text(title, M + 90, M + 52, 25, "bold", t["fg"])
    me, _ = d.text(meta, M + 90, M + 77, 15, "reg", t["muted"])
    d.add(ti, me)
    for k, line in enumerate(desc):
        s, w = d.text(line, M + 24, M + 128 + k * 28, 18.5, "reg", t["fg2"])
        assert w < CW - 48, (slug, line, w)
        d.add(s)
    x = M + 24
    for tag in tags:
        tw = measure(tag, 14, "med")
        w = tw + 24
        d.add(f'<rect x="{x}" y="{M + 178}" width="{w:.1f}" height="30" rx="8" fill="{t["chip"]}" '
              f'stroke="{t["chip_border"]}"/>')
        s, _ = d.text(tag, x + 12, M + 198, 14, "med", t["fg2"])
        d.add(s)
        x += w + 8
    d.save(f"card-{slug}-{theme}.svg")


# ---------------------------------------------------------------- stack ----
STACK = ["Python", "PyTorch", "OpenCV", "Hugging Face", "Jupyter", "Gradio",
         "Node.js", "Express", "MongoDB", "AWS", "Docker", "Linux",
         "React", "TypeScript", "Java", "Git"]


def slugify(name):
    return name.lower().replace(" ", "-").replace(".", "")


def build_chip(theme, name):
    t = T[theme]
    ic = ICONS["brands"][name]
    color = "#" + ic["hex"]
    lum = sum(w * int(color[i:i + 2], 16) for w, i in zip((0.2126, 0.7152, 0.0722), (1, 3, 5)))
    if theme == "dark" and lum < 70:
        color = t["fg"]
    H = 44
    tw = measure(name, 17, "med")
    W = round(14 + 20 + 9 + tw + 16) + 2
    d = Doc(W, H, name)
    d.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="{t["card"]}" '
          f'stroke="{t["border"]}" stroke-width="1.2"/>',
          f'<path transform="translate(15 12) scale({20 / 24:.4f})" d="{ic["path"]}" fill="{color}"/>')
    s, _ = d.text(name, 44, 28.5, 17, "med", t["fg"])
    d.add(s)
    d.save(f"chip-{slugify(name)}-{theme}.svg")


if __name__ == "__main__":
    for theme in ("light", "dark"):
        build_header(theme)
        build_button(theme, "portfolio", "Portfolio", "globe", True)
        build_button(theme, "email", "tyui3024@icloud.com", "mail", False)
        for i in range(len(STEPS)):
            build_step(theme, i)
        for c in CARDS:
            build_card(theme, *c)
        for n in STACK:
            build_chip(theme, n)
    print(len(os.listdir(OUT)), "files")
