from pathlib import Path

import argostranslate.package
import argostranslate.translate
import gradio as gr
from gradio_i18n import Translate, gettext as _

from cindergrace_common import BaseConfig, SecurityMixin, XDGStateStore, env_bool, env_int

# --- State Management ---
DEFAULT_STATE = {
    "disclaimer_accepted": False,
    "port": 7866,
    "language": "en",
}

_store = XDGStateStore(
    app_name="cindergrace_argos",
    defaults=DEFAULT_STATE,
)

# Path to translations
TRANSLATIONS_PATH = Path(__file__).parent / "translations" / "ui.yaml"

DISCLAIMER_TEXT = """
## Third-Party Language Models

This application downloads language models from **Argos Open Technologies** for offline translation.

### Important Notice:

- **Language models** are downloaded from external servers when you install language packages
- These models may be subject to their own **license terms**
- By using this application, you acknowledge that:
  - You are responsible for reviewing the license terms of downloaded language models
  - The models are provided by third parties, not by Cindergrace
  - Internet access is required for downloading language packages

### Argos Translate

This application is based on [Argos Translate](https://github.com/argosopentech/argos-translate),
which is licensed under the MIT License.

For more information about the language models, visit:
https://www.argosopentech.com/argospm/index/
"""


def is_disclaimer_accepted() -> bool:
    """Check if the disclaimer has been accepted."""
    state = _store.load()
    return state.get("disclaimer_accepted", False)


def save_disclaimer_acceptance() -> None:
    """Save disclaimer acceptance to state."""
    _store.update({"disclaimer_accepted": True})


def accept_disclaimer(accepted: bool):
    """Handle disclaimer acceptance."""
    if not accepted:
        raise gr.Error(_("please_accept_terms"))
    save_disclaimer_acceptance()
    # Return visibility updates: hide disclaimer, show main app
    return gr.update(visible=False), gr.update(visible=True)


class Config(BaseConfig, SecurityMixin):
    """Application configuration."""
    APP_PREFIX = "ARGOS"

    # Server settings
    PORT = env_int("ARGOS_PORT", 7866)
    # ARGOS_ALLOW_REMOTE=1 for network access (from SecurityMixin)

    # Package management can be disabled for read-only mode
    ENABLE_PACKAGE_MANAGEMENT = env_bool("ARGOS_ENABLE_PACKAGES", True)


# Helper to get a mapping of language names to codes
def get_language_map():
    installed_packages = argostranslate.package.get_installed_packages()
    unique_languages = set()  # To store (name, code) tuples
    for pkg in installed_packages:
        unique_languages.add((pkg.from_name, pkg.from_code))
        unique_languages.add((pkg.to_name, pkg.to_code))

    return dict(unique_languages)


def get_installed_language_names():
    return sorted(get_language_map().keys())


# Argos Translate API compatibility helpers (from_lang vs from_name)
def get_pkg_lang_name(pkg, direction):
    attr = f"{direction}_lang"
    if hasattr(pkg, attr):
        lang = getattr(pkg, attr)
        return getattr(lang, "name", None)
    return getattr(pkg, f"{direction}_name", None)


def get_pkg_lang_code(pkg, direction):
    attr = f"{direction}_lang"
    if hasattr(pkg, attr):
        lang = getattr(pkg, attr)
        return getattr(lang, "code", None)
    return getattr(pkg, f"{direction}_code", None)


# --- Translation Logic ---
def translate_text(text, from_lang_name, to_lang_name):
    """Perform translation based on selected languages."""
    if not text or not from_lang_name or not to_lang_name:
        return ""
    try:
        lang_map = get_language_map()
        from_code = lang_map[from_lang_name]
        to_code = lang_map[to_lang_name]

        # Get translation using the simpler API
        translation = argostranslate.translate.get_translation_from_codes(from_code, to_code)

        if not translation:
            raise gr.Error(
                _("no_package_found").format(from_lang=from_lang_name, to_lang=to_lang_name)
            )

        return translation.translate(text)

    except Exception as e:
        raise gr.Error(str(e)) from e


