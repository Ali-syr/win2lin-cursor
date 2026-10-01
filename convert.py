#!/usr/bin/env python3
"""
Windows-to-Linux Cursor Converter
Converts Windows cursor packages (.ani and .cur) into Linux Xcursor format.
Supports dynamic theme naming, auto-detection of ani/cur folders, ICO header fixing,
interactive scaling, symlink mapping, and automatic index.theme generation.
"""

import os
import sys
import shutil
import struct
import subprocess
from pathlib import Path

# --- LOCAL PATH CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent

# Check for win2xcur in local venv (./venv/bin/win2xcur) or fallback to system PATH
WIN2XCUR_BIN = SCRIPT_DIR / "venv" / "bin" / "win2xcur"
if not WIN2XCUR_BIN.exists():
    system_win2xcur = shutil.which("win2xcur")
    WIN2XCUR_BIN = Path(system_win2xcur) if system_win2xcur else WIN2XCUR_BIN

# Hotspot (x, y) fallback for .cur files with problematic ICO headers
CUR_FILES_HOTSPOTS = {
    "Alternate.cur": (14, 1),
    "Handwriting.cur": (8, 25),
    "Person.cur": (10, 3),
    "Pin.cur": (7, 1),
}

# Xcursor symlinks alias mapping for Linux / GTK / Qt compatibility
CURSOR_MAP = {
    # Normal
    "left_ptr": "Normal", "arrow": "Normal", "default": "Normal", "top_left_arrow": "Normal",
    "grab": "Normal", "openhand": "Normal", "dnd-copy": "Normal", "dnd-none": "Normal",
    "left_ptr_help": "Normal", "X_cursor": "Normal",

    # Help
    "question_arrow": "Help", "help": "Help", "whats_this": "Help",
    "d9ce0ab605698f320427677b458ad60b": "Help", "5c6cd98b3f3ebcb1f9c7f1c204630408": "Help",

    # Working / Progress
    "left_ptr_watch": "Working", "progress": "Working", "half-busy": "Working",
    "08e8e1c95fe2fc01f976f1e063a24ccd": "Working", "3ecb610c1bf2410f44200f48c40d3599": "Working",

    # Busy
    "wait": "Busy", "watch": "Busy",

    # Precision
    "crosshair": "Precision", "cross": "Precision", "tcross": "Precision", "cross_reverse": "Precision",

    # Text
    "xterm": "Text", "text": "Text", "ibeam": "Text", "vertical-text": "Text",

    # Handwriting
    "pencil": "Handwriting",

    # Unavailable
    "not-allowed": "Unavailable", "no-drop": "Unavailable", "circle": "Unavailable",
    "forbidden": "Unavailable", "crossed_circle": "Unavailable", "dnd-no-drop": "Unavailable",
    "03b6e0fcb3499374a867c041f52298f0": "Unavailable", "6407b0e94181790501fd1e167b474872": "Unavailable",

    # Resizing - Vertical
    "n-resize": "Vertical", "s-resize": "Vertical", "ns-resize": "Vertical",
    "sb_v_double_arrow": "Vertical", "size_ver": "Vertical", "top_side": "Vertical",
    "bottom_side": "Vertical", "v_double_arrow": "Vertical",
    "00008160000006810000408080010102": "Vertical", "2870a09082c103050810ffdffffe0204": "Vertical",

    # Resizing - Horizontal
    "e-resize": "Horizontal", "w-resize": "Horizontal", "ew-resize": "Horizontal",
    "sb_h_double_arrow": "Horizontal", "size_hor": "Horizontal", "left_side": "Horizontal",
    "right_side": "Horizontal", "h_double_arrow": "Horizontal",
    "028006030e0e7ebffc7f7070c0600140": "Horizontal", "14fef782d02440884392942c11205230": "Horizontal",

    # Resizing - Diagonal 1
    "nw-resize": "Diagonal1", "se-resize": "Diagonal1", "nwse-resize": "Diagonal1",
    "size_fdiag": "Diagonal1", "top_left_corner": "Diagonal1", "bottom_right_corner": "Diagonal1",
    "fd_double_arrow": "Diagonal1", "38c5dff7c7b8962045400281044508d2": "Diagonal1",
    "c7088f0f3e6c8088236ef8e1e3e70000": "Diagonal1",

    # Resizing - Diagonal 2
    "ne-resize": "Diagonal2", "sw-resize": "Diagonal2", "nesw-resize": "Diagonal2",
    "size_bdiag": "Diagonal2", "top_right_corner": "Diagonal2", "bottom_left_corner": "Diagonal2",
    "bd_double_arrow": "Diagonal2", "50585d75b494802d0151028115016902": "Diagonal2",
    "fcf1c3c7cd4491d801f1e1c78f100000": "Diagonal2",

    # Move
    "move": "Move", "fleur": "Move", "all-scroll": "Move", "size_all": "Move",
    "grabbing": "Move", "dnd-move": "Move", "4498f0e0c1937ffe01fd06f973665830": "Move",
    "fcf21c00b30f7e3f83fe0dfd12e71cff": "Move",

    # Link
    "hand1": "Link", "hand2": "Link", "pointer": "Link", "pointing_hand": "Link",
    "dnd-link": "Link", "e29285e634086352946a0e7090d73106": "Link",
    "9d800788f1b08800ae810202380a0822": "Link", "9116a3ea924ed2162ecab71ba103b17f": "Link",

    # Misc
    "up_arrow": "Alternate", "center_ptr": "Alternate",
    "person": "Person", "pin": "Pin"
}

