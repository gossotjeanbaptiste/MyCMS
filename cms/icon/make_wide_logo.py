#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo horizontal de l'en-tête (cms/web/static/logo-wide.png) : les logos Python et Git de logo.ico
à gauche, « MyCMS » à droite (« My » jaune Python, « CMS » orange Git), sur la même tuile bleu nuit.

À relancer après un changement de logo.ico : python cms/icon/make_wide_logo.py
(sous Windows : police Segoe UI Black, comme dans l'icône)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ICON = Path(__file__).with_name("logo.ico")
OUTPUT = Path(__file__).resolve().parents[1] / "web" / "static" / "logo-wide.png"
FONT = Path("C:/Windows/Fonts/seguibl.ttf")
NAVY = (30, 41, 59, 255)
YELLOW = "#FFD43B"
ORANGE = "#F05133"
HEIGHT = 128  # Affiché en 40 px : net aussi sur un écran haute densité
PADDING = 0.14  # Marges, en fraction de la hauteur
TEXT_SIZE = 0.48


def logos_only(icon):
    """Logos Python et Git de l'image 256 px, sans le texte : haut de l'image, recadré au plus près"""
    top = icon.crop((0, 0, 256, 160))
    mask = Image.new("L", top.size, 0)
    pixels, marks = top.load(), mask.load()
    for y in range(top.height):
        for x in range(12, top.width - 12):  # Sans les coins arrondis de la tuile
            r, g, b, a = pixels[x, y]
            if a > 200 and abs(r - NAVY[0]) + abs(g - NAVY[1]) + abs(b - NAVY[2]) > 60:
                marks[x, y] = 255
    return top.crop(mask.getbbox())


def main():
    icon = Image.open(ICON)
    icon.size = (256, 256)
    icon = icon.convert("RGBA")
    pad = round(HEIGHT * PADDING)
    logos = logos_only(icon)
    logo_height = HEIGHT - 2 * pad
    logos = logos.resize((round(logos.width * logo_height / logos.height), logo_height), Image.LANCZOS)

    font = ImageFont.truetype(str(FONT), round(HEIGHT * TEXT_SIZE))
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    my_width = measure.textlength("My", font=font)
    left, top, right, bottom = measure.textbbox((0, 0), "MyCMS", font=font, anchor="ls")
    gap = round(pad * 0.9)
    width = pad + logos.width + gap + round(right - left) + pad

    banner = Image.new("RGBA", (width, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle((0, 0, width - 1, HEIGHT - 1), radius=round(HEIGHT * 0.22), fill=NAVY)
    banner.alpha_composite(logos, (pad, pad))
    # Texte centré verticalement d'après ses limites réelles (le « y » descend sous la ligne)
    x = pad + logos.width + gap - left
    baseline = (HEIGHT - (bottom - top)) / 2 - top
    draw.text((x, baseline), "My", font=font, fill=YELLOW, anchor="ls")
    draw.text((x + my_width, baseline), "CMS", font=font, fill=ORANGE, anchor="ls")
    banner.save(OUTPUT, optimize=True)
    print(f"{OUTPUT} : {banner.width} x {banner.height}")


if __name__ == "__main__":
    main()
