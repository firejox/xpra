#!/usr/bin/env python3
# This file is part of Xpra.
# Copyright (C) 2010-2018 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
import sys

from xpra.log import Logger
log = Logger("sound")


def get_x11_property(atom_name):
    from xpra.os_util import OSX, POSIX
    if not POSIX or OSX:
        return b""
    display = os.environ.get("DISPLAY")
    if not display:
        return b""
    try:
        from xpra.x11 import bindings
        assert bindings
    except ImportError:
        from xpra.util import first_time, envint
        if first_time("pulse-x11-bindings") and not envint("XPRA_SKIP_UI", 0):
            log.info(f"unable to query display properties without the X11 bindings")
        return b""
    try:
        from xpra.gtk_common.error import xswallow
        from xpra.x11.bindings.posix_display_source import X11DisplayContext    #@UnresolvedImport
        from xpra.x11.bindings.window_bindings import X11WindowBindingsInstance
    except ImportError as e:
        log("get_x11_property(%s)", atom_name, exc_info=True)
        log.error("Error: unable to query X11 property '%s':", atom_name)
        log.estr(e)
        return b""
    try:
        with X11DisplayContext(display):
            with xswallow:
                X11Window = X11WindowBindingsInstance()
                root = X11Window.getDefaultRootWindow()
                log("getDefaultRootWindow()=%#x", root)
                try:
                    prop = X11Window.XGetWindowProperty(root, atom_name, "STRING")
                except Exception as e:
                    log("cannot get X11 property '%s': %s", atom_name, e)
                    return b""
                log("XGetWindowProperty(..)=%s", prop)
                if prop:
                    from xpra.os_util import strtobytes
                    from xpra.x11.prop_conv import prop_decode
                    v = prop_decode("latin1", prop)
                    log("get_x11_property(%s)=%s", atom_name, v)
                    return strtobytes(v)
                return b""
    except Exception as e:
        log("get_x11_property(%s)", atom_name, exc_info=True)
        log.error("Error: cannot get X11 property '%s'", atom_name)
        log.estr(e)
    return b""

def get_pulse_server_x11_property():
    return get_x11_property("PULSE_SERVER")

def get_pulse_id_x11_property():
    return get_x11_property("PULSE_ID")


def main():
    if "-v" in sys.argv:
        log.enable_debug()
    print("PULSE_SERVER=%s" % get_pulse_server_x11_property())
    print("PULSE_ID=%s" % get_pulse_id_x11_property())


if __name__ == "__main__":
    main()