def fix_ico_header_to_cur(input_path: Path, output_path: Path, hx: int = 0, hy: int = 0) -> bool:
    """Patch ICO header (type 1) to CUR (type 2) and inject hotspots"""
    try:
        with open(input_path, 'rb') as f:
            data = bytearray(f.read())

        if len(data) < 6:
            return False

        reserved, img_type, num_images = struct.unpack_from('<HHH', data, 0)

        if img_type == 2:
            shutil.copy2(input_path, output_path)
            return True

        if img_type != 1:
            return False

        # Patch ICO (1) -> CUR (2)
        struct.pack_into('<H', data, 2, 2)

        for i in range(num_images):
            entry_offset = 6 + (i * 16)
            w = data[entry_offset] or 256
            h = data[entry_offset + 1] or 256
            
            spot_x = min(hx, w - 1)
            spot_y = min(hy, h - 1)
            struct.pack_into('<HH', data, entry_offset + 4, spot_x, spot_y)

        with open(output_path, 'wb') as f:
            f.write(data)

        return True
    except Exception as e:
        print(f"  [!] Error fixing ICO header {input_path.name}: {e}")
        return False

def create_symlinks(cursors_dir: Path):
    """Create Xcursor alias symlinks for Linux desktop compatibility."""
    for alias, target in CURSOR_MAP.items():
        target_path = cursors_dir / target
        alias_path = cursors_dir / alias

        if target_path.exists():
            if alias_path.exists() or alias_path.is_symlink():
                alias_path.unlink()
            alias_path.symlink_to(target)

def setup_interactive_config():
    """Interactive user setup for theme naming and configurations."""
    print("=" * 60)
    print("      Universal Windows to Linux Cursor Converter")
    print("=" * 60)

    # 1. Theme Name Input (Output Folder Name)
    theme_name = ""
    while not theme_name:
        theme_name = input("\n[1/3] Enter Theme Name / Output Folder: ").strip()
        if not theme_name:
            print("  [!] Theme name cannot be empty! Please provide a valid name.")

    # 2. Locate Input Folders (Auto-detect 'ani' and 'cur' directories)
    print(f"\n[2/3] Select Input Cursor Directory:")
    available_dirs = []
    for item in SCRIPT_DIR.iterdir():
        if item.is_dir() and item.name not in ('venv', '_fixed_tmp', theme_name) and not item.name.startswith('.'):
            available_dirs.append(item)

    source_paths = []
    if available_dirs:
        print("     Detected directories in project path:")
        for idx, d in enumerate(available_dirs, 1):
            print(f"       {idx}. {d.name}")
        print("       3. Process All Detected Folders (Process 'ani' & 'cur' simultaneously)")
        
        choice = input(f"\n  Select option [1-{len(available_dirs)} / 3] (Default: 3): ").strip().upper()
        
        if choice == "3" or not choice:
            source_paths = available_dirs
        elif choice.isdigit() and 1 <= int(choice) <= len(available_dirs):
            source_paths = [available_dirs[int(choice) - 1]]
        else:
            custom_p = Path(choice).expanduser().resolve()
            if custom_p.exists():
                source_paths = [custom_p]
    else:
        source_paths = [SCRIPT_DIR]

    # 3. Scale Factor Option
    print("\n[3/3] Choose Cursor Scaling Factor:")
    print("  1. Original / No Scaling (1.0)")
    print("  2. Small (~24px -> Scale 0.2)")
    print("  3. Standard (~32px -> Scale 0.25)")
    print("  4. Medium (~48px -> Scale 0.375)")
    print("  5. Large (~64px -> Scale 0.5)")
    print("  6. Custom Scale Factor (manual entry)")

    scale_choice = input("\n  Select option [1-6] (Default: 1): ").strip()
    scale_factor = None
    if scale_choice == "2":
        scale_factor = "0.2"
    elif scale_choice == "3":
        scale_factor = "0.25"
    elif scale_choice == "4":
        scale_factor = "0.375"
    elif scale_choice == "5":
        scale_factor = "0.5"
    elif scale_choice == "6":
        custom_val = input("  Enter custom scale factor (e.g., 0.3): ").strip()
        scale_factor = custom_val if custom_val else None

    return theme_name, source_paths, scale_factor

