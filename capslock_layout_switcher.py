#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Caps Lock -> keyboard layout switcher for Windows 10/11.
On every Caps Lock press:
  1. Switches keyboard layout to the next one
  2. Checks if Caps Lock is on and turns it off if needed

Tray icon (right click):
  - Copy PY source code -- copies the full source code to clipboard
  - Exit -- closes the program

Build .exe (requires Python + pip):
    pip install pyinstaller
    python capslock_layout_switcher.py        # this auto-creates icon.ico
    pyinstaller --onefile --noconsole --icon=icon.ico --add-data "capslock_layout_switcher.py;." capslock_layout_switcher.py
    The .exe will be in the dist/ folder.

Run:
    python capslock_layout_switcher.py        (console visible -- for debugging)

Autostart (no console window):
    Copy dist\capslock_switcher.exe to:
    Win+R -> shell:startup

Requires: Windows, Python 3.x
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import time
import traceback

# ═══════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════
ENABLE_LOGGING = 0      # 0 = no log file created
ENABLE_TRAY_ICON = 1    # 0 = run without tray icon

# ═══════════════════════════════════════════════════════════════════
#  RUNTIME PATHS (.py vs frozen .exe)
# ═══════════════════════════════════════════════════════════════════
def _get_app_dir() -> str:
    """Return the directory where the app lives (.py or .exe)."""
    if hasattr(sys, '_MEIPASS'):
        # Frozen pyinstaller .exe -- sys.executable is the .exe path
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Running as .py
        return os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════
LOG_PATH = os.path.join(_get_app_dir(), "capslock_switcher.log")
_log_file = None

def log_init():
    if not ENABLE_LOGGING:
        return
    global _log_file
    try:
        _log_file = open(LOG_PATH, "w", encoding="utf-8")
    except Exception:
        _log_file = None

def log(msg: str):
    if not ENABLE_LOGGING or not _log_file:
        return
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    try:
        _log_file.write(line + "\n")
        _log_file.flush()
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════
#  WINDOWS API CONSTANTS
# ═══════════════════════════════════════════════════════════════════
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_CAPITAL = 0x14
KEYEVENTF_KEYUP = 0x0002

WM_INPUTLANGCHANGEREQUEST = 0x0050
INPUTLANGCHANGE_FORWARD = 0x0002

# Tray
WM_USER = 0x0400
WM_TRAY_CALLBACK = WM_USER + 1
WM_COMMAND = 0x0111
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0201
WM_DESTROY = 0x0002
NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 0x01
NIF_ICON = 0x02
NIF_TIP = 0x04
NIF_INFO = 0x10
IDI_APPLICATION = 32512
IDC_ARROW = 32512

# Single-instance guard
ERROR_ALREADY_EXISTS = 183
WM_CLOSE = 0x0010
MB_YESNO = 0x00000004
MB_ICONQUESTION = 0x00000020
MB_TOPMOST = 0x00040000
IDYES = 6

# GDI icon creation
TRANSPARENT = 1
WHITE_BRUSH = 0
FW_BOLD = 700

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
    ]

# Menu
MF_STRING = 0x0000
TPM_RETURNCMD = 0x0100
TPM_RIGHTBUTTON = 0x0002

# Clipboard
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
LRESULT = ctypes.c_ssize_t
HKL = wintypes.HANDLE

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# ═══════════════════════════════════════════════════════════════════
#  STRUCTURES
# ═══════════════════════════════════════════════════════════════════
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wintypes.HICON),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, WPARAM, LPARAM)
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, WPARAM, LPARAM)

_CallNextHookEx = user32.CallNextHookEx
_CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, WPARAM, LPARAM]
_CallNextHookEx.restype = LRESULT

_RegisterClassExW = user32.RegisterClassExW
_RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
_RegisterClassExW.restype = wintypes.ATOM

_DefWindowProcW = user32.DefWindowProcW
_DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
_DefWindowProcW.restype = LRESULT

_GlobalAlloc = kernel32.GlobalAlloc
_GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_GlobalAlloc.restype = wintypes.HANDLE

