import sys
import os
import json
import subprocess
import argparse
from pathlib import Path

# --- LOAD NATIVE JSON CONFIG ---
CONFIG_FILE = Path("config.json")
RCLONE_PASS = ""
RCLONE_REMOTE = "gdrive:/MyTermuxBackups/" # Default fallback just in case
LOG_FILE = Path("upload.log")

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

def log_print(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def upload_to_drive(target_path, no_limit=False, limit="1M"):
    target = Path(target_path).resolve()
    
    if not target.exists():
        log_print(f"Error: The path '{target}' does not exist.")
        sys.exit(1)

    log_print(f"Starting secure upload for: {target.name}")
    log_print(f"Destination: {RCLONE_REMOTE}")
    log_print(f"Logging to: {LOG_FILE} (Monitor using: tail -f {LOG_FILE})")

    # Securely inject the password into the environment variables
    # so it never appears in command line logs
    env = os.environ.copy()
    if RCLONE_PASS:
        env["RCLONE_CONFIG_PASS"] = RCLONE_PASS 
    
    upload_cmd = [
        "rclone", "copy", 
        str(target), 
        RCLONE_REMOTE, 
        "-P",
        "--log-file", str(LOG_FILE),
        "--log-level", "INFO"
    ]
    
    if not no_limit:
        upload_cmd.extend(["--bwlimit", limit])
    
    try:
        subprocess.run(upload_cmd, env=env, check=True)
        log_print("-" * 40)
        log_print("Upload successfully completed!")
    except subprocess.CalledProcessError:
        log_print("-" * 40)
        log_print("Error: Failed to upload. Check your config.json, password, or connection.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload files via rclone.")
    parser.add_argument("path", help="/path/to/your/file_or_folder")
    parser.add_argument("--no-limit", action="store_true", help="Remove the bandwidth limit")
    parser.add_argument("--limit", type=str, default="1M", help="Set the bandwidth limit (default: 1M)")
    
    args = parser.parse_args()
    upload_to_drive(args.path, args.no_limit, args.limit)
