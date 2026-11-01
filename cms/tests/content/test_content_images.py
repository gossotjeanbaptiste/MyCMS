#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de content : images allégées à l'import (taille, orientation, métadonnées)"""

import io
import random

import pytest
from PIL import Image

from content.media.image_optimizer import MAX_SIDE, optimize, size_label


def photo(size=(4000, 3000), orientation=None, gps=False, mode="RGB", fmt="JPEG"):
    """Photo bruitée (peu compressible, comme une vraie), avec ses métadonnées EXIF"""
    random.seed(1)
    image = Image.frombytes("RGB", size, random.randbytes(size[0] * size[1] * 3)).convert(mode)
    exif = Image.Exif()
    if orientation:
        exif[0x0112] = orientation
    if gps:
        exif[0x8825] = {2: (48.0, 5.0, 0.0)}  # GPSInfo : latitude
    out = io.BytesIO()
    image.save(out, fmt, quality=98, exif=exif.tobytes()) if fmt == "JPEG" else image.save(out, fmt)
    return out.getvalue()


def opened(data):
    return Image.open(io.BytesIO(data))


def test_big_phone_photo_is_resized_and_lighter():
    original = photo()
    data, lighter = optimize(original, ".jpg")
    assert lighter and len(data) < len(original) / 3
    assert opened(data).size == (MAX_SIDE, 1440)  # Proportions gardées


def test_photo_is_turned_upright_and_loses_its_metadata():
    data, lighter = optimize(photo((3000, 2000), orientation=6, gps=True), ".jpeg")
    image = opened(data)
    assert lighter and image.size == (1280, MAX_SIDE)  # Tournée d'un quart de tour, puis réduite
    assert not image.getexif()  # Ni orientation ni GPS


def test_png_keeps_transparency():
    original = photo((2500, 2500), mode="RGBA", fmt="PNG")
    data, lighter = optimize(original, ".png")
    image = opened(data)
    assert lighter and image.format == "PNG" and image.mode == "RGBA" and image.size == (MAX_SIDE, MAX_SIDE)


@pytest.mark.parametrize("suffix", [".gif", ".webp", ".avif"])
def test_other_formats_untouched(suffix):
    assert optimize(b"donnees", suffix) == (b"donnees", False)


def test_small_or_unreadable_images_are_kept():
    small = photo((800, 600))
    data, lighter = optimize(small, ".jpg")
    assert opened(data).size == (800, 600)  # Pas agrandie
    assert lighter is (data != small) and len(data) <= len(small)  # Jamais plus lourde que l'original
    assert optimize(b"pas une image", ".png") == (b"pas une image", False)


def test_size_label():
    assert size_label(6_500_000) == "6,2 Mo" and size_label(420_000) == "410 Ko" and size_label(10) == "1 Ko"


def test_upload_reports_the_saving(site_client, git_site):
    original = photo((2400, 1800))  # Sous la limite de 10 Mo de l'envoi
    response = site_client.post("/api/images", data={"page": "index.html", "file": (io.BytesIO(original), "photo.jpg")},
                                content_type="multipart/form-data")
    result = response.get_json()
    assert result["lighter"].startswith(f"{size_label(len(original))} → ")
    assert opened((git_site / "images" / "photo.jpg").read_bytes()).size == (MAX_SIDE, 1440)
