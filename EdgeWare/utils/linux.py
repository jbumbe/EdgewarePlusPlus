import codecs
import json
import logging
import os
import re
import shlex
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path

from utils.paths import Defaults, Process


def panic_script():
    subprocess.run("for pid in $(ps -u $USER -ef | grep -E \"python.* *+.pyw\" | awk '{print $2}'); do echo $pid; kill -9 $pid; done", shell=True)


def set_borderless(root):
    root.wm_attributes("-type", "splash")


def set_wallpaper(wallpaper_path: Path | str):
    global first_run
    if isinstance(wallpaper_path, Path):
        wallpaper_path = str(wallpaper_path.absolute())

    # Modified source from (Martin Hansen): https://stackoverflow.com/a/21213504
    # Note: There are two common Linux desktop environments where
    # I have not been able to set the desktop background from
    # command line: Enlightenment
    desktop_env = _get_desktop_environment()
    try:
        if desktop_env in ["gnome", "unity", "cinnamon"]:
            uri = """file://%s""" % wallpaper_path
            args = [
                "gsettings",
                "set",
                "org.gnome.desktop.background",
                "picture-uri",
                uri,
            ]
            subprocess.Popen(args)
            args = [
                "gsettings",
                "set",
                "org.gnome.desktop.background",
                "picture-uri-dark",
                uri,
            ]
            subprocess.Popen(args)
        elif desktop_env == "mate":
            try:  # MATE >= 1.6
                # info from http://wiki.mate-desktop.org/docs:gsettings
                args = [
                    "gsettings",
                    "set",
                    "org.mate.background",
                    "picture-filename",
                    """%s""" % wallpaper_path,
                ]
                subprocess.Popen(args)
            except Exception:  # MATE < 1.6
                # From https://bugs.launchpad.net/variety/+bug/1033918
                args = [
                    "mateconftool-2",
                    "-t",
                    "string",
                    "--set",
                    "/desktop/mate/background/picture_filename",
                    """%s""" % wallpaper_path,
                ]
                subprocess.Popen(args)
        elif desktop_env == "gnome2":  # Not tested
            # From https://bugs.launchpad.net/variety/+bug/1033918
            args = [
                "gconftool-2",
                "-t",
                "string",
                "--set",
                "/desktop/gnome/background/picture_filename",
                """%s""" % wallpaper_path,
            ]
            subprocess.Popen(args)
        ## KDE4 is difficult
        ## see http://blog.zx2c4.com/699 for a solution that might work
        elif desktop_env in ["kde3", "trinity"]:
            # From http://ubuntuforums.org/archive/index.php/t-803417.html
            args = 'dcop kdesktop KBackgroundIface setWallpaper 0 "%s" 6' % wallpaper_path
            subprocess.Popen(args, shell=True)
        ## Pieced together from https://develop.kde.org/docs/plasma/scripting/api/
        ## handles blur for weird size images and keeps proportions
        ## theres probably a way to work Plasma Activities into this to restore previous settings but i'm lazy
        elif desktop_env == "kde":
            script = """desktops().forEach(d => {
                        d.wallpaperPlugin = "org.kde.image";
                        d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                        d.writeConfig("Blur", true);
                        d.writeConfig("FillMode", 1);
                        d.writeConfig("Image", "file:/%s");
                    })""" % wallpaper_path
            args = "qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \'%s\'" % script
            subprocess.Popen(args, shell=True)
        elif desktop_env == "xfce4":
            # From http://www.commandlinefu.com/commands/view/2055/change-wallpaper-for-xfce4-4.6.0
            if first_run:
                args0 = [
                    "xfconf-query",
                    "-c",
                    "xfce4-desktop",
                    "-p",
                    "/backdrop/screen0/monitor0/image-path",
                    "-s",
                    wallpaper_path,
                ]
                args1 = [
                    "xfconf-query",
                    "-c",
                    "xfce4-desktop",
                    "-p",
                    "/backdrop/screen0/monitor0/image-style",
                    "-s",
                    "3",
                ]
                args2 = [
                    "xfconf-query",
                    "-c",
                    "xfce4-desktop",
                    "-p",
                    "/backdrop/screen0/monitor0/image-show",
                    "-s",
                    "true",
                ]
                subprocess.Popen(args0)
                subprocess.Popen(args1)
                subprocess.Popen(args2)
            args = ["xfdesktop", "--reload"]
            subprocess.Popen(args)
        elif desktop_env == "razor-qt":  # TODO: implement reload of desktop when possible
            if first_run:
                desktop_conf = ConfigParser()
                # Development version
                desktop_conf_file = os.path.join(_get_config_dir("razor"), "desktop.conf")
                if os.path.isfile(desktop_conf_file):
                    config_option = r"screens\1\desktops\1\wallpaper"
                else:
                    desktop_conf_file = os.path.expanduser(".razor/desktop.conf")
                    config_option = r"desktops\1\wallpaper"
                desktop_conf.read(os.path.join(desktop_conf_file))
                try:
                    if desktop_conf.has_option("razor", config_option):  # only replacing a value
                        desktop_conf.set("razor", config_option, wallpaper_path)
                        with codecs.open(
                            desktop_conf_file,
                            "w",
                            encoding="utf-8",
                            errors="replace",
                        ) as f:
                            desktop_conf.write(f)
                except Exception:
                    pass
            else:
                # TODO: reload desktop when possible
                pass
        elif desktop_env in ["fluxbox", "jwm", "openbox", "afterstep"]:
            # http://fluxbox-wiki.org/index.php/Howto_set_the_background
            # used fbsetbg on jwm too since I am too lazy to edit the XML configuration
            # now where fbsetbg does the job excellent anyway.
            # and I have not figured out how else it can be set on Openbox and AfterSTep
            # but fbsetbg works excellent here too.
            try:
                args = ["fbsetbg", wallpaper_path]
                subprocess.Popen(args)
            except Exception:
                sys.stderr.write("ERROR: Failed to set wallpaper with fbsetbg!\n")
                sys.stderr.write("Please make sre that You have fbsetbg installed.\n")
        elif desktop_env == "icewm":
            # command found at http://urukrama.wordpress.com/2007/12/05/desktop-backgrounds-in-window-managers/
            args = ["icewmbg", wallpaper_path]
            subprocess.Popen(args)
        elif desktop_env == "blackbox":
            # command found at http://blackboxwm.sourceforge.net/BlackboxDocumentation/BlackboxBackground
            args = ["bsetbg", "-full", wallpaper_path]
            subprocess.Popen(args)
        elif desktop_env == "lxde":
            args = "pcmanfm --set-wallpaper %s --wallpaper-mode=scaled" % wallpaper_path
            subprocess.Popen(args, shell=True)
        elif desktop_env == "windowmaker":
            # From http://www.commandlinefu.com/commands/view/3857/set-wallpaper-on-windowmaker-in-one-line
            args = "wmsetbg -s -u %s" % wallpaper_path
            subprocess.Popen(args, shell=True)
        ## NOT TESTED BELOW - don't want to mess things up ##
        # elif desktop_env=='enlightenment': # I have not been able to make it work on e17. On e16 it would have been something in this direction
        #    args = 'enlightenment_remote -desktop-bg-add 0 0 0 0 %s' % wallpaper_path
        #    subprocess.Popen(args,shell=True)
        # elif desktop_env=='windows': #Not tested since I do not run this on Windows
        #    #From https://stackoverflow.com/questions/1977694/change-desktop-background
        #    import ctypes
        #    SPI_SETDESKWALLPAPER = 20
        #    ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, wallpaper_path , 0)
        # elif desktop_env=='mac': #Not tested since I do not have a mac
        #    #From https://stackoverflow.com/questions/431205/how-can-i-programatically-change-the-background-in-mac-os-x
        #    try:
        #        from appscript import app, mactypes
        #        app('Finder').desktop_picture.set(mactypes.File(wallpaper_path))
        #    except ImportError:
        #        #import subprocess
        #        SCRIPT = '''/usr/bin/osascript<<END
        #        tell application 'Finder' to
        #        set desktop picture to POSIX file '%s'
        #        end tell
        #        END'''
        #        subprocess.Popen(SCRIPT%wallpaper_path, shell=True)
        else:
            if first_run:  # don't spam the user with the same message over and over again
                sys.stderr.write("Warning: Failed to set wallpaper. Your desktop environment is not supported.")
                sys.stderr.write("You can try manually to set Your wallpaper to %s" % wallpaper_path)
            return False
        if first_run:
            first_run = False
        return True
    except Exception:
        sys.stderr.write("ERROR: Failed to set wallpaper. There might be a bug.\n")
        return False