_GlobalLock = kernel32.GlobalLock
_GlobalLock.argtypes = [wintypes.HANDLE]
_GlobalLock.restype = ctypes.c_void_p

_GlobalUnlock = kernel32.GlobalUnlock
_GlobalUnlock.argtypes = [wintypes.HANDLE]
_GlobalUnlock.restype = wintypes.BOOL

_GlobalFree = kernel32.GlobalFree
_GlobalFree.argtypes = [wintypes.HANDLE]
_GlobalFree.restype = wintypes.HANDLE

_SetClipboardData = user32.SetClipboardData
_SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
_SetClipboardData.restype = wintypes.HANDLE

_CreateSolidBrush = ctypes.windll.gdi32.CreateSolidBrush
_CreateSolidBrush.argtypes = [wintypes.COLORREF]
_CreateSolidBrush.restype = wintypes.HBRUSH

_CreateIconIndirect = user32.CreateIconIndirect
_CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
_CreateIconIndirect.restype = wintypes.HICON

_GetStockObject = ctypes.windll.gdi32.GetStockObject
_GetStockObject.argtypes = [ctypes.c_int]
_GetStockObject.restype = wintypes.HGDIOBJ

_SelectObject = ctypes.windll.gdi32.SelectObject
_SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_SelectObject.restype = wintypes.HGDIOBJ

_DeleteObject = ctypes.windll.gdi32.DeleteObject
_DeleteObject.argtypes = [wintypes.HGDIOBJ]
_DeleteObject.restype = wintypes.BOOL

_DeleteDC = ctypes.windll.gdi32.DeleteDC
_DeleteDC.argtypes = [wintypes.HDC]
_DeleteDC.restype = wintypes.BOOL

_CreateCompatibleDC = ctypes.windll.gdi32.CreateCompatibleDC
_CreateCompatibleDC.argtypes = [wintypes.HDC]
_CreateCompatibleDC.restype = wintypes.HDC

_CreateCompatibleBitmap = ctypes.windll.gdi32.CreateCompatibleBitmap
_CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
_CreateCompatibleBitmap.restype = wintypes.HBITMAP

_CreateBitmap = ctypes.windll.gdi32.CreateBitmap
_CreateBitmap.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.UINT, wintypes.UINT, ctypes.c_void_p]
_CreateBitmap.restype = wintypes.HBITMAP

_FillRect = user32.FillRect
_FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), wintypes.HBRUSH]
_FillRect.restype = ctypes.c_int

_SetTextColor = ctypes.windll.gdi32.SetTextColor
_SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
_SetTextColor.restype = wintypes.COLORREF

_SetBkMode = ctypes.windll.gdi32.SetBkMode
_SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
_SetBkMode.restype = ctypes.c_int

_TextOutW = ctypes.windll.gdi32.TextOutW
_TextOutW.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.LPCWSTR, ctypes.c_int]
_TextOutW.restype = wintypes.BOOL

_CreateFontW = ctypes.windll.gdi32.CreateFontW
_CreateFontW.argtypes = [
    ctypes.c_int,   # cHeight
    ctypes.c_int,   # cWidth
    ctypes.c_int,   # cEscapement
    ctypes.c_int,   # cOrientation
    ctypes.c_int,   # cWeight
    wintypes.DWORD, # bItalic
    wintypes.DWORD, # bUnderline
    wintypes.DWORD, # bStrikeOut
    wintypes.DWORD, # iCharSet
    wintypes.DWORD, # iOutPrecision
    wintypes.DWORD, # iClipPrecision
    wintypes.DWORD, # iQuality
    wintypes.DWORD, # iPitchAndFamily
    wintypes.LPCWSTR # pszFaceName
]
_CreateFontW.restype = wintypes.HFONT

_CreateDIBSection = ctypes.windll.gdi32.CreateDIBSection
_CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
_CreateDIBSection.restype = wintypes.HBITMAP

_MessageBoxW = user32.MessageBoxW
_MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
_MessageBoxW.restype = ctypes.c_int

