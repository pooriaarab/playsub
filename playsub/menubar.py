"""macOS menu bar icon using native AppKit (main-thread safe with tkinter)."""

from __future__ import annotations

from AppKit import NSMenu, NSMenuItem, NSStatusBar, NSVariableStatusItemLength
from Foundation import NSObject
import objc


class _MenuActions(NSObject):
    def initWithController_(self, controller):
        self = objc.super(_MenuActions, self).init()
        if self is None:
            return None
        self.controller = controller
        return self

    def toggleOverlay_(self, _sender) -> None:
        self.controller.toggle_overlay()

    def openSettings_(self, _sender) -> None:
        self.controller.open_settings()

    def quitApp_(self, _sender) -> None:
        self.controller.quit_app()


class MenuBarController:
    def __init__(self, app: object) -> None:
        self._app = app
        self._visible = True
        self._status_item = None
        self._toggle_item = None
        self._actions = None

    def setup_on_main_thread(self) -> None:
        self._actions = _MenuActions.alloc().initWithController_(self)

        status_bar = NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        self._status_item.button().setTitle_("♪")

        menu = NSMenu.alloc().init()
        self._toggle_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide Lyrics Bar",
            "toggleOverlay:",
            "",
        )
        self._toggle_item.setTarget_(self._actions)
        menu.addItem_(self._toggle_item)

        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings…",
            "openSettings:",
            ",",
        )
        settings_item.setTarget_(self._actions)
        menu.addItem_(settings_item)

        menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Playsub",
            "quitApp:",
            "q",
        )
        quit_item.setTarget_(self._actions)
        menu.addItem_(quit_item)

        self._status_item.setMenu_(menu)

    def _run_on_overlay(self, callback) -> None:
        self._app.overlay.after(0, callback)

    def toggle_overlay(self) -> None:
        self._visible = not self._visible
        if self._visible:
            self._run_on_overlay(self._app.overlay.set_visible)
            self._toggle_item.setTitle_("Hide Lyrics Bar")
        else:
            self._run_on_overlay(self._app.overlay.hide)
            self._toggle_item.setTitle_("Show Lyrics Bar")

    def open_settings(self) -> None:
        self._run_on_overlay(self._app.overlay.open_settings)

    def quit_app(self) -> None:
        self._run_on_overlay(self._app.overlay.quit)