def hide_file(path: Path | str):
    if isinstance(path, str):
        path = Path(path)
    hidden_path = path.parent / f".{path.name}"
    if path.exists():
        path.rename(hidden_path)


def show_file(path: Path | str):
    if isinstance(path, str):
        path = Path(path)
    hidden_path = path.parent / f".{path.name}"
    if hidden_path.exists():
        hidden_path.rename(path)


def open_directory(url: str):
    subprocess.Popen(["xdg-open", url])


def does_desktop_shortcut_exist(name: str):
    file = Path(name)
    return Path(os.path.expanduser("~/Desktop") / file.with_name(f"{file.name}.desktop")).exists()


def make_shortcut(title: str, process: Path, icon: Path, location: Path | None = None) -> bool:
    with open(Defaults.CONFIG, "r") as f:
        default_settings = json.loads(f.read())
        version = default_settings["versionplusplus"]

    shortcut_content = f"""[Desktop Entry]
Version={version}
Name={title}
Exec={shlex.join([str(sys.executable), str(process)])}
Icon={icon}
Terminal=false
Type=Application
Categories=Application;"""

    file_name = f"{title.lower()}.desktop"
    file = (location if location else Path(os.path.expanduser("~/Desktop"))) / file_name

    try:
        file.write_text(shortcut_content)
        if _get_desktop_environment() == "gnome":
            subprocess.run(
                [
                    "gio",
                    "set",
                    str(file.absolute()),
                    "metadata::trusted",
                    "true",
                ]
            )
    except Exception:
        return False
    return True


