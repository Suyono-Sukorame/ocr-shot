# ocr-shot 📸🔤

Aplikasi **Live Text OCR Screenshot** modern untuk **Void Linux** (Wayland & X11). Mengambil tangkapan layar wilayah (*screenshot region*) dan mengekstraksi teks secara interaktif mirip seperti fitur **Apple Live Text**.

Dibuat khusus menggunakan **Python 3**, **PyQt6**, dan **Tesseract OCR** dengan dukungan bahasa **Indonesia (`ind`)**, **Inggris (`eng`)**, dan **Arab (`ara`)**.

---

## ✨ Fitur Utama

- 🔍 **Interactive Live Text Overlay**: Membekukan layar, memberi highlight kotak transparan di atas kata-kata yang terdeteksi, dan mengizinkan seleksi teks interaktif menggunakan mouse.
- 🌐 **Multi-Language Combined Mode**: Mengenali Bahasa Indonesia (`ind`), Inggris (`eng`), dan Arab (`ara`) secara bersamaan dalam satu kali scan (`ind+eng+ara`).
- ⚡ **Auto-Detect Display Server**: Mendukung lingkungan **Wayland** (`grim` + `slurp`) dan **X11** (`maim`, `xfce4-screenshooter`, `scrot`).
- 📋 **Floating Action Bar**:
  - 📋 **Copy**: Menyalin teks terpilih ke clipboard (`wl-copy` / `xclip`).
  - 🔍 **Search**: Langsung mencari teks terpilih di Google.
  - 🌐 **Translate**: Mengubah teks terpilih di Google Translate.
  - 🌐 **Selector Bahasa**: Ganti mode bahasa scan instan di UI overlay.
- 💻 **Mode CLI & Export JSON**:
  - `--cli`: Pemindaian cepat tanpa GUI langsung ke clipboard.
  - `--json`: Mengekspor teks dan posisi koordinat bounding box $(x, y, w, h)$ kata ke format JSON terstruktur.

---

## 📦 Instalasi Dependensi di Void Linux

Jalankan perintah berikut untuk menginstall dependensi yang dibutuhkan di Void Linux:

```bash
sudo xbps-install -S python3 python3-Pillow python3-PyQt6 tesseract tesseract-data-ind tesseract-data-eng tesseract-data-ara libnotify wl-clipboard xclip grim slurp maim
```

---

## 🛠️ Instalasi Manual / Penggunaan Langsung

1. Clone repositori ini:
   ```bash
   git clone https://github.com/Suyono-Sukorame/ocr-shot.git
   cd ocr-shot
   ```

2. Berikan izin eksekusi dan salin ke `/usr/local/bin`:
   ```bash
   chmod +x ocr-shot ocr_gui.py
   sudo cp ocr-shot ocr_gui.py /usr/local/bin/
   sudo cp ocr-shot.desktop /usr/share/applications/
   ```

---

## ❄️ Build Paket XBPS di Void Linux (`xbps-src`)

Jika Anda menggunakan repositori lokal `void-packages` untuk Void Linux:

1. Salin folder template paket ke repositori `void-packages`:
   ```bash
   cp -r xbps/template ~/void-packages/srcpkgs/ocr-shot/template
   ```

2. Build paket menggunakan `xbps-src`:
   ```bash
   cd ~/void-packages
   ./xbps-src pkg ocr-shot
   ```

3. Install paket `.xbps` yang dihasilkan:
   ```bash
   sudo xbps-install --repository hostdir/binpkgs ocr-shot
   ```

---

## 🚀 Cara Penggunaan

### 1. Mode GUI Live Text Interaktif (Default)
```bash
ocr-shot
```
*Atau tekan pintasan tombol global keyboard yang telah diatur (Hotkey).*

### 2. Mode Bahasa Spesifik
```bash
ocr-shot ara        # Khusus Bahasa Arab
ocr-shot ind        # Khusus Bahasa Indonesia
ocr-shot eng        # Khusus Bahasa Inggris
ocr-shot ind+eng    # Indonesia & Inggris
```

### 3. Mode Cepat Non-GUI (CLI Direct to Clipboard)
```bash
ocr-shot --cli
```

### 4. Export JSON Bounding Box
```bash
ocr-shot --json
```

---

## ⌨️ Pengaturan Hotkey Keyboard (Window Manager / Desktop)

Anda disarankan untuk mendaftarkan perintah `ocr-shot` ke tombol pintas global (*Keybinding*):

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
  Buka *Settings* $\rightarrow$ *Keyboard Shortcuts* $\rightarrow$ Tambahkan Custom Shortcut $\rightarrow$ Perintah: `ocr-shot` $\rightarrow$ Pintasan: `Super+Shift+S` atau `Print`.

---

## 📄 Lisensi

Berlisensi di bawah [MIT License](LICENSE).
