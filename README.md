# RClone Upload

A cross-platform Python script to securely upload files or folders to cloud storage (e.g., Google Drive, OneDrive, S3) using **rclone** with customizable bandwidth throttling and real-time logging.

---

## Features

- **Cross-Platform Path Support**: Seamlessly works with:
  - Windows paths (e.g., `C:\Users\username\Documents\file.zip` or `C:/Users/...`)
  - Linux, macOS, and Termux paths (e.g., `/home/user/file.zip`)
  - WSL & Git Bash paths (e.g., `/c/Users/...` or `/mnt/c/Users/...`)
  - Home directory paths (`~/file.zip`) and environment variables (`%USERPROFILE%\file.zip` or `$HOME/file.zip`)
  - Relative paths (`./folder`, `..\data`)
  - Paths containing spaces or quotes
- **Bandwidth Throttling**: Default 1MB/s upload limit to prevent network saturation, with flags for custom limits or uncapped speed.
- **Secure Password Handling**: Injects `RCLONE_CONFIG_PASS` via process environment variables so secrets never appear in command-line arguments or logs.
- **Live Logging**: Logs operations and rclone output to `upload.log`.

---

## Configuration (`config.json`)

Create or update `config.json` in the script directory:

```json
{
  "RCLONE_CONFIG_PASS": "your_master_password_here",
  "RCLONE_REMOTE": "gdrive:/MyTermuxBackups/"
}
```

- **`RCLONE_CONFIG_PASS`**: *(Optional)* Master password used to decrypt your rclone configuration.
- **`RCLONE_REMOTE`**: Destination cloud remote and folder path configured in rclone.

---

## Usage & Command Scenarios

```bash
python main.py <source> [--no-limit] [--limit <LIMIT>]
```

### Scenario 1: Upload a Single File (Default 1MB/s Limit)

**Windows (Command Prompt / PowerShell):**
```cmd
python main.py "C:\Users\username\Documents\backup.zip"
```

**Linux / macOS / Termux:**
```bash
python main.py /home/user/documents/backup.zip
```

---

### Scenario 2: Upload an Entire Folder (Default 1MB/s Limit)

**Windows:**
```cmd
python main.py "C:\Users\username\Photos\Vacation"
```

**Linux / macOS / Termux:**
```bash
python main.py /home/user/photos/vacation
```

---

### Scenario 3: Upload with Maximum Network Speed (No Limit)

Use the `--no-limit` flag to remove all bandwidth restrictions:

**Windows:**
```cmd
python main.py "C:\Users\username\Videos\project.mp4" --no-limit
```

**Linux / macOS / Termux:**
```bash
python main.py /path/to/large_folder --no-limit
```

---

### Scenario 4: Upload with a Custom Bandwidth Limit

Use the `--limit` flag to specify a custom speed limit (e.g. `500k`, `2M`, `10M`, `50M`):

**Windows:**
```cmd
python main.py "C:\Users\username\Data" --limit 5M
```

**Linux / macOS / Termux:**
```bash
python main.py /path/to/data --limit 2.5M
```

---

### Scenario 5: Relative Paths & Current Directory

**Windows:**
```cmd
python main.py .\my_folder --limit 10M
python main.py .\hashes.sha256
```

**Linux / macOS / Termux:**
```bash
python main.py ./my_folder --limit 10M
python main.py ./hashes.sha256
```

---

### Scenario 6: Using Home Directory (`~`) & Environment Variables

**Windows (PowerShell / CMD):**
```cmd
python main.py "~\Documents\report.pdf" --no-limit
python main.py "%USERPROFILE%\Downloads\dataset.zip" --limit 4M
```

**Linux / macOS / Termux:**
```bash
python main.py ~/documents/report.pdf --no-limit
python main.py "$HOME/downloads/dataset.zip" --limit 4M
```

---

### Scenario 7: Git Bash / WSL Path Formats on Windows

If you run the script from Git Bash or WSL on Windows:

```bash
python main.py /c/Users/username/Desktop/archive.tar.gz --limit 8M
python main.py /mnt/c/Users/username/Desktop/archive.tar.gz --no-limit
```

---

## CLI Options Reference

| Argument / Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `source` | Positional | *Required* | Path to the source file or folder to upload. |
| `--limit <LIMIT>` | Optional | `1M` | Sets bandwidth limit (e.g., `500k`, `2M`, `10M`). |
| `--no-limit` | Flag | `False` | Disables bandwidth limiting for maximum speed. |
| `-h`, `--help` | Flag | - | Displays help and argument usage. |

---

## Monitoring Upload Logs Live

Upload logs are saved to `upload.log`. You can monitor upload progress in real-time in a separate terminal:

- **Windows (PowerShell):**
  ```powershell
  Get-Content upload.log -Wait
  ```

- **Linux / macOS / Git Bash / Termux:**
  ```bash
  tail -f upload.log
  ```