def toggle_run_at_startup(state: bool):
    autostart_path = Path(os.path.expanduser("~/.config/autostart"))
    try:
        if state:
            make_shortcut("Edgeware", Process.START, Defaults.ICON, autostart_path)
        else:
            os.remove(autostart_path / "edgeware.desktop")
    except Exception:
        logging.warning("failed to toggle autostart")


def _get_config_dir(app_name: str):
    if "XDG_CONFIG_HOME" in os.environ:
        confighome = os.environ["XDG_CONFIG_HOME"]
    else:
        confighome = os.environ.get("XDG_HOMD_CONFIG", os.path.expanduser(".config"))
    configdir = os.path.join(confighome, app_name)
    return configdir


def _is_running(process):
    # From http://www.bloggerpolis.com/2011/05/how-to-check-if-a-process-is-running-using-python/
    s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    if s.stdout:
        for x in s.stdout:
            if re.search(process, x):
                return True
    return False


# Source(Martin Hansen, Serge Stroobandt): https://stackoverflow.com/a/21213358
def _get_desktop_environment():
    # From http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=1139057
    desktop_session = os.environ.get("DESKTOP_SESSION")
    if desktop_session is not None:
        # easier to match if we doesn't have to deal with character cases
        desktop_session = desktop_session.lower()
        if desktop_session in [
            "gnome",
            "unity",
            "cinnamon",
            "mate",
            "xfce4",
            "lxde",
            "fluxbox",
            "blackbox",
            "openbox",
            "icewm",
            "jwm",
            "afterstep",
            "trinity",
            "kde",
        ]:
            return desktop_session
        ## Special cases ##
        # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
        # There is no guarantee that they will not do the same with the other desktop environments.
        elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
            return "xfce4"
        elif desktop_session.startswith("ubuntustudio"):
            return "kde"
        elif desktop_session.startswith("ubuntu"):
            return "gnome"
        elif desktop_session.startswith("lubuntu"):
            return "lxde"
        elif desktop_session.startswith("kubuntu"):
            return "kde"
        elif desktop_session.startswith("razor"):  # e.g. razorkwin
            return "razor-qt"
        elif desktop_session.startswith("wmaker"):  # e.g. wmaker-common
            return "windowmaker"
        elif desktop_session.startswith("pop"):  # e.g. wmaker-common
            return "gnome"
    if os.environ.get("KDE_FULL_SESSION") == "true":
        return "kde"
    elif os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        if "deprecated" not in os.environ.get("GNOME_DESKTOP_SESSION_ID"):  # type: ignore
            return "gnome2"
    # From http://ubuntuforums.org/showthread.php?t=652320
    elif _is_running("xfce-mcs-manage"):
        return "xfce4"
    elif _is_running("ksmserver"):
        return "kde"
    return "unknown"
