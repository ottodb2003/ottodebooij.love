import os

# Deine Verzeichnisse
folders = [
    "IMAGE",
    "IMAGE/COMPRESSED",
    "IMAGE/SMALL",
    "IMAGE/thumbs"
]

def rename_files(folder):
    for filename in os.listdir(folder):
        old_path = os.path.join(folder, filename)

        # Nur Dateien anfassen
        if os.path.isfile(old_path):
            new_filename = filename.replace(" ", "")
            new_path = os.path.join(folder, new_filename)

            # Nur umbenennen, wenn sich was ändert
            if old_path != new_path:
                print(f"Renaming: {old_path} -> {new_path}")
                os.rename(old_path, new_path)

# Alle Ordner durchgehen
for f in folders:
    if os.path.exists(f):
        rename_files(f)
