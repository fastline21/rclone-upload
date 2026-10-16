import sys
import os
import re
import json
import shutil
import subprocess
import argparse
from pathlib import Path

# --- LOAD NATIVE JSON CONFIG ---
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json" if (SCRIPT_DIR / "config.json").exists() else Path("config.json")
RCLONE_PASS = ""
RCLONE_REMOTE = "gdrive:/MyTermuxBackups/"  # Default fallback just in case
LOG_FILE = SCRIPT_DIR / "upload.log"

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

def get_rclone_bin() -> str:
    """
    Search and find the rclone executable across multiple locations on all OSes:
    1. Script directory and current working directory
    2. Subdirectories in script dir / cwd (e.g. extracted release folders)
    3. System PATH
    4. Common OS-specific installation paths
    """
    target_names = ["rclone.exe", "rclone"] if os.name == "nt" else ["rclone", "rclone.exe"]

    # 1. Check directly in script directory & current working directory
    for root in [SCRIPT_DIR, Path.cwd()]:
        if not root.exists():
            continue
        for name in target_names:
            candidate = root / name
            if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return str(candidate.resolve())

    # 2. Check system PATH
    for name in target_names:
        found = shutil.which(name)
        if found:
            return found

    # 3. Search subdirectories in SCRIPT_DIR and CWD (e.g. rclone-v1.XX-windows-amd64/rclone.exe)
    for root in [SCRIPT_DIR, Path.cwd()]:
        if root.exists():
            for name in target_names:
                try:
                    for match in root.glob(f"*/{name}"):
                        if match.is_file() and (os.name == "nt" or os.access(match, os.X_OK)):
                            return str(match.resolve())
                    for match in root.glob(f"*/*/{name}"):
                        if match.is_file() and (os.name == "nt" or os.access(match, os.X_OK)):
                            return str(match.resolve())
                except (PermissionError, OSError):
                    pass

    # 4. Check common standard directories
    common_dirs = [
        Path.home() / ".local" / "bin",
        Path.home() / "bin",
    ]
    if os.name == "nt":
        common_dirs.extend([
            Path.home() / "rclone",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "rclone" if os.environ.get("LOCALAPPDATA") else None,
            Path(r"C:\rclone"),
            Path(r"C:\Program Files\rclone"),
        ])
    else:
        common_dirs.extend([
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/opt/homebrew/bin"),
            Path("/data/data/com.termux/files/usr/bin"),
        ])

    for cdir in common_dirs:
        if cdir and cdir.exists():
            for name in target_names:
                candidate = cdir / name
                if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
                    return str(candidate.resolve())

    return "rclone.exe" if os.name == "nt" else "rclone"

def resolve_source_path(source_str: str) -> Path:
    """Normalize and resolve source path across Windows and POSIX systems."""
    if not source_str:
        return Path(".")

    # 1. Clean whitespace and surrounding quotes (handles drag-and-drop or CLI quotes)
    p = str(source_str).strip().strip("\"'")

    # Strip any trailing leftover quotes resulting from trailing backslash escaping
    while p.endswith('"') or p.endswith("'"):
        p = p[:-1].strip()

    # 2. Expand environment variables (e.g. %USERPROFILE% on Windows, $HOME on POSIX)
    p = os.path.expandvars(p)

    # 3. Expand user home directory (~)
    p = os.path.expanduser(p)

    # 4. Handle WSL / Git Bash / MSYS / Cygwin path formats on Windows (e.g., /c/Users/... or /mnt/c/Users/...)
    wsl_match = re.match(r'^[/\\](?:mnt[/\\])?([a-zA-Z])(?:[/\\](.*))?$', p)
    if wsl_match and (os.name == 'nt' or not Path(p).exists()):
        drive = wsl_match.group(1).upper()
        rest = wsl_match.group(2) or ""
        candidate = Path(f"{drive}:/{rest}")
        if candidate.exists() or os.name == 'nt':
            p = f"{drive}:/{rest}"

    # 5. Handle Windows extended-length path prefix (\\?\)
    if p.startswith(r"\\?\UNC\\"):
        p = r"\\" + p[8:]
    elif p.startswith(r"\\?\\"):
        p = p[4:]

    return Path(p).resolve()

def upload_to_drive(target_path, no_limit=False, limit="1M"):
    target = resolve_source_path(target_path)
    
    if not target.exists():
        log_print(f"Error: The path '{target}' does not exist.")
        sys.exit(1)

    destination_path = RCLONE_REMOTE
    rclone_bin = get_rclone_bin()

    log_print(f"Starting secure upload for: {target.name}")
    log_print(f"Destination: {destination_path}")
    monitor_cmd = f"Get-Content {LOG_FILE} -Wait" if os.name == "nt" else f"tail -f {LOG_FILE}"
    log_print(f"Logging to: {LOG_FILE} (Monitor using: {monitor_cmd})")

    # Securely inject the password into the environment variables
    # so it never appears in command line logs
    env = os.environ.copy()
    if RCLONE_PASS:
        env["RCLONE_CONFIG_PASS"] = RCLONE_PASS 
    
    upload_cmd = [
        rclone_bin, "copy", 
        str(target), 
        destination_path, 
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
    except FileNotFoundError:
        log_print("-" * 40)
        bin_name = "rclone.exe" if os.name == "nt" else "rclone"
        log_print(f"Error: '{bin_name}' not found. Please ensure {bin_name} is in the script directory or added to your system PATH.")
    except subprocess.CalledProcessError:
        log_print("-" * 40)
        log_print("Error: Failed to upload. Check your config.json, password, or connection.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload files via rclone.")
    parser.add_argument("source", help="Source file or folder path (supports Windows paths e.g. C:\\path\\to\\file, relative paths, and POSIX/WSL paths)")
    parser.add_argument("--no-limit", action="store_true", help="Remove the bandwidth limit")
    parser.add_argument("--limit", type=str, default="1M", help="Set the bandwidth limit (default: 1M)")
    
    args = parser.parse_args()
    upload_to_drive(args.source, args.no_limit, args.limit)