def main():
    if not WIN2XCUR_BIN.exists():
        print(f"Error: win2xcur executable not found at: {WIN2XCUR_BIN}")
        print("Ensure virtual environment is set up and win2xcur is installed")
        print("  python3 -m venv venv")
        print("  ./venv/bin/pip install win2xcur")
        sys.exit(1)

    theme_name, source_paths, scale_factor = setup_interactive_config()

    # Dynamic output folder creation matching user prompt!
    theme_dir = SCRIPT_DIR / theme_name
    cursors_dir = theme_dir / "cursors"
    tmp_dir = SCRIPT_DIR / "_fixed_tmp"

    tmp_dir.mkdir(parents=True, exist_ok=True)
    cursors_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print(f"  Starting Conversion Process:")
    print(f"  - Theme / Output Folder Name : {theme_name}")
    print(f"  - Input Source Directories  : {[p.name for p in source_paths]}")
    print(f"  - Output Destination Path   : {theme_dir}")
    print(f"  - Scale Factor Applied      : {scale_factor if scale_factor else 'None (1.0)'}")
    print("=" * 60 + "\n")

    all_files = []
    for s_path in source_paths:
        if s_path.exists():
            all_files.extend([f for f in s_path.iterdir() if f.suffix.lower() in ('.ani', '.cur')])

    if not all_files:
        print(f"[!] No .ani or .cur files found in selected directories!")
        sys.exit(1)

    success, failed = 0, 0

    for file_path in all_files:
        fname = file_path.name
        input_target = file_path

        hx, hy = CUR_FILES_HOTSPOTS.get(fname, (0, 0))
        fixed_file = tmp_dir / fname
        if fix_ico_header_to_cur(file_path, fixed_file, hx, hy):
            input_target = fixed_file

        cmd = [str(WIN2XCUR_BIN), str(input_target), "-o", str(cursors_dir) + "/"]
        if scale_factor:
            cmd.extend(["--scale", str(scale_factor)])

        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode == 0:
            print(f"  [OK] {fname}")
            success += 1
        else:
            print(f"  [FAIL] {fname}: {res.stderr.strip()}")
            failed += 1

    print("\n[+] Generating Xcursor symlinks...")
    create_symlinks(cursors_dir)

    print("[+] Generating index.theme...")
    index_file = theme_dir / "index.theme"
    with open(index_file, "w") as f:
        f.write(f"[Icon Theme]\nName={theme_name}\nComment={theme_name} cursor theme converted with win2xcur\nInherits=default\n")

    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f" Finished! Success: {success} | Failed: {failed}")
    print(f" Output files saved at: {theme_dir}")
    print("=" * 60)
    print(f"\nTo install the cursor theme into your Linux system, run:")
    print(f"  mkdir -p ~/.local/share/icons/")
    print(f"  cp -r '{theme_dir}' ~/.local/share/icons/\n")

if __name__ == "__main__":
    main()