# --- Language Management Logic ---
def get_all_packages_status():
    """Return a list of all available packages and their installation status."""
    try:
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        installed = argostranslate.package.get_installed_packages()
        installed_codes = {
            (get_pkg_lang_code(p, "from"), get_pkg_lang_code(p, "to")) for p in installed
        }

        status = {}
        for pkg in available:
            from_name = get_pkg_lang_name(pkg, "from")
            to_name = get_pkg_lang_name(pkg, "to")
            from_code = get_pkg_lang_code(pkg, "from")
            to_code = get_pkg_lang_code(pkg, "to")
            name = f"{from_name} -> {to_name}"
            status[name] = (from_code, to_code) in installed_codes

        # Ensure default packages are in the list if index is stale
        if "Englisch -> Deutsch" not in status:
            status["Englisch -> Deutsch"] = ("en", "de") in installed_codes
        if "Deutsch -> Englisch" not in status:
            status["Deutsch -> Englisch"] = ("de", "en") in installed_codes

        return status
    except Exception as e:
        print(f"Error fetching language packages: {e}")
        return {"Englisch -> Deutsch": True, "Deutsch -> Englisch": True}  # Fallback


def update_languages(packages_to_install_names, progress=gr.Progress(track_tqdm=True)):  # noqa: B008
    """Install and uninstall language packages based on selection."""
    progress(0, desc="Starting update...")

    # Get all available packages
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    # Map names to package objects
    name_to_pkg = {
        f"{get_pkg_lang_name(p, 'from')} -> {get_pkg_lang_name(p, 'to')}": p
        for p in available_packages
    }

    # Get currently installed packages
    installed_packages = argostranslate.package.get_installed_packages()
    installed_names = {
        f"{get_pkg_lang_name(p, 'from')} -> {get_pkg_lang_name(p, 'to')}": p
        for p in installed_packages
    }

    # Determine which packages to install and uninstall
    packages_to_install = {
        name_to_pkg[name]
        for name in packages_to_install_names
        if name in name_to_pkg and name not in installed_names
    }
    packages_to_uninstall = {
        p
        for p in installed_packages
        if f"{get_pkg_lang_name(p, 'from')} -> {get_pkg_lang_name(p, 'to')}"
        not in packages_to_install_names
    }

    total_ops = len(packages_to_install) + len(packages_to_uninstall)
    if total_ops == 0:
        yield (
            _("no_changes"),
            get_checkbox_group_update(),
            get_source_dropdown_update(),
            get_target_dropdown_update(),
        )
        return

    op_count = 0

    # Uninstall
    if packages_to_uninstall:
        for pkg in progress.tqdm(packages_to_uninstall, desc="Uninstalling packages"):
            op_count += 1
            progress(
                op_count / total_ops,
                desc=f"Uninstalling {get_pkg_lang_name(pkg, 'from')} -> {get_pkg_lang_name(pkg, 'to')}",
            )
            argostranslate.package.uninstall(pkg)

    # Install
    if packages_to_install:
        for pkg in progress.tqdm(packages_to_install, desc="Installing packages"):
            op_count += 1
            progress(
                op_count / total_ops,
                desc=f"Installing {get_pkg_lang_name(pkg, 'from')} -> {get_pkg_lang_name(pkg, 'to')}",
            )
            argostranslate.package.install_from_path(pkg.download())

    yield (
        _("packages_updated"),
        get_checkbox_group_update(),
        get_source_dropdown_update(),
        get_target_dropdown_update(),
    )


def get_checkbox_group_update():
    status = get_all_packages_status()
    all_names = sorted(status.keys())
    installed_names = [name for name, installed in status.items() if installed]
    return gr.CheckboxGroup(
        choices=all_names, value=installed_names, label=_("language_packages_label")
    )


def get_source_dropdown_update():
    """Update for source language dropdown."""
    installed_langs = get_installed_language_names()
    default = (
        "Englisch"
        if "Englisch" in installed_langs
        else (installed_langs[0] if installed_langs else None)
    )
    return gr.Dropdown(choices=installed_langs, value=default, label=_("source_language"))


