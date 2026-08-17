# ocr-shot 📸🔤

A modern **Live Text OCR Screenshot** utility for **Void Linux** (Wayland & X11). It captures a screen region and interactively extracts text, featuring an **Apple Live Text**-like visual overlay.

Built with **Python 3**, **PyQt6**, and **Tesseract OCR** with native support for **Indonesian (`ind`)**, **English (`eng`)**, and **Arabic (`ara`)**.

---

## ✨ Features

- 🔍 **Interactive Live Text Overlay**: Freezes the screen, displays transparent highlight boxes over detected words, and allows interactive mouse text selection (*click & drag*, double-click word, triple-click line).
- ⚡ **Smart Data Detectors (Apple Live Text-like)**:
  - 🔗 **Web Links**: Automatically detects URLs (`http://`, `https://`, `www...`) and adds an instant **"🔗 Open Link"** button.
  - 📧 **Emails**: Detects email addresses (`test@example.com`) and adds a **"📧 Email"** button (`mailto:`).
  - 📞 **Phone Numbers**: Detects phone numbers and adds a **"📞 Phone"** button.
  - 📍 **Addresses & Locations**: Detects street names / locations and adds a **"📍 Maps"** button (opens Google Maps).
- 🖱️ **Gestures & Selection UX**:
  - 🔳 **Select All (`Ctrl+A`)**: Instantly select all detected text on screen.
  - 🖱️ **Double-Click**: Select single word under cursor.
  - 🖱️ **Triple-Click**: Select entire line under cursor.
  - 🖱️ **Right-Click Context Menu**: Native popup menu for quick actions (Copy, Select All, Search, Translate, Smart Actions).
- 📄 **Paragraph Join Mode**: Toggle between original line breaks (`≡ Lines`) and continuous single paragraph mode (`¶ Para`) to remove line-wrap breaks and hyphenations.
- 📋 **Floating Action Bar**:
  - 📋 **Copy**: Copy selected text with visual **"Copied to Clipboard!"** toast notification.
  - 🔳 **All**: Select all words (`Ctrl+A`).
  - 🔗 / 📧 / 📞 / 📍 **Smart Detector Buttons**: Dynamic quick action buttons based on selected text.
  - 🔍 **Search**: Instantly search selected text on Google.
  - 🌐 **Translate**: Translate selected text via Google Translate.
  - ≡ / ¶ **Format Toggle**: Switch between raw lines and joined paragraph text.
  - 🌐 **Language Selector**: Switch OCR scan languages directly from the overlay.
- ⚡ **Auto-Detect Display Server**: Full compatibility with **Wayland** (`grim` + `slurp`) and **X11** (`maim`, `xfce4-screenshooter`, `scrot`).
- 💻 **CLI & JSON Export Modes**:
  - `--cli`: Fast non-GUI scan directly to clipboard.
  - `--json`: Export full text and word bounding box coordinates $(x, y, w, h)$ in structured JSON format.

---

## 📦 Dependencies Installation on Void Linux

Install all required dependencies using `xbps-install`:

```bash
sudo xbps-install -S python3 python3-Pillow python3-PyQt6 tesseract tesseract-data-ind tesseract-data-eng tesseract-data-ara libnotify wl-clipboard xclip grim slurp maim
```

---

## 🛠️ Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Suyono-Sukorame/ocr-shot.git
   cd ocr-shot
   ```

2. Make scripts executable and copy binaries, desktop entry & manpage:
   ```bash
   chmod +x ocr-shot ocr_gui.py build-xbps.sh
   sudo cp ocr-shot ocr_gui.py /usr/local/bin/
   sudo cp ocr-shot.desktop /usr/share/applications/
   sudo cp ocr-shot.1 /usr/share/man/man1/
   ```

---

## ❄️ Building XBPS Package for Void Linux (`xbps-src`)

You can easily build the `.xbps` package using the included helper script or manually:

### Option A: Using the Helper Script (Recommended)
```bash
./build-xbps.sh ~/void-packages
```

### Option B: Manual setup with `xbps-src`
1. Copy the package template into your `void-packages` directory:
   ```bash
   mkdir -p ~/void-packages/srcpkgs/ocr-shot
   cp xbps/template ~/void-packages/srcpkgs/ocr-shot/template
   ```

2. Build the package with `xbps-src`:
   ```bash
   cd ~/void-packages
   ./xbps-src pkg ocr-shot
   ```

3. Install the generated `.xbps` package:
   ```bash
   sudo xbps-install --repository hostdir/binpkgs ocr-shot
   ```

---

## 🚀 Usage

### 1. Interactive Live Text GUI Mode (Default)
```bash
ocr-shot
```
*Or trigger via custom global hotkey.*

### 2. Specific Language Scan
```bash
ocr-shot ara        # Arabic only
ocr-shot ind        # Indonesian only
ocr-shot eng        # English only
ocr-shot ind+eng    # Indonesian & English
```

### 3. Fast Non-GUI Mode (CLI Direct to Clipboard)
```bash
ocr-shot --cli
```

### 4. Export Word Bounding Boxes to JSON
```bash
ocr-shot --json
```

### 5. View Manpage
```bash
man ocr-shot
```

---

## ⌨️ Global Keybinding Setup

Register `ocr-shot` to a global keyboard shortcut in your Window Manager or Desktop Environment:

- **Sway / Hyprland (Wayland)**:
  ```ini
  # ~/.config/hypr/hyprland.conf
  bind = $mainMod SHIFT, S, exec, ocr-shot
  ```
- **i3 / bspwm (X11)**:
  ```ini
  # ~/.config/i3/config
  bindsym $mod+Shift+s exec ocr-shot
  ```
- **XFCE / GNOME / KDE**:
  Go to **Settings** $\rightarrow$ **Keyboard Shortcuts** $\rightarrow$ Add Custom Shortcut $\rightarrow$ Command: `ocr-shot` $\rightarrow$ Shortcut: `Super+Shift+S` or `Print`.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
