import sys
import os
import json
import subprocess
from pathlib import Path

# --- LOAD NATIVE JSON CONFIG ---
CONFIG_FILE = Path("config.json")
RCLONE_PASS = ""
RCLONE_REMOTE = "gdrive:/MyTermuxBackups/" # Default fallback just in case

# Read the config file natively without any external packages
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        try:
            config_data = json.load(f)
            RCLONE_PASS = config_data.get("RCLONE_CONFIG_PASS", "")
            RCLONE_REMOTE = config_data.get("RCLONE_REMOTE", RCLONE_REMOTE)
        except json.JSONDecodeError:
            print("Error: config.json is not formatted correctly.")
            sys.exit(1)
else:
    print("Warning: config.json not found. Using default settings.")
# -------------------------------

def upload_to_drive(target_path):
    target = Path(target_path).resolve()
    
    if not target.exists():
        print(f"Error: The path '{target}' does not exist.")
        sys.exit(1)

    print(f"Starting secure upload for: {target.name}")
    print(f"Destination: {RCLONE_REMOTE}")

    # Securely inject the password into the environment variables
    # so it never appears in command line logs
    env = os.environ.copy()
    if RCLONE_PASS:
        env["RCLONE_CONFIG_PASS"] = RCLONE_PASS 
    
    upload_cmd = [
        "rclone", "copy", 
        str(target), 
        RCLONE_REMOTE, 
        "-P" 
    ]
    
    try:
        subprocess.run(upload_cmd, env=env, check=True)
        print("-" * 40)
        print("Upload successfully completed!")
    except subprocess.CalledProcessError:
        print("-" * 40)
        print("Error: Failed to upload. Check your config.json, password, or connection.")

if __name__ == "__main__":
    # Ensure the user provided a file or folder path
    if len(sys.argv) < 2:
        print("Usage: python upload.py /path/to/your/file_or_folder")
        sys.exit(1)
        
    upload_to_drive(sys.argv[1])
