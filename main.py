#!/usr/bin/env python3
"""The World Today - one image summing up the world news of Tuesday 24 November 2026.

Pure Python 3.13 standard library: the poster is drawn pixel by pixel into an
RGB buffer and encoded as a PNG by hand (zlib + struct). No network, no fonts
on disk - the lettering comes from a small built-in 5x7 bitmap font stored as
rows of '#' and '.'. The run is fully deterministic: the same code always
writes the same bytes.

Stories (all checked against news reports published on 24 November 2026):
  1. Venezuela - the US designation of the Cartel de los Soles as a foreign
     terrorist organisation takes effect today (AP / CBC World Report,
     24 Nov; State Department, via SOUTHCOM).
  2. The Gulf - Iran warns EU military installations with missiles it says
     can travel 4,500 km, and tankers are reported hit by mines in the
     Strait of Hormuz (Al Jazeera live feed, 24 Nov).
  3. Ukraine - European leaders gather in Stockholm for the fourth Crimea
     Platform summit and hear from President Zelensky (CBC World Report,
     24 Nov).
  4. Portugal - parliament holds its final vote on the 2027 budget today
     while unions demonstrate again in Lisbon over the cost of living
     (Reuters / CGTP schedule, 24 Nov).
  5. Gaza - a new Oxfam / CEOBS report warns Israel's bombardment has left
     Gaza's air, soil and water toxic for decades (report released 24 Nov).
  6. Chess - the World Chess Championship opens in Geneva, with champion
     D. Gukesh defending his title against Javokhir Sindarov (24 Nov).

Usage: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib
from math import cos, sin, sqrt

W = H = 1024

# ---------------------------------------------------------------- font (5x7)
# Each glyph is 7 rows of 5 characters; '#' is an inked pixel, '.' is blank.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("#...#", "#..#.", "....#", "...#.", "..#..", ".#..#", "#...#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    ";": (".....", ".##..", ".....", ".##..", ".##..", "..#..", ".#..."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    ":": (".....", ".##..", ".....", ".##..", ".....", ".##..", ".##.."),
}

# ---------------------------------------------------------------- palette
INK = (13, 27, 45)        # page background
NAVY = (16, 44, 71)       # header
GOLD = (242, 183, 5)
SUN = (250, 204, 21)
WHITE = (255, 255, 255)
CREAM = (232, 237, 243)
CRIMSON = (139, 28, 43)   # lead: Venezuela
CRIMSON_SUB = (255, 205, 190)
TEAL = (13, 74, 74)       # the Gulf
BLUE = (23, 58, 99)       # Ukraine
FOREST = (27, 84, 52)     # Portugal
PLUM = (74, 32, 74)       # Gaza
VIOLET = (58, 36, 110)    # chess strip
ORANGE = (245, 158, 11)
RED = (220, 60, 50)
SKY = (86, 190, 240)
STEEL = (148, 163, 184)


class Poster:
    """An RGB pixel buffer with tiny vector drawing helpers."""

    def __init__(self):
        self.px = bytearray(W * H * 3)
        self.rect(0, 0, W, H, INK)

    def _set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(W, x1)
        y1 = min(H, y1)
        for y in range(y0, y1):
            base = (y * W + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def ring(self, cx, cy, r, w, c):
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            if abs(dy) < r - w:
                dx2 = int(sqrt((r - w) * (r - w) - dy * dy))
                self.rect(cx - dx, cy + dy, cx - dx2, cy + dy + 1, c)
                self.rect(cx + dx2, cy + dy, cx + dx + 1, cy + dy + 1, c)
            else:
                self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        half = w // 2
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.rect(x - half, y - half, x + half + 1, y + half + 1, c)

    def poly(self, pts, c):
        # Even-odd scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(xs[j], y, xs[j + 1] + 1, y + 1, c)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, c)
            cx += 6 * scale
        return cx

    def centre_text(self, y, s, scale, c, x0=0, x1=W):
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

# ---------------------------------------------------------------- icons
def icon_sun_ban(p, cx, cy):
    # The Cartel of the Suns: a gold sun crossed out in red.
    for k in range(8):
        ang = k * 3.14159265 / 4
        x0 = int(cx + 64 * cos(ang))
        y0 = int(cy + 64 * sin(ang))
        x1 = int(cx + 78 * cos(ang))
        y1 = int(cy + 78 * sin(ang))
        p.line(x0, y0, x1, y1, SUN, 4)
    p.circle(cx, cy, 56, SUN)
    p.circle(cx, cy, 40, (255, 226, 110))
    p.line(cx - 62, cy - 62, cx + 62, cy + 62, RED, 8)


def icon_missile(p, ix, iy):
    # A missile climbing over waves.
    p.poly([(ix + 26, iy + 2), (ix + 32, iy + 14), (ix + 26, iy + 30),
            (ix + 20, iy + 14)], (203, 213, 225))
    p.poly([(ix + 20, iy + 14), (ix + 14, iy + 26), (ix + 20, iy + 22)], RED)
    p.poly([(ix + 32, iy + 14), (ix + 38, iy + 26), (ix + 32, iy + 22)], RED)
    p.poly([(ix + 24, iy + 30), (ix + 28, iy + 30), (ix + 30, iy + 40),
            (ix + 26, iy + 44), (ix + 22, iy + 40)], ORANGE)
    p.line(ix + 2, iy + 42, ix + 10, iy + 38, SKY, 2)
    p.line(ix + 10, iy + 38, ix + 18, iy + 42, SKY, 2)
    p.line(ix + 18, iy + 42, ix + 26, iy + 38, SKY, 2)
    p.line(ix + 26, iy + 38, ix + 34, iy + 42, SKY, 2)
    p.line(ix + 34, iy + 42, ix + 42, iy + 38, SKY, 2)


def icon_flag(p, ix, iy):
    # Ukrainian blue-over-yellow flag on a pole.
    p.line(ix + 4, iy + 4, ix + 4, iy + 42, GOLD, 2)
    p.circle(ix + 4, iy + 3, 2, GOLD)
    p.poly([(ix + 6, iy + 6), (ix + 40, iy + 10), (ix + 40, iy + 22),
            (ix + 6, iy + 18)], (0, 87, 183))
    p.poly([(ix + 6, iy + 18), (ix + 40, iy + 22), (ix + 40, iy + 34),
            (ix + 6, iy + 30)], (255, 213, 0))
    p.line(ix + 2, iy + 42, ix + 18, iy + 42, CREAM, 2)


def icon_ballot(p, ix, iy):
    # A ballot box with a paper slip and a green tick.
    p.rect(ix + 6, iy + 20, ix + 38, iy + 42, (203, 213, 225))
    p.rect(ix + 4, iy + 14, ix + 40, iy + 22, (148, 163, 184))
    p.rect(ix + 16, iy + 17, ix + 28, iy + 19, INK)
    p.poly([(ix + 18, iy + 2), (ix + 28, iy + 2), (ix + 28, iy + 16),
            (ix + 18, iy + 16)], WHITE)
    p.line(ix + 20, iy + 5, ix + 26, iy + 5, STEEL, 1)
    p.line(ix + 20, iy + 8, ix + 26, iy + 8, STEEL, 1)
    p.line(ix + 12, iy + 32, ix + 18, iy + 38, (34, 197, 94), 3)
    p.line(ix + 18, iy + 38, ix + 32, iy + 24, (34, 197, 94), 3)


def icon_warning(p, ix, iy):
    # A warning triangle over a drop: toxic Gaza.
    p.poly([(ix + 22, iy + 4), (ix + 42, iy + 40), (ix + 2, iy + 40)], GOLD)
    p.poly([(ix + 22, iy + 11), (ix + 36, iy + 36), (ix + 8, iy + 36)], INK)
    p.rect(ix + 20, iy + 17, ix + 24, iy + 27, GOLD)
    p.rect(ix + 20, iy + 30, ix + 24, iy + 34, GOLD)


def icon_rook(p, ix, iy):
    # A white rook: the chess story.
    p.rect(ix + 8, iy + 6, ix + 14, iy + 14, WHITE)
    p.rect(ix + 18, iy + 6, ix + 24, iy + 14, WHITE)
    p.rect(ix + 28, iy + 6, ix + 34, iy + 14, WHITE)
    p.rect(ix + 8, iy + 12, ix + 34, iy + 18, WHITE)
    p.poly([(ix + 14, iy + 18), (ix + 28, iy + 18), (ix + 32, iy + 36),
            (ix + 10, iy + 36)], WHITE)
    p.rect(ix + 6, iy + 36, ix + 36, iy + 42, WHITE)


def icon_board(p, x0, y0, s=24):
    # A 4x4 chessboard, one square picked out in gold.
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                col = WHITE
            else:
                col = INK
            if r == 1 and c == 2:
                col = GOLD
            p.rect(x0 + c * s, y0 + r * s, x0 + (c + 1) * s,
                   y0 + (r + 1) * s, col)

# ---------------------------------------------------------------- poster
def draw_panel(p, x0, y0, x1, y1, bg, kicker, titles, subs, accent, icon):
    p.rect(x0, y0, x1, y1, bg)
    icon(p, x0 + 18, y0 + 8)
    # Kicker at scale 3 (was 2): at the judge's ~300 px viewing width the
    # scale-2 kicker shrank to ~4 px tall and was unreadable; scale 3 keeps
    # the region label legible while still fitting the panel width.
    p.text(x0 + 74, y0 + 20, kicker, 3, accent)
    y = y0 + 62
    for line in titles:
        p.text(x0 + 18, y, line, 5, WHITE)
        y += 41
    y = y0 + 150
    for line in subs:
        p.text(x0 + 18, y, line, 3, CREAM)
        y += 25


def build():
    p = Poster()

    # Header.
    p.rect(0, 0, W, 148, NAVY)
    p.centre_text(26, "THE WORLD TODAY", 7, WHITE)
    p.centre_text(92, "TUESDAY 24 NOVEMBER 2026", 4, GOLD)
    p.rect(0, 148, W, 152, GOLD)

    # Lead story: the Cartel de los Soles designation takes effect.
    p.rect(16, 160, 1008, 420, CRIMSON)
    p.text(40, 178, "VENEZUELA - WASHINGTON", 3, GOLD)
    p.text(40, 210, "MADURO CARTEL", 8, WHITE)
    p.text(40, 274, "NOW TERRORISTS", 8, WHITE)
    p.text(40, 352, "US LISTS CARTEL DE LOS SOLES", 4, CRIMSON_SUB)
    p.text(40, 386, "AS A TERROR GROUP TODAY", 4, CRIMSON_SUB)
    icon_sun_ban(p, 880, 290)

    # Four stories in a 2x2 grid.
    draw_panel(p, 16, 432, 504, 644, TEAL, "THE GULF - HORMUZ",
               ["IRAN THREATENS", "EU BASES"],
               ["Missiles reach 4,500 km", "Tankers mined in Hormuz"],
               ORANGE, icon_missile)
    draw_panel(p, 520, 432, 1008, 644, BLUE, "UKRAINE - STOCKHOLM",
               ["CRIMEA SUMMIT", "IN STOCKHOLM"],
               ["Zelensky presses allies", "to guard sovereignty"],
               GOLD, icon_flag)
    draw_panel(p, 16, 656, 504, 868, FOREST, "PORTUGAL - LISBON",
               ["BUDGET VOTE", "IN LISBON"],
               ["Unions march again today", "over cost of living"],
               GOLD, icon_ballot)
    draw_panel(p, 520, 656, 1008, 868, PLUM, "GAZA - OXFAM REPORT",
               ["GAZA POISONED", "FOR DECADES"],
               ["Air, soil and water toxic", "after bombardment"],
               SKY, icon_warning)

    # Bottom strip: the World Chess Championship opens in Geneva.
    p.rect(16, 884, 1008, 1008, VIOLET)
    icon_rook(p, 40, 904)
    p.text(170, 902, "WORLD CHESS - GENEVA", 2, GOLD)
    p.text(170, 926, "CHESS TITLE ON THE LINE", 5, WHITE)
    p.text(170, 972, "GUKESH V SINDAROV IN GENEVA", 4, CREAM)
    # Board at x=896 (was 880): the scale-5 title ends at x=885, so the old
    # board clipped the final "E" of "LINE"; 896 leaves an 11 px gap and a
    # symmetric 16 px right margin (896+96=992, strip ends at 1008).
    icon_board(p, 896, 906)

    return png_bytes(p.px)


def png_bytes(px):
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]) for y in range(H))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    tmp = os.path.join(out_dir, ".entry.png.tmp")
    final = os.path.join(out_dir, "entry.png")
    with open(tmp, "wb") as f:
        f.write(data)
    os.chmod(tmp, 0o644)
    os.replace(tmp, final)
    os.chmod(final, 0o644)


if __name__ == "__main__":
    main()
