"""Draw results/<experiment>.json as an SVG forest plot: one line per row and model, the effect as a marker, the
simultaneous interval as a bar, the verdict in words at the right. Model is shown by marker shape and by colour
(Okabe-Ito blue and vermillion, which also differ in lightness), and named in the legend.

  python3 scripts/forest.py results/2026-11-04.json > results/2026-11-04.svg
"""
import json
import sys

MODELS = {"haiku": ("#0072B2", "circle", "Claude Haiku 5.5"), "deepseek-flash": ("#D55E00", "square", "DeepSeek Flash")}
W, LEFT, RIGHT, ROW, TOP = 760, 200, 150, 26, 54
LO, HI = -0.40, 0.40


def x(v: float) -> float:
    v = max(LO, min(HI, v))
    return LEFT + (v - LO) / (HI - LO) * (W - LEFT - RIGHT)


def marker(shape: str, cx: float, cy: float, colour: str) -> str:
    if shape == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{colour}"/>'
    return f'<rect x="{cx - 5:.1f}" y="{cy - 5:.1f}" width="10" height="10" fill="{colour}"/>'


def main(path: str) -> None:
    res = json.load(open(path))
    lines = []
    for model, (colour, shape, _) in MODELS.items():
        for r in res.get(model, {}).get("rows", []):
            lines.append((r, model, colour, shape))
    order = list(dict.fromkeys(r["id"] for r, *_ in lines))
    lines.sort(key=lambda t: (order.index(t[0]["id"]), list(MODELS).index(t[1])))
    h = TOP + ROW * len(lines) + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" font-family="system-ui, sans-serif" '
           f'font-size="13">', f'<rect width="{W}" height="{h}" fill="#ffffff"/>']
    for v in (-0.4, -0.2, 0.0, 0.2, 0.4):
        stroke = "#222222" if v == 0 else "#dddddd"
        out.append(f'<line x1="{x(v):.1f}" y1="{TOP - 8}" x2="{x(v):.1f}" y2="{h - 30}" stroke="{stroke}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 12}" text-anchor="middle" fill="#444444">{100 * v:+.0f} pp</text>')
    lx = LEFT
    for model, (colour, shape, name) in MODELS.items():
        if model in res:
            out.append(marker(shape, lx, 22, colour))
            out.append(f'<text x="{lx + 10}" y="26" fill="#222222">{name}</text>')
            lx += 170
    out.append(f'<text x="{W - RIGHT + 10}" y="26" fill="#222222">verdict</text>')
    prev = None
    for i, (r, model, colour, shape) in enumerate(lines):
        cy = TOP + ROW * i + ROW / 2
        if r["id"] != prev:
            out.append(f'<text x="{LEFT - 12}" y="{cy + 4:.1f}" text-anchor="end" fill="#222222">{r["id"]}</text>')
            prev = r["id"]
        out.append(f'<line x1="{x(r["lo"]):.1f}" y1="{cy:.1f}" x2="{x(r["hi"]):.1f}" y2="{cy:.1f}" '
                   f'stroke="{colour}" stroke-width="3"/>')
        out.append(marker(shape, x(r["effect"]), cy, colour))
        out.append(f'<text x="{W - RIGHT + 10}" y="{cy + 4:.1f}" fill="#222222">{r["verdict"]}</text>')
    out.append("</svg>")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
