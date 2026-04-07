## RClone Upload

This will upload file(s) or folder via rclone to any cloud storage (eg. google drive) with a default 1MBps bandwidth limit.

## Commands

```bash
python main.py /path/to/your/folder/hashes.sha256
```

```bash
python main.py /path/to/your/folder
```

To run without the 1MBps limit, use the `--no-limit` flag:

```bash
python main.py /path/to/your/folder --no-limit
```

To run with custom limit, use `--limit` flag:

```bash
python main.py /path/to/your/folder --limit 2M
```
