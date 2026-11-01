#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Images allégées à l'import : une photo de téléphone (4000 pixels, 6 Mo) ralentit le site et alourdit le dépôt
pour toujours (Git garde chaque version). Elle est réduite à 1920 pixels au plus, remise droite (orientation
EXIF), recompressée, et débarrassée de ses métadonnées, dont la position GPS de la prise de vue.

JPEG et PNG seulement : les GIF (parfois animés), WebP et AVIF sont gardés tels quels. Si le résultat
n'est pas plus léger, ou si l'image est illisible, l'original est gardé.
"""

import io

from PIL import Image, ImageOps

MAX_SIDE = 1920
JPEG_QUALITY = 85
OPTIMIZED = {".jpg", ".jpeg", ".png"}


def _encode(image, suffix):
    out = io.BytesIO()
    # Le profil de couleur est gardé (photos en Display P3) ; les métadonnées EXIF ne sont pas recopiées
    icc = image.info.get("icc_profile")
    if suffix == ".png":
        image.save(out, "PNG", optimize=True, icc_profile=icc)
    else:
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True, icc_profile=icc)
    return out.getvalue()


def optimize(data, suffix):
    """(octets à enregistrer, True si l'image a été allégée) ; suffix : extension en minuscules"""
    if suffix not in OPTIMIZED:
        return data, False
    try:
        with Image.open(io.BytesIO(data)) as original:
            image = ImageOps.exif_transpose(original)
            if max(image.size) > MAX_SIDE:
                image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            result = _encode(image, suffix)
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        return data, False
    return (result, True) if len(result) < len(data) else (data, False)


def size_label(count):
    """« 6,2 Mo », « 410 Ko »"""
    if count >= 1024 * 1024:
        return f"{count / (1024 * 1024):.1f} Mo".replace(".", ",")
    return f"{max(1, round(count / 1024))} Ko"
