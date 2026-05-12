# CapsLock Layout Switcher

A lightweight system tray utility for Windows 10/11 that turns the **Caps Lock** key into a **keyboard layout switcher**.

No more awkward `Alt+Shift` or `Win+Space` finger gymnastics. One tap on Caps Lock — the language changes instantly. And because the physical Caps Lock behavior is suppressed, you will never accidentally type in ALL CAPS again.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Option 1: Ready-made executable](#option-1-ready-made-executable)
  - [Option 2: Build from source](#option-2-build-from-source)
- [How It Works](#how-it-works)
  - [Layout switching](#layout-switching)
  - [Caps Lock suppression](#caps-lock-suppression)
  - [Single-instance guard](#single-instance-guard)
- [Configuration](#configuration)
- [Requirements](#requirements)
- [License & Distribution](#license--distribution)
- [Feedback](#feedback)

---

## Features

| Feature | Description |
|---|---|
| **Instant layout switching** | Tap Caps Lock to cycle through all installed keyboard layouts. |
| **Caps Lock suppression** | The LED never turns on; your text stays lowercase. |
| **System-native mechanism** | Uses the same Windows API as `Alt+Shift`, works in every app. |
| **Single-instance guard** | Prevents accidental duplicate launches with a friendly dialog. |
| **System tray icon** | Blue "CL" icon with a menu to copy source or exit. |
| **Self-contained .exe** | No Python, no dependencies, no installation. |
| **Open source** | Public domain — use freely for any purpose. |

---

## Quick Start

### Option 1: Ready-made executable

1. Download `capslock_switcher.exe` from the [Releases](../../releases) page.
2. Double-click to run. No installation, no Python, no dependencies.
3. (Optional) Place it in your autostart folder for automatic launch on login:
   ```
   Win+R → shell:startup
   ```
4. Press **Caps Lock** to switch languages.

### Option 2: Build from source

Requires **Python 3.x** and **pip**.

```bash
pip install pyinstaller
python capslock_layout_switcher.py   # auto-generates icon.ico
pyinstaller --onefile --noconsole --icon=icon.ico --add-data "capslock_layout_switcher.py;." capslock_layout_switcher.py
```

The `.exe` will appear in the `dist/` folder.

> **Note:** `--onefile` bundles everything into a single self-contained executable. On launch it briefly unpacks to a temporary folder — this is normal pyinstaller behavior and shows two processes in Task Manager until the app closes.

---

## How It Works

### Layout switching

The program installs a low-level keyboard hook (`WH_KEYBOARD_LL`). When Caps Lock is pressed, it sends a `WM_INPUTLANGCHANGEREQUEST` message to the foreground window. This is the same mechanism Windows uses when you press `Alt+Shift` or click the language bar — so the switch is **system-native** and works in every application.

The program queries the list of installed layouts at runtime via `GetKeyboardLayoutList`. If you have 2 layouts, it toggles between them. If you have 5, it cycles through all 5 in order.

### Caps Lock suppression

After switching the layout, the program checks the Caps Lock state. If it is on, it synthesizes a key-release event to turn it off immediately. The LED stays dark and your case stays normal.

### Single-instance guard

On launch, the program creates a named system mutex (`CapsLockSwitcher_Mutex_7A3F`). If another instance already holds it, a top-most dialog appears:

> *"CapsLock Switcher is already running. Do you want to terminate it?"*

- **Yes** — signals the running instance to close. The new instance does **not** start.
- **No** — leaves the running instance alone. The new instance still does **not** start.

This works reliably regardless of whether the tray icon is enabled or not.

---

## Configuration

Open `capslock_layout_switcher.py` in any text editor. Two flags near the top control behavior:

```python
ENABLE_LOGGING = 0      # 1 = write capslock_switcher.log next to the .exe
ENABLE_TRAY_ICON = 1    # 0 = run completely silent, no tray icon
```

| Flag | `0` | `1` |
|---|---|---|
| `ENABLE_LOGGING` | No log file created | Debug log written to application folder |
| `ENABLE_TRAY_ICON` | No tray icon, no menu | Tray icon with right-click menu |

Changes take effect the next time you run the program.

---

## Requirements

- Windows 10 or Windows 11
- For building from source: Python 3.x + pip + pyinstaller

The released `.exe` is fully self-contained and does **not** require Python on the target machine.

---

## License & Distribution

This project is released into the **public domain**.

You may use, copy, modify, distribute, bundle, sell, or do absolutely anything with the source code and the compiled binary — no attribution required, no restrictions apply.

---

## Feedback

Suggestions, bug reports, and pull requests are welcome.

If this tool saved you a few awkward key combinations, feel free to star the repository.