_PostMessageW = user32.PostMessageW
_PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
_PostMessageW.restype = wintypes.BOOL

_FindWindowW = user32.FindWindowW
_FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_FindWindowW.restype = wintypes.HWND

_CreateMutexW = kernel32.CreateMutexW
_CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
_CreateMutexW.restype = wintypes.HANDLE

# ═══════════════════════════════════════════════════════════════════
#  GLOBALS
# ═══════════════════════════════════════════════════════════════════
_g_hwnd = None
_g_nid = None
_g_hMenu = None
_g_hCustomIcon = None
_g_running = True

# ═══════════════════════════════════════════════════════════════════
#  CLIPBOARD
# ═══════════════════════════════════════════════════════════════════
def copy_to_clipboard(text: str) -> bool:
    log("  clipboard: OpenClipboard...")
    if not user32.OpenClipboard(None):
        err = kernel32.GetLastError()
        log(f"  clipboard: OpenClipboard failed, err={err}")
        return False
    log("  clipboard: OpenClipboard OK")
    try:
        log("  clipboard: EmptyClipboard...")
        if not user32.EmptyClipboard():
            err = kernel32.GetLastError()
            log(f"  clipboard: EmptyClipboard failed, err={err}")
        log("  clipboard: EmptyClipboard OK")

        data = text.encode("utf-16le") + b"\x00\x00"
        size = len(data)
        log(f"  clipboard: data size={size}")

        log("  clipboard: GlobalAlloc...")
        h_global = _GlobalAlloc(GMEM_MOVEABLE, size)
        if not h_global:
            err = kernel32.GetLastError()
            log(f"  clipboard: GlobalAlloc failed, err={err}")
            return False
        log(f"  clipboard: GlobalAlloc h_global={h_global}")

        log("  clipboard: GlobalLock...")
        ptr = _GlobalLock(h_global)
        if not ptr:
            err = kernel32.GetLastError()
            log(f"  clipboard: GlobalLock failed, err={err}")
            _GlobalFree(h_global)
            return False
        log(f"  clipboard: GlobalLock ptr={ptr}")

        ctypes.memmove(ptr, data, size)
        log("  clipboard: memmove done")

        _GlobalUnlock(h_global)
        log("  clipboard: GlobalUnlock done")

        log("  clipboard: SetClipboardData...")
        result = _SetClipboardData(CF_UNICODETEXT, h_global)
        log(f"  clipboard: SetClipboardData returned={result}")
        return bool(result)
    except Exception as exc:
        log(f"  clipboard: EXCEPTION {exc}")
        return False
    finally:
        user32.CloseClipboard()
        log("  clipboard: CloseClipboard")

# ═══════════════════════════════════════════════════════════════════
#  SOURCE CODE LOADER (works from .py and frozen .exe)
# ═══════════════════════════════════════════════════════════════════
def get_source_code() -> str:
    """Read the bundled source file. Requires PyInstaller --add-data."""
    filename = 'capslock_layout_switcher.py'

    if hasattr(sys, '_MEIPASS'):
        # Frozen .exe built with --add-data
        base = sys._MEIPASS
    else:
        # Running as .py script
        base = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(base, filename)
    log(f"  source: reading {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════
#  TRAY
# ═══════════════════════════════════════════════════════════════════
MENU_ID_COPY = 1001
MENU_ID_EXIT = 1002

def create_tray_menu():
    h_menu = user32.CreatePopupMenu()
    user32.AppendMenuW(h_menu, MF_STRING, MENU_ID_COPY, "Copy PY source code")
    user32.AppendMenuW(h_menu, MF_STRING, MENU_ID_EXIT, "Exit")
    return h_menu

def show_tray_menu(hwnd):
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    user32.SetForegroundWindow(hwnd)
    cmd = user32.TrackPopupMenu(
        _g_hMenu,
        TPM_RETURNCMD | TPM_RIGHTBUTTON,
        pt.x, pt.y,
        0, hwnd, None
    )
    if cmd == MENU_ID_EXIT:
        log("Tray: Exit selected")
        global _g_running
        _g_running = False
        user32.PostQuitMessage(0)
    elif cmd == MENU_ID_COPY:
        log("Tray: Copy source selected")
        try:
            source = get_source_code()
            if copy_to_clipboard(source):
                _g_nid.szInfoTitle = "CapsLock Switcher"
                _g_nid.szInfo = "Source code copied to clipboard!"
                _g_nid.dwInfoFlags = 0x01
            else:
                _g_nid.szInfoTitle = "CapsLock Switcher"
                _g_nid.szInfo = "Clipboard copy failed"
                _g_nid.dwInfoFlags = 0x03  # NIIF_ERROR
            _g_nid.uFlags = NIF_INFO
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(_g_nid))
        except Exception as exc:
            log(f"  copy error: {exc}")
            _g_nid.szInfoTitle = "CapsLock Switcher"
            _g_nid.szInfo = f"Failed to copy source: {exc}"
            _g_nid.dwInfoFlags = 0x03
            _g_nid.uFlags = NIF_INFO
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(_g_nid))

