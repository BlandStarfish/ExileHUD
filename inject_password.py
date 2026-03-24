"""
Reads installer_password.json and patches the _PW_SALT / _PW_HASH
constants in installer_gui.py before the build.

Called automatically by build_installer.bat.
"""

import json, os, re, sys

HERE     = os.path.dirname(os.path.abspath(__file__))
PW_FILE  = os.path.join(HERE, "installer_password.json")
GUI_FILE = os.path.join(HERE, "installer_gui.py")

if not os.path.exists(PW_FILE):
    print("[ERROR] installer_password.json not found.")
    print("        Run: python set_password.py")
    sys.exit(1)

with open(PW_FILE) as f:
    pw = json.load(f)

salt   = pw["salt"]
hashed = pw["hash"]

with open(GUI_FILE, "r", encoding="utf-8") as f:
    src = f.read()

src = re.sub(r'_PW_SALT = "[^"]*"', f'_PW_SALT = "{salt}"', src)
src = re.sub(r'_PW_HASH = "[^"]*"', f'_PW_HASH = "{hashed}"', src)

with open(GUI_FILE, "w", encoding="utf-8") as f:
    f.write(src)

print(f"[OK] Password hash injected into installer_gui.py")
