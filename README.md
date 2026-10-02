# Win2Lin Cursor Converter

Interactive Python tool for seamlessly converting Windows cursor packages (`.ani` and `.cur`) into Linux Xcursor format. Designed with modularity.

---

## Features

- **Interactive CLI Setup**: Dynamically configure theme output names and scale factors.
- **Auto-Detection**: Automatically detects and processes `ani/` and `cur/` directories simultaneously.
- **ICO Header Fixer**: Patches invalid ICO headers (type 1 to type 2) and injects accurate hotspots for problematic `.cur` files.
- **Xcursor Symlink Generator**: Automatically generates comprehensive cursor aliases for GTK, Qt, and Linux window manager compatibility.
- **Index Theme Creation**: Automatically generates a valid `index.theme` manifest file.

---

```plainttext
.
win2lin-cursor/
├── convert.py
├── .gitignore
├── venv/
├── ani/
├── cur/
└── YourThemeName/          <-- Generated Theme Folder
```

## Prerequisites

Ensure you have the following system dependencies installed on your Linux distribution before running the converter:

- **Python 3.8+**
- **libxcursor**
- **ImageMagick**

### Dependencies
```bash
libxcursor
imagemagick
```