def get_target_dropdown_update():
    """Update for target language dropdown."""
    installed_langs = get_installed_language_names()
    default = (
        "Deutsch"
        if "Deutsch" in installed_langs
        else (installed_langs[0] if installed_langs else None)
    )
    return gr.Dropdown(choices=installed_langs, value=default, label=_("target_language"))


# --- UI Definition ---
custom_css = """
:root {
    --cg-ink: #1c1a19;
    --cg-ink-muted: #3a332f;
    --cg-paper: #f8f5f1;
    --cg-warm: #f2e9df;
    --cg-accent: #c2562b;
    --cg-accent-strong: #9e421f;
    --cg-line: rgba(28, 26, 25, 0.12);
    --cg-shadow: 0 16px 40px rgba(39, 30, 24, 0.12);
}

.gradio-container {
    background: radial-gradient(1200px 600px at 15% 10%, #fff4e5 0%, #f8f5f1 55%, #f3efe8 100%);
    color: var(--cg-ink);
    font-family: "Alegreya Sans", "Trebuchet MS", sans-serif;
}

#hero {
    padding: 18px 20px 8px 20px;
    border-bottom: 1px solid var(--cg-line);
    margin-bottom: 16px;
}

#hero h1 {
    font-family: "Playfair Display", "Georgia", serif;
    font-size: 32px;
    letter-spacing: 0.4px;
    margin: 0 0 6px 0;
}

#hero p {
    color: var(--cg-ink-muted);
    margin: 0;
}

.cg-card {
    background: var(--cg-paper);
    border: 1px solid var(--cg-line);
    border-radius: 16px;
    padding: 16px;
    box-shadow: var(--cg-shadow);
    animation: cg-fade 420ms ease-out both;
}

@keyframes cg-fade {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.tab-nav button {
    font-weight: 600;
    color: var(--cg-ink-muted);
}

.tab-nav button.selected {
    color: var(--cg-ink);
    border-bottom: 2px solid var(--cg-accent);
}

.gr-textbox textarea, .gr-textbox input, .gr-dropdown select {
    background: #fffdf9;
    border-radius: 12px;
    border: 1px solid var(--cg-line);
    font-size: 15px;
}

.cg-textarea textarea {
    min-height: 280px;
}

.gr-button.gr-button-primary {
    background: linear-gradient(135deg, var(--cg-accent) 0%, var(--cg-accent-strong) 100%);
    border: none;
    color: #fff8f2;
    border-radius: 999px;
    font-weight: 700;
    letter-spacing: 0.3px;
    padding: 10px 18px;
    box-shadow: 0 12px 24px rgba(158, 66, 31, 0.22);
}

.gr-button.gr-button-primary:hover {
    filter: brightness(1.03);
    transform: translateY(-1px);
}

.cg-translate-row .gr-column {
    gap: 10px;
}
"""


def _get_tab_labels(lang_code: str) -> tuple[str, str, str]:
    """Get localized tab labels based on saved language."""
    if lang_code == "de":
        return "Uebersetzen", "Sprachen verwalten", "Einstellungen"
    return "Translate", "Manage Languages", "Settings"