@WNDPROC
def tray_wndproc(hwnd, msg, w_param, l_param):
    if msg == WM_TRAY_CALLBACK:
        if l_param == WM_RBUTTONUP or l_param == WM_LBUTTONUP:
            show_tray_menu(hwnd)
        return 0
    elif msg == WM_COMMAND:
        cmd_id = w_param & 0xFFFF
        if cmd_id == MENU_ID_EXIT:
            global _g_running
            _g_running = False
            user32.PostQuitMessage(0)
        elif cmd_id == MENU_ID_COPY:
            try:
                source = get_source_code()
                copy_to_clipboard(source)
            except Exception:
                pass
        return 0
    elif msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return _DefWindowProcW(hwnd, msg, w_param, l_param)

def init_tray():
    if not ENABLE_TRAY_ICON:
        log("Tray disabled")
        return True

    global _g_hwnd, _g_nid, _g_hMenu

    wndclass = WNDCLASSEXW()
    wndclass.cbSize = ctypes.sizeof(wndclass)
    wndclass.lpfnWndProc = ctypes.cast(tray_wndproc, ctypes.c_void_p).value
    wndclass.hInstance = kernel32.GetModuleHandleW(None)
    wndclass.lpszClassName = "CapsLockSwitcherTray"
    wndclass.hCursor = user32.LoadCursorW(None, IDC_ARROW)

    if not _RegisterClassExW(ctypes.byref(wndclass)):
        log(f"RegisterClassExW failed: {kernel32.GetLastError()}")
        return False

    _g_hwnd = user32.CreateWindowExW(
        0,
        "CapsLockSwitcherTray",
        "CapsLock Switcher",
        0,
        0, 0, 0, 0,
        None, None,
        kernel32.GetModuleHandleW(None),
        None
    )
    if not _g_hwnd:
        log(f"CreateWindowExW failed: {kernel32.GetLastError()}")
        return False

    global _g_hCustomIcon
    _g_hCustomIcon = create_gdi_icon(32)
    h_icon = _g_hCustomIcon if _g_hCustomIcon else user32.LoadIconW(None, IDI_APPLICATION)
    _g_hMenu = create_tray_menu()

    nid = NOTIFYICONDATAW()
    nid.cbSize = ctypes.sizeof(nid)
    nid.hWnd = _g_hwnd
    nid.uID = 1
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    nid.uCallbackMessage = WM_TRAY_CALLBACK
    nid.hIcon = h_icon
    nid.szTip = "CapsLock Layout Switcher"

    _g_nid = nid

    if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
        log(f"Shell_NotifyIconW failed: {kernel32.GetLastError()}")
        return False

    log("Tray icon initialized")
    return True

