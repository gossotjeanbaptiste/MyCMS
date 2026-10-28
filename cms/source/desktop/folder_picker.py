#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sélecteur de dossier - Fenêtre « Sélectionner un dossier » de l'Explorateur Windows
Le navigateur ne peut pas donner le chemin complet d'un dossier : c'est le serveur local qui ouvre la fenêtre.
API Windows IFileOpenDialog via ctypes (pas de dépendance ; tkinter n'est pas embarqué dans l'exécutable).
"""

import ctypes
import os
import threading
from ctypes import wintypes

# Identifiants COM
CLSID_FILE_OPEN_DIALOG = "{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}"
IID_IFILE_OPEN_DIALOG = "{D57C7288-D4AD-4768-BE02-9D969532D960}"
IID_ISHELL_ITEM = "{43826D1E-E718-42EE-BC55-A1E261C37BFE}"

CLSCTX_INPROC_SERVER = 0x1
COINIT_APARTMENTTHREADED = 0x2
FOS_PICKFOLDERS = 0x20
FOS_FORCEFILESYSTEM = 0x40
SIGDN_FILESYSPATH = 0x80058000
HRESULT_CANCELLED = 0x800704C7  # L'utilisateur a fermé la fenêtre sans choisir

# Position des méthodes dans les tables virtuelles (IUnknown, puis IModalWindow, puis IFileDialog)
SHOW, SET_OPTIONS, GET_OPTIONS, SET_FOLDER, SET_TITLE, SET_OK_LABEL, GET_RESULT = 3, 9, 10, 12, 17, 18, 20
RELEASE = 2
GET_DISPLAY_NAME = 5  # IShellItem

_busy = threading.Lock()  # Une seule fenêtre à la fois


class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


def _guid(text):
    guid = _GUID()
    ctypes.oledll.ole32.CLSIDFromString(text, ctypes.byref(guid))
    return guid


def _method(pointer, index, *argtypes):
    """Méthode n° index de l'objet COM (lecture de sa table virtuelle)"""
    vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)
    return lambda *args: prototype(vtable[index])(pointer, *args) & 0xFFFFFFFF


def _release(pointer):
    if pointer:
        _method(pointer, RELEASE)()


def _pick(title, start, result):
    ole32 = ctypes.oledll.ole32
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    dialog = ctypes.c_void_p()
    folder = ctypes.c_void_p()
    item = ctypes.c_void_p()
    try:
        ole32.CoCreateInstance(ctypes.byref(_guid(CLSID_FILE_OPEN_DIALOG)), None, CLSCTX_INPROC_SERVER,
                               ctypes.byref(_guid(IID_IFILE_OPEN_DIALOG)), ctypes.byref(dialog))
        options = wintypes.DWORD()
        _method(dialog, GET_OPTIONS, ctypes.POINTER(wintypes.DWORD))(ctypes.byref(options))
        _method(dialog, SET_OPTIONS, wintypes.DWORD)(options.value | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM)
        _method(dialog, SET_TITLE, wintypes.LPCWSTR)(title)
        _method(dialog, SET_OK_LABEL, wintypes.LPCWSTR)("Choisir ce dossier")

        # Dossier de départ : le chemin déjà saisi s'il existe
        if start and os.path.isdir(start):
            create_item = ctypes.windll.shell32.SHCreateItemFromParsingName
            create_item.restype = ctypes.c_long
            if create_item(os.path.abspath(start), None, ctypes.byref(_guid(IID_ISHELL_ITEM)), ctypes.byref(folder)) == 0:
                _method(dialog, SET_FOLDER, ctypes.c_void_p)(folder)

        # Fenêtre au premier plan du navigateur (la fenêtre active au moment du clic)
        owner = ctypes.windll.user32.GetForegroundWindow()
        hr = _method(dialog, SHOW, wintypes.HWND)(owner)
        if hr == HRESULT_CANCELLED:
            result["cancelled"] = True
            return
        if hr != 0:
            result["error"] = f"Fenêtre de sélection impossible (code 0x{hr:08X})"
            return

        _method(dialog, GET_RESULT, ctypes.POINTER(ctypes.c_void_p))(ctypes.byref(item))
        name = ctypes.c_wchar_p()
        _method(item, GET_DISPLAY_NAME, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p))(SIGDN_FILESYSPATH, ctypes.byref(name))
        result["path"] = name.value
        ole32.CoTaskMemFree(name)
    except OSError as e:
        result["error"] = f"Fenêtre de sélection impossible : {e}"
    finally:
        _release(item)
        _release(folder)
        _release(dialog)
        ole32.CoUninitialize()


def choose_folder(title="Choisir un dossier", start=""):
    """Ouvre la fenêtre et attend le choix. Retourne {"path"}, {"cancelled": True} ou {"error"}."""
    if os.name != "nt":
        return {"error": "La sélection de dossier n'est disponible que sous Windows : saisissez le chemin"}
    if not _busy.acquire(blocking=False):
        return {"error": "Une fenêtre de sélection de dossier est déjà ouverte"}
    try:
        result = {}
        # COM a besoin d'un thread « STA » dédié, indépendant des threads du serveur web
        thread = threading.Thread(target=_pick, args=(title, start, result), daemon=True)
        thread.start()
        thread.join()
        return result
    finally:
        _busy.release()
