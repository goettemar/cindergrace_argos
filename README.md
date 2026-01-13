# Cindergrace Argos

**Status:** Final

> **Note:** This is a hobby project for personal use. It may contain bugs and is provided as-is without warranty.

Offline translator with web interface supporting multiple languages.

Based on [Argos Translate](https://github.com/argosopentech/argos-translate) (OpenNMT).

## Features

- **Offline Translation** - No internet connection required after initial setup
- **Multi-Language** - Support for 30+ languages (downloadable via UI)
- **Language Management** - Install/uninstall language packages directly in the app
- **Web Interface** - Simple Gradio UI with Cindergrace styling
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
3. Download default language packages (English <-> German)
4. Start the Gradio server

On first launch, you'll see a disclaimer about third-party language models that must be accepted.

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

Use the **"Manage Languages"** tab in the web interface to:
- View all available language packages
- Install new language pairs
- Uninstall unused packages

Available languages include: Arabic, Chinese, Dutch, French, German, Italian, Japanese, Korean, Polish, Portuguese, Russian, Spanish, and many more.

For a complete list, see: https://www.argosopentech.com/argospm/index/

### CLI Alternative

Show installed packages:
```bash
source .venv/bin/activate
python -c "import argostranslate.package; print([str(p) for p in argostranslate.package.get_installed_packages()])"
```

## License

- This project: MIT
- Argos Translate: MIT
- Language models: Various open-source licenses