def _draw_icon_content(hdc, size: int, text: str):
    """Draw blue square + white bold text on a DC."""
    rc = RECT(0, 0, size, size)
    blue_brush = _CreateSolidBrush(0x00D77800)  # RGB(0, 120, 215)
    _FillRect(hdc, ctypes.byref(rc), blue_brush)
    _DeleteObject(blue_brush)

    font = _CreateFontW(
        -int(size * 0.55),
        0, 0, 0,
        FW_BOLD,
        0, 0, 0,
        0, 0, 0, 0,
        0,
        "Segoe UI"
    )
    _SelectObject(hdc, font)
    _SetTextColor(hdc, 0x00FFFFFF)  # white
    _SetBkMode(hdc, TRANSPARENT)

    # Center text
    text_len = len(text)
    x = size // 2 - (size * text_len // 5)
    y = size // 6
    _TextOutW(hdc, x, y, text, text_len)
    _DeleteObject(font)


def create_gdi_icon(size: int = 32) -> wintypes.HICON:
    """Create a blue-square-with-white-CL icon in memory using GDI."""
    hdc_screen = user32.GetDC(None)
    hdc_color = _CreateCompatibleDC(hdc_screen)
    hdc_mask = _CreateCompatibleDC(hdc_screen)

    hbm_color = _CreateCompatibleBitmap(hdc_screen, size, size)
    hbm_mask = _CreateBitmap(size, size, 1, 1, None)

    old_color = _SelectObject(hdc_color, hbm_color)
    old_mask = _SelectObject(hdc_mask, hbm_mask)

    # AND mask: all white = fully opaque
    rc = RECT(0, 0, size, size)
    white_brush = _GetStockObject(WHITE_BRUSH)
    _FillRect(hdc_mask, ctypes.byref(rc), white_brush)

    # Color bitmap
    _draw_icon_content(hdc_color, size, "CL")

    # Create icon
    ii = ICONINFO()
    ii.fIcon = True
    ii.xHotspot = 0
    ii.yHotspot = 0
    ii.hbmMask = hbm_mask
    ii.hbmColor = hbm_color
    h_icon = _CreateIconIndirect(ctypes.byref(ii))

    # Cleanup
    _SelectObject(hdc_color, old_color)
    _SelectObject(hdc_mask, old_mask)
    _DeleteObject(hbm_color)
    _DeleteObject(hbm_mask)
    _DeleteDC(hdc_color)
    _DeleteDC(hdc_mask)
    user32.ReleaseDC(None, hdc_screen)

    log(f"GDI icon created, size={size}x{size}")
    return h_icon


