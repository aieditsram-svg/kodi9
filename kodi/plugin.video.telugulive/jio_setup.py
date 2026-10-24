"""Optional: use your own JioTV login with Telugu Live.

This add-on does not log in to Jio and never sees your number, OTP or tokens. You install the separate JioTV
add-on (an unofficial add-on, not made by Jio), log in there with your own Jio number, and it writes a channel
list on this device. Telugu Live can then read that file as "your own extra playlist": its channels are tried
first, and the public links stay as the backup. Nothing from your Jio login is sent to or stored in the
repository.
"""
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

JIO_ID = "plugin.video.jiotv"
ADDON = xbmcaddon.Addon()

INSTALL_HELP = (
    "JioTV is a separate, unofficial add-on (not made by Jio). You log in there with your own Jio number.\n\n"
    "It is hosted in the Telugu Live Repository. To install it by hand:\n"
    "Add-ons > Install from repository > Telugu Live Repository > Video add-ons > JioTV.\n\n"
    "Then open JioTV settings, log in with your Jio number and the OTP, and turn on its playlist generation. "
    "After that, choose this entry again.\n\n"
    "The JioTV add-on was last updated in 2023 and may not work with Jio's current service. Its login "
    "requests do not check Jio's security certificate, so log in on a network you trust. Never put a "
    "playlist made by it into a public repository."
)


def jio_installed():
    return bool(xbmc.getCondVisibility("System.HasAddon(%s)" % JIO_ID))


def playlist_path():
    profile = xbmcvfs.translatePath(xbmcaddon.Addon(JIO_ID).getAddonInfo("profile"))
    return os.path.join(profile, "playlist.m3u")


def install_jio(dialog):
    """Install JioTV from the Telugu Live Repository and wait for Kodi to finish."""
    xbmc.executebuiltin("InstallAddon(%s)" % JIO_ID)
    monitor = xbmc.Monitor()
    for _ in range(120):  # up to two minutes: confirmation dialog + download
        if monitor.waitForAbort(1):
            return False
        if jio_installed():
            return True
    return False


def run():
    dialog = xbmcgui.Dialog()
    if not jio_installed():
        if not dialog.yesno("JioTV with your own Jio login",
                            "JioTV is a separate, unofficial add-on (not made by Jio). You log in there with "
                            "your own Jio number; Telugu Live never sees it.\n\nInstall JioTV from the Telugu "
                            "Live Repository now?"):
            return
        if install_jio(dialog):
            dialog.ok("JioTV", "Installed. Now choose this entry again, open JioTV settings, log in with your "
                               "Jio number and the OTP, and turn on its playlist generation.")
        else:
            dialog.textviewer("JioTV with your own Jio login", INSTALL_HELP)
        return

    path = playlist_path()
    using = ADDON.getSetting("extra_playlist").strip() == path
    pick = dialog.select("JioTV", [
        "Open JioTV settings (log in with your Jio number and OTP)",
        "Stop using JioTV channels in Telugu Live" if using else "Use JioTV channels in Telugu Live",
    ])
    if pick == 0:
        xbmc.executebuiltin("Addon.OpenSettings(%s)" % JIO_ID)
    elif pick == 1 and using:
        ADDON.setSetting("extra_playlist", "")
        dialog.ok("Telugu Live", "JioTV channels are no longer used here.")
    elif pick == 1:
        if not xbmcvfs.exists(path):
            dialog.ok("Telugu Live",
                      "JioTV has not written its channel list yet.\n\nOpen JioTV settings, log in, and turn on "
                      "its playlist generation. Then choose this entry again.")
            return
        current = ADDON.getSetting("extra_playlist").strip()
        if current and not dialog.yesno("Telugu Live",
                                        "You already use your own extra playlist:\n%s\n\nReplace it with the "
                                        "JioTV list?" % current):
            return
        ADDON.setSetting("extra_playlist", path)
        dialog.ok("Telugu Live",
                  "Done. JioTV channels now appear in Telugu Live and are tried first. If one does not play, "
                  "the add-on switches to the public link by itself.")
