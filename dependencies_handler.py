#!/bin/env python3
"""
see https://github.com/fdobad/qgis-easy-dependencies-plugin/blob/main/README.md
"""
from sys import prefix as sys_prefix
from configparser import ConfigParser
from distutils.version import LooseVersion
from importlib import import_module, reload
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from re import match as re_match
from subprocess import run as subprocess_run
from platform import system as platform_system

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import QCheckBox, QMessageBox


def run():
    # get the plugin name from metadata.txt
    cp = ConfigParser()
    cp.read(Path(__file__).parent / "metadata.txt")
    plugin_name = cp.get("general", "name")

    # SWITCH COMENT IN PRODUCTION
    # config_file = Path().cwd() / "dependencies_handler.txt"
    config_file = Path(__file__).parent / "dependencies_handler.txt"
    if not config_file.is_file():
        QgsMessageLog().logMessage(
            f"Plugin {plugin_name}: dependencies_handler.txt not found! (create this file to enable checking)",
            tag="Plugins",
            level=Qgis.Critical,
        )
        return
    config = ConfigParser()
    config.read(config_file)

    if config.get("general", "enabled", fallback="True") == "False":
        QgsMessageLog().logMessage(
            f"Plugin {plugin_name}: checking & installing dependencies is disabled (to enable edit {config_file})",
            tag="Plugins",
            level=Qgis.Warning,
        )
        return

    requirements = [
        v for k, v in config.items("general")
        if k.startswith("plugin_dependency_") and v.strip()
    ]

    any_installed = False
    messages = []

    to_install = []

    for requirement in requirements:
        match = re_match(r"(.*?)([=<>!]{1,2})([\d.]+)", requirement)
        if not match:
            continue

        req_pkg_name = match.group(1)
        req_operator = match.group(2)
        req_version = match.group(3)

        try:
            found_version = distribution(req_pkg_name).version
            # No agregar si la versión existente ya satisface el requerimiento
            if LooseVersion(found_version) == LooseVersion(req_version):
                continue
        except PackageNotFoundError:
            pass  # Not installed at all

        to_install.append(requirement)

    if to_install:
        install_list = "\n".join(f"• {r}" for r in to_install)
        proceed = QMessageBox.question(
            None,
            f"Plugin '{plugin_name}' - Install missing dependencies",
            f"The following packages will be installed:\n\n{install_list}\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if proceed != QMessageBox.Yes:
            QgsMessageLog().logMessage(f"{plugin_name}: User canceled installation.", tag="Plugins", level=Qgis.Warning)
            return


    for requirement in to_install:
        match = re_match(r"(.*?)([=<>!]{1,2})([\d.]+)", requirement)
        if match:
            req_pkg_name = match.group(1)
            req_operator = match.group(2)
            req_version = match.group(3)
        else:
            messages.append(f"❌ Invalid requirement format: {requirement}")
            continue  # skip invalid lines

        try:
            found_version = distribution(req_pkg_name).version
            if LooseVersion(req_version) == LooseVersion(found_version):
                QgsMessageLog().logMessage(
                    f"Plugin {plugin_name}: {requirement} already satisfied.",
                    tag="Plugins", level=Qgis.Info
                )
                continue
            else:
                msg = f"{req_pkg_name} version mismatch: found {found_version}, required {req_version}"
        except PackageNotFoundError:
            msg = f"{req_pkg_name} is not installed"


        # Try install
        result = subprocess_run(["python3", "-m", "pip", "install", requirement], capture_output=True, text=True)

        if result.returncode == 0:
            any_installed = True
            messages.append(f"✅ Installed {requirement}")
            QgsMessageLog().logMessage(f"Plugin {plugin_name}: Installed {requirement}", tag="Plugins", level=Qgis.Success)
            # Try reload
            try:
                for module_name in get_module_names(req_pkg_name):
                    import_module(module_name)
                messages.append(f"🔁 Reloaded {req_pkg_name}")
            except Exception:
                messages.append(f"⚠️ Could not reload {req_pkg_name}, restart QGIS may be required.")
        else:
            messages.append(f"❌ Failed to install {requirement}: {result.stderr}")
            QgsMessageLog().logMessage(f"Plugin {plugin_name}: Failed to install {requirement}", tag="Plugins", level=Qgis.Critical)

    # Final message
    if messages:
        msg_text = "\n".join(messages)
        if any_installed:
            msg_text += "\n\n🔁 You may need to restart QGIS."
            QMessageBox.information(None, f"Plugin '{plugin_name}' - Dependencies", msg_text)
        else:
            QMessageBox.information(None, f"Plugin '{plugin_name}'", msg_text)


def get_module_names(distribution_name="your-package-name"):
    try:
        dist_info = distribution(distribution_name)
        unique_parents = set()

        for file in dist_info.files:
            path = Path(str(file))
            if name := path.parent.name:
                if name != "__pycache__" and name.find(".") == -1:
                    unique_parents.add(path.parent.name)

        return unique_parents

    except PackageNotFoundError as e:
        QgsMessageLog().logMessage(
            f"Plugin:{plugin_name}: {e} attempting to get module names", tag="Plugins", level=Qgis.Critical
        )
        return []