def generate_ico_file(out_path: str, size: int = 256):
    """Generate a .ico file from GDI-rendered bitmap (for pyinstaller --icon)."""
    hdc_screen = user32.GetDC(None)

    # Setup DIB section for direct pixel access
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = size
    bmi.bmiHeader.biHeight = -size  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    pixels_ptr = ctypes.c_void_p()
    hbm = _CreateDIBSection(hdc_screen, ctypes.byref(bmi), 0, ctypes.byref(pixels_ptr), None, 0)
    hdc = _CreateCompatibleDC(hdc_screen)
    old = _SelectObject(hdc, hbm)

    # Draw content
    _draw_icon_content(hdc, size, "CL")

    # Read pixels
    pixel_count = size * size
    pixels = (ctypes.c_uint32 * pixel_count).from_address(pixels_ptr.value)
    xor_data = bytes(pixels)

    # Cleanup GDI
    _SelectObject(hdc, old)
    _DeleteObject(hbm)
    _DeleteDC(hdc)
    user32.ReleaseDC(None, hdc_screen)

    # ICO requires BGRA bottom-up; we have BGRA top-down from DIB.
    # Flip rows.
    row_size = size * 4
    rows = [xor_data[i * row_size:(i + 1) * row_size] for i in range(size)]
    xor_data = b"".join(reversed(rows))

    # AND mask (1bpp) all zeros = fully opaque
    and_stride = ((size + 31) // 32) * 4
    and_data = bytes(and_stride * size)

    bitmap_size = ctypes.sizeof(BITMAPINFOHEADER) + len(xor_data) + len(and_data)
    image_offset = 6 + 16  # ICONDIR + ICONDIRENTRY

    with open(out_path, "wb") as f:
        # ICONDIR
        f.write(bytes([0, 0, 1, 0, 1, 0]))
        # ICONDIRENTRY
        f.write(bytes([size if size < 256 else 0]))       # width
        f.write(bytes([size if size < 256 else 0]))       # height
        f.write(bytes([0]))                               # colors
        f.write(bytes([0]))                               # reserved
        f.write(bytes([1, 0]))                            # planes
        f.write(bytes([32, 0]))                           # bit count
        f.write(bitmap_size.to_bytes(4, "little"))        # size
        f.write(image_offset.to_bytes(4, "little"))       # offset
        # BITMAPINFOHEADER
        f.write(ctypes.sizeof(BITMAPINFOHEADER).to_bytes(4, "little"))
        f.write(size.to_bytes(4, "little"))               # width
        f.write((size * 2).to_bytes(4, "little"))         # height (XOR + AND)
        f.write(bytes([1, 0]))                            # planes
        f.write(bytes([32, 0]))                           # bit count
        f.write(bytes([0, 0, 0, 0]))                      # compression
        f.write(bytes([0, 0, 0, 0]))                      # size image
        f.write(bytes([0, 0, 0, 0]))                      # X ppm
        f.write(bytes([0, 0, 0, 0]))                      # Y ppm
        f.write(bytes([0, 0, 0, 0]))                      # clr used
        f.write(bytes([0, 0, 0, 0]))                      # clr important
        # XOR mask
        f.write(xor_data)
        # AND mask
        f.write(and_data)

    log(f"ICO file generated: {out_path} ({size}x{size})")

def cleanup_tray():
    if not ENABLE_TRAY_ICON:
        return
    global _g_hCustomIcon
    if _g_nid:
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_g_nid))
    if _g_hMenu:
        user32.DestroyMenu(_g_hMenu)
    if _g_hCustomIcon:
        user32.DestroyIcon(_g_hCustomIcon)
        _g_hCustomIcon = None

