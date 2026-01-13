# Cindergrace Argos

**Status:** Final

> **Note:** This is a hobby project for personal use. It may contain bugs and is provided as-is without warranty.

Offline translator with web interface for English <-> German.

Based on [Argos Translate](https://github.com/argosopentech/argos-translate) (OpenNMT).

## Features

- **Offline Translation** - No internet connection required after initial setup
- **Bidirectional** - English -> German and German -> English
- **Web Interface** - Simple Gradio UI
- **Lightweight** - No GPU required

## Requirements

- Python 3.10+
- Internet access for initial setup (downloads language packages ~100MB)

## Installation & Start

```bash
cd /home/zorinadmin/projekte/cindergrace_argos
./start.sh
```

The script will:
1. Create a virtual environment (`.venv`)
2. Install dependencies (`argostranslate`, `gradio`)
3. Download language packages (en<->de)
4. Start the Gradio server

Then open the URL shown in the terminal (usually http://127.0.0.1:7860) in your browser.

Stop with `CTRL+C` in the terminal.

## Desktop Integration

The app is available in the application menu as "Cindergrace Argos".

Manual path:
```bash
~/.local/share/applications/cindergrace_argos.desktop
```

## Project Structure

```
cindergrace_argos/
├── start.sh              # Start script Linux
├── start.bat             # Start script Windows
├── installer.py          # Setup logic (cross-platform)
├── app.py                # Gradio application
├── pyproject.toml        # Project configuration
└── README.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Language packages missing | Run `./start.sh` again |
| Port 7860 in use | Stop other process or change port |
| Stanza warning | Ignore - does not affect functionality |

## Managing Language Packages

Show installed packages:
```bash
source .venv/bin/activate
python -c "import argostranslate.package; print([str(p) for p in argostranslate.package.get_installed_packages()])"
```

Add more languages:
```python
import argostranslate.package
argostranslate.package.update_package_index()
# Available packages: https://www.argosopentech.com/argospm/index/
```

## License

- This project: MIT
- Argos Translate: MIT
- Language models: Various open-source licenses
