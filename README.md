<div align="center">

win2lin-cursor

</div>

### Convert Windows cursor themes (.ani and .cur) into Linux Xcursor format.

Features
- Converts both animated (.ani) and static (.cur) cursors using win2xcur.
- Auto-patches ICO headers and injects hotspots for problematic .cur files.
- Generates all required Linux/X11 symlinks (GTK, Qt, Wayland compatibility).
- Interactive prompts for custom theme names and scaling factors.
Generates a ready-to-use index.theme.

### Requirements
```bash
win2xcur
imagemagick
libxcursor
```