# ═══════════════════════════════════════════════════════════════════
#  LAYOUT SWITCHING
# ═══════════════════════════════════════════════════════════════════
class LayoutSwitcher:
    def __init__(self):
        self.hook_id = None
        self.hook_proc = None
        self._processing = False

    def _caps_on(self) -> bool:
        return bool(user32.GetKeyState(VK_CAPITAL) & 0x0001)

    def _turn_off_caps(self):
        if self._caps_on():
            log("  Caps was ON, turning OFF")
            user32.keybd_event(VK_CAPITAL, 0x3A, 0, 0)
            user32.keybd_event(VK_CAPITAL, 0x3A, KEYEVENTF_KEYUP, 0)
        else:
            log("  Caps already OFF")

    def _switch_layout(self):
        try:
            hwnd = user32.GetForegroundWindow()
            log(f"  hwnd={hwnd}")
            if not hwnd:
                return

            pid = wintypes.DWORD()
            target_thread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            log(f"  target_thread={target_thread}, pid={pid.value}")
            if not target_thread:
                return

            current_hkl = user32.GetKeyboardLayout(target_thread)
            log(f"  current_hkl={current_hkl}")

            buff = (HKL * 16)()
            count = user32.GetKeyboardLayoutList(16, ctypes.byref(buff))
            log(f"  layout count={count}")
            if count <= 0:
                return

            layouts = [buff[i] for i in range(count)]
            log(f"  layouts={layouts}")
            if len(layouts) < 2:
                log("  Only one layout, nothing to switch")
                return

            try:
                idx = layouts.index(current_hkl)
                next_idx = (idx + 1) % len(layouts)
            except ValueError:
                log("  current_hkl not in list, starting from 0")
                next_idx = 0

            next_hkl = layouts[next_idx]
            log(f"  switching to hkl={next_hkl} (idx={next_idx})")

            result = user32.SendMessageW(
                hwnd,
                WM_INPUTLANGCHANGEREQUEST,
                INPUTLANGCHANGE_FORWARD,
                ctypes.c_ssize_t(next_hkl)
            )
            log(f"  SendMessage returned={result}")

            new_hkl = user32.GetKeyboardLayout(target_thread)
            log(f"  new_hkl={new_hkl}")

        except Exception as exc:
            log(f"  switch_layout ERROR: {exc}")

    def _handler(self, n_code, w_param, l_param):
        if n_code != 0:
            return _CallNextHookEx(None, n_code, w_param, l_param)

        kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

        if kb.vkCode == VK_CAPITAL:
            log(f"CAPS LOCK event: w_param={w_param}, flags={kb.flags}")

            if self._processing:
                log("  Already processing, passing through")
                return _CallNextHookEx(None, n_code, w_param, l_param)

            if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self._processing = True
                try:
                    log("  -> switch_layout + turn_off_caps")
                    self._switch_layout()
                    self._turn_off_caps()
                except Exception as exc:
                    log(f"  ERROR in handler: {exc}")
                finally:
                    self._processing = False
                return 1

            if w_param in (WM_KEYUP, WM_SYSKEYUP):
                return 1

        return _CallNextHookEx(None, n_code, w_param, l_param)

    def run(self):
        log("=== Starting ===")

        # Turn off Caps Lock if it was left on before starting
        if self._caps_on():
            log("Caps Lock was ON at startup, turning OFF")
            self._turn_off_caps()

        self.hook_proc = HOOKPROC(self._handler)
        self.hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.hook_proc, None, 0)

        if not self.hook_id:
            err = kernel32.GetLastError()
            log(f"SetWindowsHookExW FAILED, GetLastError={err}")
            print(f"Hook installation error: {err}")
            sys.exit(1)

        log("Hook installed. Running message loop...")
        if ENABLE_TRAY_ICON:
            print("[CapsLock Switcher] Running. Right-click tray icon for menu.")
        else:
            print("[CapsLock Switcher] Running. Ctrl+C to stop.")
        print("  Caps Lock switches keyboard layout.")

        msg = wintypes.MSG()
        try:
            while _g_running:
                ret = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
                if ret:
                    if msg.message == 0x0012:
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.005)
        except KeyboardInterrupt:
            log("Interrupted")
        finally:
            if self.hook_id:
                user32.UnhookWindowsHookEx(self.hook_id)
                self.hook_id = None
            cleanup_tray()
            log("=== Stopped ===")
            print("\n[CapsLock Switcher] Stopped.")


# ═══════════════════════════════════════════════════════════════════
#  SINGLE-INSTANCE GUARD
# ═══════════════════════════════════════════════════════════════════
def check_single_instance():
    """Prevent multiple instances using a named mutex."""
    mutex = _CreateMutexW(None, False, "CapsLockSwitcher_Mutex_7A3F")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        answer = _MessageBoxW(
            None,
            "CapsLock Switcher is already running.\n\n"
            "Do you want to terminate it?",
            "CapsLock Switcher",
            MB_YESNO | MB_ICONQUESTION | MB_TOPMOST
        )
        if answer == IDYES:
            hwnd = _FindWindowW("CapsLockSwitcherTray", None)
            if hwnd:
                _PostMessageW(hwnd, WM_CLOSE, 0, 0)
        sys.exit(0)
    return mutex


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    check_single_instance()
    log_init()
    try:
        # Auto-generate icon.ico when running as .py (for pyinstaller --icon)
        if not hasattr(sys, '_MEIPASS'):
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if not os.path.isfile(ico_path):
                try:
                    generate_ico_file(ico_path, 256)
                    print(f"Generated {ico_path} -- use it with pyinstaller --icon=icon.ico")
                except Exception as exc:
                    log(f"ICO generation failed: {exc}")
        if not init_tray():
            log("Tray init failed, continuing without tray icon")
        switcher = LayoutSwitcher()
        switcher.run()
    except Exception:
        log(f"FATAL:\n{traceback.format_exc()}")
        raise
    finally:
        global _log_file
        if _log_file:
            _log_file.close()
            _log_file = None


if __name__ == "__main__":
    main()
