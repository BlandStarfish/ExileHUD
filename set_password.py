"""
Set the installer password.

Run this whenever you want to change the password:
    python set_password.py

Writes the salted hash to installer_password.json (gitignored).
Then rebuild the installer with build_installer.bat.
"""

import hashlib
import json
import os
import secrets
import getpass

OUT = os.path.join(os.path.dirname(__file__), "installer_password.json")


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print("=" * 40)
    print("  PoELens Installer Password Setup")
    print("=" * 40)
    print()

    while True:
        pw  = getpass.getpass("Enter new installer password: ")
        pw2 = getpass.getpass("Confirm password:             ")
        if pw != pw2:
            print("Passwords do not match. Try again.\n")
            continue
        if len(pw) < 4:
            print("Password must be at least 4 characters.\n")
            continue
        break

    salt   = secrets.token_hex(16)
    hashed = hash_password(pw, salt)

    with open(OUT, "w") as f:
        json.dump({"salt": salt, "hash": hashed}, f)

    print(f"\nPassword set. Hash written to: {OUT}")
    print("Run build_installer.bat to rebuild the .exe with the new password.")