def build_app():
    """Build the Gradio application with i18n support."""
    # Load saved language preference (default: English)
    state = _store.load()
    saved_lang = state.get("language", "en")
    tab_translate, tab_languages, tab_settings = _get_tab_labels(saved_lang)

    with gr.Blocks(title="Cindergrace Argos") as demo:
        with Translate(
            str(TRANSLATIONS_PATH), placeholder_langs=["en", "de"]
        ) as lang:
            # Set language from saved state (not browser detection)
            lang.value = saved_lang

            # Check if disclaimer was already accepted
            disclaimer_already_accepted = is_disclaimer_accepted()

            # --- Disclaimer Section ---
            with gr.Column(visible=not disclaimer_already_accepted) as disclaimer_section:
                gr.Markdown(
                    lambda: f"# {_('app_title')}",
                    elem_id="hero",
                )
                with gr.Column(elem_classes=["cg-card"]):
                    gr.Markdown(DISCLAIMER_TEXT)
                    disclaimer_checkbox = gr.Checkbox(
                        label=_("disclaimer_accept"),
                        value=False,
                    )
                    accept_btn = gr.Button(_("disclaimer_continue"), variant="primary")

            # --- Main Application Section ---
            with gr.Column(visible=disclaimer_already_accepted) as main_section:
                gr.Markdown(
                    lambda: f"# {_('app_title')}\n{_('app_subtitle')}",
                    elem_id="hero",
                )

                with gr.Tabs():
                    with gr.TabItem(tab_translate):
                        with gr.Row(elem_classes=["cg-translate-row", "cg-card"]):
                            with gr.Column():
                                from_lang = gr.Dropdown(
                                    get_installed_language_names(),
                                    value=(
                                        "Englisch"
                                        if "Englisch" in get_installed_language_names()
                                        else None
                                    ),
                                    label=_("source_language"),
                                )
                                source_text = gr.Textbox(
                                    lines=12,
                                    label=_("input_text"),
                                    placeholder=_("input_placeholder"),
                                    elem_classes=["cg-textarea"],
                                )
                            with gr.Column():
                                to_lang = gr.Dropdown(
                                    get_installed_language_names(),
                                    value=(
                                        "Deutsch"
                                        if "Deutsch" in get_installed_language_names()
                                        else None
                                    ),
                                    label=_("target_language"),
                                )
                                translated_text = gr.Textbox(
                                    lines=12,
                                    label=_("translation"),
                                    interactive=False,
                                    elem_classes=["cg-textarea"],
                                )

                        translate_btn = gr.Button(_("translate_btn"), variant="primary")
                        translate_btn.click(
                            translate_text,
                            inputs=[source_text, from_lang, to_lang],
                            outputs=translated_text,
                        )

                    with gr.TabItem(tab_languages):
                        status_label = gr.Label(_("packages_status_default"))

                        # Initial state
                        packages_status = get_all_packages_status()
                        all_package_names = sorted(packages_status.keys())
                        installed_package_names = [
                            name for name, installed in packages_status.items() if installed
                        ]

                        with gr.Column(elem_classes=["cg-card"]):
                            package_checkboxes = gr.CheckboxGroup(
                                choices=all_package_names,
                                value=installed_package_names,
                                label=_("language_packages_label"),
                                info=_("language_packages_info"),
                            )

                        update_btn = gr.Button(_("update_packages_btn"), variant="primary")

                        update_btn.click(
                            update_languages,
                            inputs=[package_checkboxes],
                            outputs=[status_label, package_checkboxes, from_lang, to_lang],
                        )

                    with gr.TabItem(tab_settings):
                        with gr.Column(elem_classes=["cg-card"]):
                            gr.Markdown(lambda: f"## {_('settings_title')}")
                            lang_dropdown = gr.Dropdown(
                                choices=[("English", "en"), ("Deutsch", "de")],
                                value=saved_lang,
                                label=_("language"),
                                interactive=True,
                            )
                            settings_port = gr.Number(
                                value=state.get("port", 7866),
                                precision=0,
                                minimum=1024,
                                maximum=65535,
                                label=_("server_port"),
                                info=_("port_restart_hint"),
                            )
                            save_settings_btn = gr.Button(
                                _("save_settings_btn"), variant="primary"
                            )
                            settings_out = gr.Markdown()

                        def save_settings(lang_val, port_val):
                            _store.update({
                                "language": lang_val,
                                "port": int(port_val),
                            })
                            return _("settings_saved")

                        save_settings_btn.click(
                            save_settings,
                            inputs=[lang_dropdown, settings_port],
                            outputs=[settings_out],
                        )

                        # Language change triggers UI refresh
                        lang_dropdown.change(
                            lambda new_lang: _store.update({"language": new_lang}),
                            inputs=[lang_dropdown],
                        )

            # Connect disclaimer acceptance
            accept_btn.click(
                accept_disclaimer,
                inputs=[disclaimer_checkbox],
                outputs=[disclaimer_section, main_section],
            )

    return demo


def main():
    """Main entry point."""
    # Port: ENV var > State > Default
    port = Config.get_port(state_store=_store, default=7866)
    demo = build_app()
    demo.launch(
        server_name=Config.get_server_bind(),
        server_port=port,
        share=False,
        theme=gr.themes.Soft(),
        css=custom_css,
    )


if __name__ == "__main__":
    main()
