# Native (non-web, non-Qt) Python desktop UI toolkits as PySide6 replacement candidates (state: 2026-10-24)

Scope note: facts below were gathered on 2026-10-24. Primary sources were PyPI metadata, project changelogs/READMEs on GitHub, and official docs where reachable. Several official doc hosts (pygobject.gnome.org, gnome.pages.gitlab.gnome.org, docs.gtk.org, slint.dev/docs.slint.dev, beeware.org/toga.beeware.org, dearpygui.readthedocs.io, kivy.org, wxpython.org, gstreamer.freedesktop.org) could not be fetched directly from this environment (DNS blocked); for those, findings rest on search-result excerpts of the pages plus GitHub raw files, and are marked as such. Where something could not be verified it is listed under Gaps rather than guessed.

Requirement checklist used throughout (from the assignment): (1) main window with mode-dependent header buttons/combobox, (2) VIEW two-pane resizable layout + sentence list + read-only interleaved word grid, (3) CREATE form + 5-60 s background AI call with progress and no UI freeze, (4) EDIT mode with draggable word tags between columns/pool, per-column states and confirm buttons, validation, (5) audio bar with play/stop/loop/speed/save-as + native file dialog, (6) settings with provider CRUD dialogs incl. password field, (7) pytest-testable, packageable, native dialogs, Wayland/Hyprland.

---

## Key Question 1: GTK4 + libadwaita via PyGObject

### Takeaway
PyGObject 3.58.1 (Oct 2026, LGPL-2.1+, Python ≥3.10) with libadwaita 1.9/1.10 and pygobject-stubs 2.20.0 (Oct 2026, covers Gtk4, Adw, Gst) is the only candidate where every item 1-7 is covered by documented first-party APIs (Gtk.DragSource/DropTarget for in-app object drags, GStreamer playbin/GstPlay + scaletempo for rate-changed, looping audio, Gtk.FileDialog native dialogs, Flatpak as the canonical packaging). It is Linux/GNOME-first: Windows and macOS are possible (MSYS2/gvsbuild, Homebrew) but libadwaita there is a build-it-yourself story with no verified current recipe.

### Cited Findings

**Versions, license, Python support**
- PyGObject latest is 3.58.1, released Oct 9, 2026; metadata requires Python ≥3.10; license LGPLv2.1+ ("LGPLv2 or later" classifier); distributed as source only, so a C compiler is needed on the host (on Arch it is normally installed as the distro package `python-gobject`) — [PyPI PyGObject](https://pypi.org/project/PyGObject/)
- Arch Linux ships `python-gobject 3.58.0-1` in its gnome-unstable repo (packaged PyGObject matching the system GTK), i.e. an Omarchy/Arch user gets PyGObject from pacman without compiling — [archlinux.org python-gobject](https://archlinux.org/packages/gnome-unstable/x86_64/python-gobject/)
- libadwaita 1.8 shipped alongside GNOME 49 (Sept 17, 2025) with `AdwShortcutsDialog`, `AdwShortcutLabel`, full CSS media-query support (one stylesheet for light/dark/high-contrast), a `.document` style class — [Linuxiac](https://linuxiac.com/libadwaita-1-8-arrives-alongside-gnome-49/); [Phoronix](https://www.phoronix.com/news/libadwaita-1.8-Released)
- libadwaita 1.9.0 was packaged in Debian unstable on 2 April 2026 (upstream 1.9.0, GNOME 50 cycle); Arch Linux carries libadwaita 1:1.9.2-1 (built 28 June 2026) — [Debian tracker 1.9.0](https://tracker.debian.org/news/1737851/accepted-libadwaita-1-190-1-source-into-unstable/); [archlinux.org libadwaita](https://archlinux.org/packages/extra/x86_64/libadwaita/)
- pygobject-stubs 2.20.0 (19 Oct 2026) updated type hints for Adw to 1.10.0 and Gtk4 to 4.24.1, implying libadwaita 1.10 / GTK 4.24 exist upstream as of Oct 2026 — [pygobject-stubs CHANGELOG](https://raw.githubusercontent.com/pygobject/pygobject-stubs/master/CHANGELOG.md)

**Drag and drop (requirement 4)**
- GTK4 DnD model (PyGObject tutorial): `Gtk.DragSource` and `Gtk.DropTarget` are event controllers attached with `Gtk.Widget.add_controller`; payload is a `Gdk.ContentProvider` (`Gdk.ContentProvider.new_for_value(value)`, several combined via `new_union`); source signals `prepare`, `drag-begin` (set icon via `Gtk.DragSource.set_icon`), `drag-end`, `drag-cancel`; `Gtk.DropTarget.new(type, actions)`, multiple types via `GObject.TYPE_NONE` + `set_gtypes([...])` (list order = priority); target signals `accept`, `enter`, `motion`, `leave`, `drop`; `Gtk.DropTargetAsync` for complex cases — [PyGObject GTK4 Drag and Drop tutorial](https://pygobject.gnome.org/tutorials/gtk4/drag-and-drop.html)
- The official example passes an arbitrary Python GObject subclass as the drag value: `Gdk.ContentProvider.new_for_value(self)` where `self` is a `SourceFlowBoxChild` (Gtk widget subclass), drop target created with `Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)` then `set_gtypes([SourceFlowBoxChild, Gdk.FileList, str])`; the `drop` handler receives `value` and branches with `isinstance`; the drag icon is a `Gtk.WidgetPaintable` of the dragged child — [drag_and_drop.py example](https://raw.githubusercontent.com/GNOME/pygobject/main/docs/tutorials/gtk4/examples/drag_and_drop.py)
- Common pitfall: all signals fire except `drop` when the accepted GTypes don't match the provider's type (`set_gtypes`) — [python-gtk-pygobject issue #5](https://github.com/natorsc/python-gtk-pygobject/issues/5)

**Audio via GStreamer (requirement 5)**
- `scaletempo` element: "when an application sends a seek event with rate != 1.0, Scaletempo applies the rate change by scaling the tempo without scaling the pitch"; documented usage is to put `scaletempo ! audioconvert ! audioresample ! autoaudiosink` as playbin's audio sink — [GStreamer scaletempo docs](https://gstreamer.freedesktop.org/documentation/audiofx/scaletempo.html)
- `GstPlay` (the modern high-level player API in gst-plugins-bad) exposes `gst_play_set_rate(play, double rate)` — [gstreamer-rs sys docs for gst_play_set_rate](https://gstreamer.pages.freedesktop.org/gstreamer-rs/git/docs/gstreamer_play_sys/fn.gst_play_set_rate.html)
- Looping pattern in PyGObject with `playbin3`: react to the `about-to-finish` signal (gapless) or re-seek on EOS; an author's experiments note the playback rate resets after the first loop iteration unless the rate is re-applied in the seek — [gst-looping-video-2.py (Gst 1.0, gi.repository)](https://git.ao2.it/experiments/gstreamer.git/blob/812f9174c7d3d3f3265142e905d3964978d8e647:/python/gst-looping-video-2.py); [gst-trick-mode-looping-3.py](https://git.ao2.it/experiments/gstreamer.git/blob/e1fd500bd67cf3b6136a3f5fb4ce6f6cd698f924:/gst-trick-mode-looping-3.py)
- A WebKit discussion notes scaletempo/pitch plugins "need quite some CPU" — [WebKit bug 31155](https://bugs.webkit.org/show_bug.cgi?id=31155)
- pygobject-stubs added GStreamer stubs in 2.18.0 (14 Oct 2026) and updated Gst* hints in 2.16.0/2.17.0 — [pygobject-stubs CHANGELOG](https://raw.githubusercontent.com/pygobject/pygobject-stubs/master/CHANGELOG.md)

**libadwaita widgets for layout/settings (requirements 1, 2, 6)**
- Toga's GTK docs state its libadwaita integration requires libadwaita ≥1.5 (the version that introduced `AdwDialog`/`AdwPreferencesDialog`); the Ubuntu/Debian GIR package is `gir1.2-adw-1`, Fedora/Arch `libadwaita` — [Toga GTK platform page](https://toga.beeware.org/en/latest/reference/platforms/linux/gtk)
- The libadwaita API docs host (gnome.pages.gitlab.gnome.org/libadwaita/doc/main/) was not reachable from this environment; the widget list (NavigationSplitView, OverlaySplitView, ViewStack/ViewSwitcher, PreferencesDialog/Group, ActionRow/EntryRow/PasswordEntryRow/ComboRow/SpinRow/SwitchRow, ToolbarView, HeaderBar, Toast, AlertDialog, Banner, SplitButton, StyleManager) could therefore not be re-verified here — see Gaps.

**Blueprint markup**
- blueprint-compiler 0.22.2 released Jul 10, 2026 on PyPI, "Markup compiler for GTK user interface definitions", LGPL-3.0-or-later — [PyPI blueprint-compiler](https://pypi.org/project/blueprint-compiler/)

**Type stubs / pyright**
- pygobject-stubs 2.20.0 released Oct 19, 2026; Python ≥3.10; libraries with multiple versions (Gtk3/Gtk4) share a namespace so only one can be installed; selected at install time via `--config-settings=config=Gtk4,...` or `PYGOBJECT_STUB_CONFIG`; default = most recent version of each library; for uv use `config-settings-package` in `pyproject.toml`; reinstall needs `--no-cache-dir` — [PyPI pygobject-stubs](https://pypi.org/project/pygobject-stubs/); [README](https://raw.githubusercontent.com/pygobject/pygobject-stubs/master/README.md)
- Release cadence: 2.16.0 (08 Dec 2025), 2.17.0 (18 Mar 2026: Adw, Gdk4, Gio, Gst, Gtk4, GtkSource5 updated), 2.18.0 (14 Oct 2026: Gio asyncio stubs, GStreamer stubs, "versioned imports"), 2.19.0 (16 Oct 2026), 2.20.0 (19 Oct 2026) — [CHANGELOG](https://raw.githubusercontent.com/pygobject/pygobject-stubs/master/CHANGELOG.md)
- Arch packages pygobject-stubs (`python-pygobject-stubs 2.17.0-1`) and its file list includes a generated `gi-stubs/repository/Adw.pyi` — [archlinux.org file list](https://archlinux.org/packages/extra/any/python-pygobject-stubs/files/)
- Stubs depend on `PyGObject>=3.55.0` and `typing_extensions` (2.17.0 metadata) — [PyPI PyGObject-stubs via search](https://pypi.org/project/PyGObject-stubs/)

**Packaging**
- Flatpak docs: Python apps with pip/setuptools installs use the `simple` buildsystem; `flatpak-pip-generator` generates manifest modules once dependency counts get large — [docs.flatpak.org Python](https://docs.flatpak.org/en/latest/python.html); `req2flatpak` converts requirements to flatpak-builder modules — [PyPI req2flatpak](https://pypi.org/project/req2flatpak); worked example generating `python-deps.json` — [byabbe.se 2022](https://byabbe.se/2022/11/07/python-dependencies-and-flatpak); PyGObject has its own Flatpak guide — [pygobject.gnome.org/guide/flatpak](https://pygobject.gnome.org/guide/flatpak.html)
- PyInstaller: "PyInstaller's packager has built-in support for automatically including PyGObject dependencies with your application without requiring additional configuration"; macOS pipeline described there uses jhbuild + gtk-mac-bundler + dmgbuild (page is old) — [PyGObject deployment guide](https://pygobject.readthedocs.io/en/latest/guide/deploy.html)

**Windows / macOS**
- Windows: official GTK docs recommend MSYS2 (packages for the whole GTK stack) or gvsbuild for Visual Studio; PyGObject getting-started installs `mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-python3 mingw-w64-ucrt-x86_64-python3-gobject` — [gtk.org Windows](https://gtk.org/docs/installations/windows/); [PyGObject Getting Started](https://pygobject.gnome.org/getting_started.html)
- gvsbuild supports GTK3 and GTK4, requires Visual Studio + Python 3 + MSYS2, builds PyGObject wheels with `gvsbuild build --enable-gi --py-wheel gtk4 pygobject`, and "strongly recommend[s] to build your own binaries" for distribution — [wingtk/Gvsbuild](https://github.com/wingtk/Gvsbuild)
- libadwaita on Windows: gtk-rs book says `gvsbuild build libadwaita librsvg` or manual meson/MSVC build — [gtk-rs book libadwaita](https://gtk-rs.org/gtk4-rs/git/book/libadwaita.html)
- macOS: Homebrew has a `libadwaita` formula with bottles for Apple Silicon and Intel (search snapshot showed stable 1.7.5; may be stale) depending on `gtk4` — [formulae.brew.sh libadwaita](https://formulae.brew.sh/formula/libadwaita)
- The Swift libadwaita wrapper (AparokshaUI) is no longer maintained, an indicator of thin non-Linux ecosystem — [github.com/AparokshaUI/Libadwaita](https://github.com/AparokshaUI/Libadwaita)

**Testing**
- PyGObject testing guide recommends Mutter in headless Wayland mode under a dbus session for running GTK tests without display hardware; Xvfb is the classic alternative (without a display, `import Gtk` succeeds but the first Gdk/Gtk call crashes) — [PyGObject testing guide](https://pygobject.gnome.org/guide/testing.html); [pygobject MR 85](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/85)
- dogtail (AT-SPI UI automation) supports GTK4 apps; its notes say disabling window shadows is essential for accurate positioning — [PyPI dogtail](https://pypi.org/project/dogtail)

**Wayland / Hyprland**
- Hyprland sets the "maximized" xdg-toplevel state on all tiled windows so clients stop drawing their own decorations (commit referencing issue #3830) — [Hyprland commit ae46fbafe5](https://git.protagon.space/hiro/Hyprland/src/commit/ae46fbafe5ba2d707e3d2897de74bf5a1d7397c6)
- Hyprland 0.56 (released 20 July 2026) added "XDG interactive drag support for dragging client-side decoration titlebars" — [Phoronix Hyprland 0.56](https://www.phoronix.com/news/Hyprland-0.56)
- Hyprland dropped wlroots in 0.41.0 — [hypr.land update41](https://hypr.land/news/update41)

### Inferences
- Requirement 4 (word tags dragged between columns and an "unassigned pool") maps directly onto the official example: each tag is a `Gtk.Button`/`Gtk.Label` with a `Gtk.DragSource` whose content provider carries a Python GObject (or a `str` token id); each column and the pool is a widget with a `Gtk.DropTarget` accepting that GType; `drag-end` on the source removes the tag from the old column. No text-based payload is needed, so repeated words stay distinct (matches the project's "never align by word text" rule).
- Requirement 5: `GstPlay` with `set_rate()` or `playbin3` + `scaletempo` as `audio-filter`/`audio-sink` gives speed 0.7-1.0 without pitch change; looping is app-driven (seek on EOS/`about-to-finish`). Since the app already generates files via Piper, GStreamer merely plays local files, so a minimal pipeline suffices.
- Requirement 3: PyGObject's GLib main loop integrates with Python threads via `GLib.idle_add`; PyGObject 3.50+ also ships an asyncio event-loop integration (`gi.events`), which would let the existing `async` pydantic-ai calls run on the GTK loop — not re-verified here (see Gaps).
- Requirement 7 on Hyprland: GTK4/libadwaita apps use client-side decorations; Hyprland's forced maximized state means the Adw header bar renders without rounded corners/shadows when tiled, which is cosmetic. Being a Wayland-native toolkit, HiDPI/fractional scaling and native file dialogs (`Gtk.FileDialog`, which goes through the xdg-desktop-portal if present) work without XWayland.
- Learning curve for a Qt developer: GObject signals (`widget.connect("clicked", handler)`) and `GObject.Property` bindings (`bind_property`) are the direct analogues of signals/slots and Qt properties; MVVM maps naturally onto `Gio.ListStore` + `Gtk.ListView`/`Gtk.SignalListItemFactory` and `Gtk.Expression` bindings, but the "factory" list model is the biggest conceptual shift from `QAbstractItemModel`.
- Portability: feasible on Windows/macOS but the libadwaita look is GNOME-specific, and packaging there is a multi-day DIY effort compared with PySide6's wheels.

### Gaps
- Could not fetch libadwaita API docs to confirm the current widget list and the exact version in which `Adw.NavigationSplitView` (1.4), `Adw.PreferencesDialog` (1.5), `Adw.Spinner`/`Adw.ButtonRow` (1.6) appeared; the 1.9/1.10 changelogs were also not retrievable.
- No source found that evaluates pygobject-stubs under `pyright --strict` specifically (completeness of overloads, `Any` leakage); the stubs are generated from GIR data and known to need per-library config, but strict-mode noise level is unverified.
- PyGObject asyncio integration (`gi.events.GLibEventLoopPolicy`, introduced around 3.50) was not confirmed by a fetched source.
- GstPlay reference page (loop/repeat support, whether rate changes preserve pitch internally) was not reachable; the scaletempo page confirms pitch-preserving rate changes only via seek events.
- No verified current recipe for bundling a PyGObject + libadwaita app as a Windows installer or macOS .app in 2026 (gtk-mac-bundler era docs only).
- Flathub policy specifics for Python/uv-based apps (offline builds from `uv.lock`) not researched.

---

## Key Question 2: Toga / BeeWare status 2026

### Takeaway
Toga 0.5.7 (1 Oct 2026, BSD-3, Python ≥3.11) is active (releases May/Jul/Jul/Oct 2026, a new Qt backend with full widget coverage in Q1 2026, a "Scaffold" navigation layer started in Q4 2026) but its GTK4/libadwaita backend is still partial (as of 0.5.7 no working GTK4 multiline text input), and no drag-and-drop or audio widget could be found, so items 4 and 5 would need escape hatches into the native toolkit.

### Cited Findings
- Latest release 0.5.7 uploaded 2026-10-01; `requires_python >=3.11`; license expression BSD-3-Clause; release cadence: 0.5.3 (2025-12-03), 0.5.4 (2026-05-06), 0.5.5 (2026-07-02), 0.5.6 (2026-07-08), 0.5.7 (2026-10-01) — [PyPI JSON toga](https://pypi.org/pypi/toga/json)
- 0.5.3 added a Qt backend "for KDE-based desktops", a GTK DateInput, and GTK4 support for several widgets — [Toga releases v0.5.3](https://toga.beeware.org/en/v0.5.3/about/releases/)
- Release notes: early GTK4 support is enabled with `TOGA_GTK=4`; later the GTK4 backend "integrated with libadwaita for ActivityIndicator, Window, and App"; 0.5.6 requires PyGObject 3.55.1 and dropped Debian 12 / Ubuntu 22.04; 0.5.6 Qt backend integrates with system Qt themes incl. Breeze — [Toga release history](https://toga.beeware.org/en/stable/about/releases/)
- BeeWare toga-code-editor PR (Oct 2026): recipe is "GTK 3 only, since Toga 0.5.7 has no working GTK 4 multiline input"; Qt backend selected with `TOGA_BACKEND=toga_qt` because both GTK and Qt register as `linux` — [beeware/toga-code-editor PR #6](https://github.com/beeware/toga-code-editor/pull/6)
- Toga GTK platform docs: GTK4 support described as experimental (v0.5.3 docs); needs `gir1.2-gtk-4.0`/`gtk4`; libadwaita integration needs libadwaita ≥1.5 (`gir1.2-adw-1`/`libadwaita`); toga-gtk requires Python 3.10+, GTK ≥3.22 and libgirepository 2.0 — [Toga GTK (latest)](https://toga.beeware.org/en/latest/reference/platforms/linux/gtk); [Toga GTK v0.5.3](https://toga.beeware.org/en/v0.5.3/reference/platforms/linux/gtk/)
- 2026 Q2 roadmap: Q1 2026 delivered the new Qt backend with full widget coverage, better Tree/Table column handling, Tree on Windows; the quarter's "biggest Toga news" is a design plan for "Big Picture" app design (navigation) — [BeeWare 2026Q2 roadmap](https://beeware.org/news/buzz/2026/2026q2-roadmap/); Q4 2026 roadmap reports implementation of the new "Scaffold" layer has started — [BeeWare 2026Q4 roadmap](https://beeware.org/news/buzz/2026/2026q4-roadmap/)
- May 2026 status: Canvas gained drawing-context attributes + save/restore, dark-mode detection, dialog fixes on macOS 26 — [May 2026 status update](https://beeware.org/news/buzz/2026/may-2026-status-update/)
- Toga roadmap page lists planned widgets (ComboBox, Switch, DateInput, NumberInput, SearchInput ...) and does not mention drag and drop — [Toga roadmap](https://toga.beeware.org/en/stable/about/roadmap/)
- Testing: the `toga-dummy` backend implements the full platform interface without drawing, exposes an API to check widget behaviour; chosen when it is the only backend installed or `TOGA_BACKEND=toga_dummy` — [Toga testing backend](https://toga.beeware.org/en/stable/reference/platforms/testing/)

### Inferences
- Items 1, 2 (Box layouts, SplitContainer, Selection, Table/DetailedList), 3 (TextInput, MultilineTextInput, Selection, ProgressBar/ActivityIndicator, async handlers) and 6 (PasswordInput, dialogs) are within Toga's standard widget set; item 4's drag-and-drop and item 5's audio have no Toga abstraction found, which would force per-backend "native widget" code, undermining the cross-platform value.
- Toga's GTK backend is still GTK3-first; on Hyprland GTK3 runs natively on Wayland, but the "modern libadwaita look" the developer wants is only partially there (Window/App/ActivityIndicator) and only under the experimental `TOGA_GTK=4` flag.
- Briefcase (the BeeWare packager) is the natural packaging path (Flatpak/AppImage/system packages on Linux, MSI on Windows, .app on macOS) — not re-verified in this session.

### Gaps
- The widgets-by-platform table (toga.beeware.org) could not be fetched; existence of SplitContainer on the GTK4 and Qt backends in 0.5.7 is unverified.
- No GitHub issue on Toga drag-and-drop was found in search; absence of the feature is inferred from roadmap/docs, not confirmed by a maintainer statement.
- No audio/media widget found; not confirmed by a fetched widget list.
- Briefcase version/date and its Flatpak template status were not retrieved (GitHub API access blocked).

---

## Key Question 3: Slint Python bindings

### Takeaway
Slint-python 1.18.1b1 (21 Sept 2026) is still officially beta ("APIs mostly stable", PyPI classifier "3 - Alpha"), Python ≥3.12, triple-licensed (GPLv3 / royalty-free with mandatory "AboutSlint" attribution / commercial); UI is declared in `.slint` files with a generated typed Python wrapper, drag-and-drop (`DragArea`/`DropArea`) exists since 1.17 (June 2026), it runs on Wayland through winit (now the default backend everywhere), has a full asyncio event loop, but has no audio API and no native file dialogs of its own.

### Cited Findings
- PyPI `slint` latest 1.18.1b1 (pre-release) released Sept 21, 2026; requires Python ≥3.12 (wheels tagged cp311-abi3; classifiers inconsistent); license "GPLv3 and Other/Proprietary"; description: "Slint-python is in a beta phase of development"; classifier "3 - Alpha"; generates type stubs via `slint-compiler`; runs on a full asyncio event loop; pipes/subprocesses only on Unix-like platforms — [PyPI slint](https://pypi.org/project/slint/)
- README: UIs are `.slint` files exporting components (e.g. inheriting `Window`) with properties, callbacks, `std-widgets.slint`; Python loads via `slint.load_file()` or `slint.loader` (sys.path search); properties are attributes; callbacks set by assignment or `@slint.callback` on a subclass; `slint.ListModel` / subclass `slint.Model` (`row_count`, `row_data`, `set_row_data`, `notify_row_*`); structs/enums exposed; event loop is an asyncio loop (`slint.run_event_loop(coroutine)`); `uvx slint-compiler -f python -o app_window.py app-window.slint` generates typed wrappers "that work with type checkers such as mypy, Pyre, and ty"; prebuilt binaries for macOS/Windows/Linux, else `uv` builds from source with Rust — [slint python README](https://raw.githubusercontent.com/slint-ui/slint/master/api/python/slint/README.md)
- Changelog: 1.15.0 (2026-02-04) "slint-compiler: added support for generating Python stubs"; 1.16.0 (2026-04-16) "The winit backend is now the default on all platforms. (Qt is no longer the default on Linux)"; 1.17.0 (2026-06-24) "Added `DragArea` and `DropArea` elements, as well as the `data-transfer` type for drag and drop support within a window", Python `int` callback args now `int`, asyncio signal handlers; 1.17.1 (2026-07-07) "winit: Fixed wrong initial window size on Wayland"; 1.18.0 (2026-09-16) Qt native DnD to other apps, "winit: Fixed the first frame being rendered at the wrong size on Wayland, and windows being auto-sized below their preferred size with fractional scale factors", musl wheels, Ctrl-C raises KeyboardInterrupt, GC fix for model wrappers; 1.18.1 (2026-09-21) Python `del model[-1]` fix; no audio/media entries in 1.15-1.18 — [Slint CHANGELOG](https://raw.githubusercontent.com/slint-ui/slint/master/CHANGELOG.md)
- DnD semantics: `DropArea` accepts drops from a `DragArea` (or other apps where supported); payload is an opaque `data-transfer` value built/read by host-language code; `allow-copy/move/link` on the source, `can-drop` callback returns a `DragAction`, `dropped`, `drag-finished(action)` lets a move source remove the original, `has-drag` for hover feedback — [Slint DnD guide](https://docs.slint.dev/latest/docs/slint/guide/development/drag-and-drop/); [Slint 1.17 blog](https://slint.dev/blog/slint-1.17-released)
- Licensing (repo LICENSE.md): three options — Royalty-free License (free for proprietary desktop/mobile/web, not embedded, must disclose Slint use via the `AboutSlint` widget or Slint badge, otherwise commercial license needed), GPLv3, Commercial (paid) — [Slint LICENSE.md](https://raw.githubusercontent.com/slint-ui/slint/master/LICENSE.md); Royalty-free 2.0 text: attribution via `AboutSlint` in an About screen reachable from the top-level menu, or splash screen, or badge on the download webpage — [LicenseRef-Slint-Royalty-free-2.0](https://unpkg.com/slint-ui@1.12.0/LICENSES/LicenseRef-Slint-Royalty-free-2.0.md)
- Python bindings moved from alpha to beta in Slint 1.11 (April 23, 2025) — [Slint 1.11 blog](https://www.slint.dev/blog/slint-1.11-released)
- winit (Slint's windowing layer) contains a Wayland `wp_fractional_scaling` module — [winit docs](https://doc.servo.org/winit/platform_impl/linux/wayland/types/wp_fractional_scaling/index.html)

### Inferences
- Item 4 is covered by `DragArea`/`DropArea` with an opaque payload that Python constructs (e.g. a struct with sentence id + token index); per-column styling (orange/red) is trivial in `.slint` declarative states. Item 2's interleaved grid is a `for` loop over a model of columns, each a `VerticalLayout` of tags.
- Item 5: Slint has no audio playback; the app would need a Python audio library (e.g. `sounddevice`/`pyaudio` + resampling, or GStreamer via PyGObject anyway) and no built-in native file dialog — a third-party dialog library would be needed.
- Item 3 is natural: the event loop is asyncio, so pydantic-ai coroutines run directly and update properties on completion.
- Typing story is strong for the UI contract (generated wrappers), but the package is beta on Python ≥3.12 only (fine for this 3.13 project).
- Look: Slint renders its own widgets (Fluent/Material/Cupertino/"Cosmic" styles in std-widgets) — it will not look like a libadwaita app on GNOME, but is consistent across OSes. Style list not re-verified here.
- The royalty-free attribution requirement is a product decision the developer must accept (or use GPLv3 if the app is open source).

### Gaps
- Slint docs for Python (`docs.slint.dev/latest/docs/python/`) and pricing page were unreachable; exact commercial pricing and the current std-widgets style list unverified.
- No information found on native file dialogs in Slint-python (Slint has no dialog API; whether `slint` ships any helper is unknown).
- No evaluation of pyright-strict compatibility of the generated wrappers (README names mypy/Pyre/ty, not pyright).
- Testing story (headless/test-driver for Slint-python) not researched.
- PyInstaller/Nuitka packaging of Slint-python apps not verified.

---

## Key Question 4: Dear PyGui

### Takeaway
Dear PyGui 2.3.1 (1 May 2026, MIT, Python 3.8-3.14) is actively maintained and GPU-rendered (OpenGL 3 on Linux) with an immediate-mode "tool/game-dev" aesthetic and deep theming; it supports item-level drag payloads (ImGui payload model), has "asynchronous function support", but no audio, no native file dialogs of its own, and its Linux viewport runs through GLFW/X11 with documented Wayland-compositor glitches (window not closing on KDE/Sway).

### Cited Findings
- Latest 2.3.1 released May 1, 2026; requires Python ≥3.8, classifiers 3.8-3.14; MIT; wheels for Windows x86-64, macOS 13+ ARM64, Linux x86-64 (glibc ≥2.5) and ARM64; rendering: DirectX 11 (Windows), Metal (macOS), OpenGL 3 (Linux) — [PyPI dearpygui](https://pypi.org/project/dearpygui/)
- Release history: 1.11.1 (Mar 15, 2024) was the last 1.x; 2.0.0 (Oct 16, 2024), 2.1.0 (Jul 7, 2025), 2.1.1 (Nov 14, 2025), 2.2 (Feb 17, 2026), 2.3 (Apr 16, 2026), 2.3.1 (May 1, 2026) — [PyPI dearpygui history](https://pypi.org/project/dearpygui/#history)
- README: built on Dear ImGui + ImPlot + imnodes, immediate-mode paradigm using the GPU, "complete theme and style control", asynchronous function support, canvas drawing API, node editor, built-in demo, runtime metrics/debugger; "continued maintenance and development is a full-time effort" funded by sponsors — [DearPyGui README](https://raw.githubusercontent.com/hoffstadt/DearPyGui/master/README.md)
- Theming docs: theme components (Core/Plots/Nodes), default themes propagate to children, `theme_component` with `dpg.mvAll` — [DPG themes docs](https://dearpygui.readthedocs.io/en/latest/documentation/themes.html)
- Wayland: issue #2173 (`destroy_context` does not close the window, only freezes it) reported on Ubuntu 22.04/KDE and SwayWM, "Probably Linux-only", marked fixed by PR #2275 — [DearPyGui issue #2173](https://github.com/hoffstadt/DearPyGui/issues/2173)
- Upstream Dear ImGui's GLFW backend has Wayland-specific issues such as "DPI scaling seems to be applied twice on style on Wayland" (#9422) and requests for a pure Wayland backend because GLFW/SDL backends lack layer-shell support (#9365) — [imgui #9422](https://upd.dev/ocornut/imgui/issues/9422); [imgui #9365](https://upd.dev/ocornut/imgui/issues/9365)
- `create_viewport()` has a `decorated` flag controlling the OS title bar — [DPG application lifecycle docs mirror](https://tessl.io/registry/tessl/pypi-dearpygui/files/docs/application-lifecycle.md)
- Dear ImGui DnD model (what DPG wraps): source sets a payload under a type string ≤32 chars (`SetDragDropPayload`), target accepts via `AcceptDragDropPayload(type)` only if the type matches — [imgui drag-and-drop docs mirror](https://www.mintlify.com/ocornut/imgui/advanced/drag-and-drop)
- Dear PyGui does not use native system widgets; it draws its own via OpenGL/Metal/DirectX — [LinuxAdictos on DPG 1.0](https://www.linuxadictos.com/en/dear-pygui-an-easy-to-use-python-graphical-user-interface-framework.html)

### Inferences
- Item 4 is achievable: in DPG every item can carry a `drag_payload` child with `payload_type`, and containers/items accept via `drop_callback` filtered by `payload_type` (ImGui mechanism); dragging between columns/groups is the standard use case.
- Items 1-3, 6 are achievable with DPG windows/groups/tables/combos/input_text (password flag) and progress bars; item 5 needs an external audio library, and item 7's "native file dialog" needs a third-party package (DPG ships only its own ImGui-drawn file dialog).
- Look: a developer who finds Qt Widgets "ugly" is unlikely to prefer the ImGui aesthetic (flat, dense, tool-like) despite full theme control; it does not follow any OS design language and has no HiDPI text rendering comparable to GTK/Qt.
- Wayland: DPG on Hyprland runs via GLFW; depending on the GLFW build it may use XWayland (blurry under fractional scaling) or native Wayland (libdecor decorations); the #2173 history shows compositor-specific bugs.
- Testing: immediate-mode UI has no widget tree to introspect from pytest beyond DPG's item registry; headless testing requires a GPU context.

### Gaps
- DPG's own drag/drop documentation page (`add_drag_payload`, `drop_callback` signature) could not be fetched; the mechanism is inferred from the ImGui model and general knowledge.
- Whether DPG's Linux viewport is built with GLFW's Wayland backend or X11-only was not confirmed from source (file path guesses returned 404).
- No 2.x release notes (what changed in 2.0: ImGui 1.9x/docking) could be retrieved.
- Type stubs: DPG ships Python-side wrappers with signatures, but pyright-strict quality unverified.

---

## Key Question 5: Kivy + KivyMD

### Takeaway
Kivy stable is still 2.3.1 (Dec 26, 2024, MIT, Python 3.8-3.13; SDL2-based, Kivy 3.0 with SDL3 unreleased), KivyMD finally shipped 2.0.0 on Aug 6, 2026 (MIT, "Beta" classifier, Kivy ≥2.3.0, Material-inspired with M3 ripple/new widgets); drag is a `DragBehavior` mixin with no drop-target abstraction, `SoundLoader` has `loop` but pitch only on the SDL audio provider, native Wayland is contested (SDL2 under XWayland is the working path), and file dialogs go through plyer's zenity/kdialog wrappers.

### Cited Findings
- Kivy latest 2.3.1 released Dec 26, 2024; Python ≥3.8, classifiers 3.8-3.13; MIT — [PyPI Kivy](https://pypi.org/project/Kivy/)
- KivyMD latest 2.0.0 released Aug 6, 2026; Python ≥3.7 (classifiers to 3.13); MIT; classifier "4 - Beta"; requires Kivy ≥2.3.0, plus `MaterialColor>=3.0.3` and `MaterialShapes`; described as "inspired by Google's Material Design" — [PyPI kivymd](https://pypi.org/project/kivymd/)
- KivyMD changelog items: "New M3 ripple effect", new widgets `MDLoadingIndicator` and `MDCarousel`, "Implement declarative style for all KivyMD widgets" — [KivyMD changelog](https://kivymd.readthedocs.io/en/latest/changelog/index.html)
- Audio: `SoundLoader.load()` returns the best provider class per file type; `loop` is a `BooleanProperty` (since 1.8.0) that auto-restarts on finish; `pitch` ("2 is an octave higher, .5 one below") "is only implemented for SDL3 audio provider yet" in master docs (older versions say SDL2) — [Kivy core.audio docs](https://kivy.org/doc/stable/api-kivy.core.audio.html)
- Drag: `kivy.uix.behaviors.drag.DragBehavior` makes a widget draggable within `drag_rectangle` (`drag_timeout`, `drag_distance`) — [DragBehavior source](https://kivy.readthedocs.io/en/latest/_modules/kivy/uix/behaviors/drag.html); `collide_point()` is the hit-test, and `on_touch_*` handlers "perform no collision checks" themselves; only Layouts position children — [Kivy Widget docs](https://kivy.org/doc/stable/api-kivy.uix.widget.html)
- SDL3/Kivy 3.0: a python-for-android maintainer (March 2025) said "only Kivy 3.0.0 will support SDL3" and both SDL2 and SDL3 will be supported "for a long time" — [python-for-android issue #3136](https://github.com/kivy/python-for-android/issues/3136); Kivy issue proposes a `MIGRATION-2.3.x_to_3.0.0.md` for breaking changes — [kivy issue #8585](https://redirect.github.com/kivy/kivy/issues/8585)
- Wayland: a 2021 PinePhone forum post claims Kivy "supports Wayland and uses a SDL2 backend", while a Dec 2024 Purism forum post says "Kivy does not support native Wayland events" and no efforts are known — [Pine64 forum](https://forum.pine64.org/showthread.php?pid=89009); [Purism forum](https://forums.puri.sm/t/phosh-app-developer-forum/27140?page=2); Yocto recipes build Kivy with `USE_WAYLAND` from distro features — [meta-openembedded kivy 2.3.0 recipe](https://gbmc.googlesource.com/openbmc/+/e3fb95bf86bd5c874afdc1c7fc2e950d7a5e229a/meta-openembedded/meta-python/recipes-devtools/python/python3-kivy_2.3.0.bb)
- SDL3 prefers Wayland over X11 by default when built with Wayland support — [Phoronix SDL3 Wayland default](https://www.phoronix.com/news/SDL-3.0-Wayland-Default-Prefer)
- plyer offers a native file chooser API where "on windows/mac/linux, commonly found libraries and programs will be used"; reported issues: Zenity on Ubuntu 24 no longer supports `--name`, and `plyer.filechooser.open_file()` not responding to mouse in a Kivy window — [PyPI Plyer](https://pypi.org/project/Plyer/)

### Inferences
- Item 4 requires hand-rolled drop detection: on `on_touch_up`, iterate candidate columns, `collide_point`, then `remove_widget`/`add_widget` — workable but entirely custom, including the drag preview.
- Item 5: `loop` is built in; speed 0.7-1.0 via `pitch` changes pitch along with tempo (resampling), and is provider-dependent (SDL2 in 2.3.1) — not the pitch-preserving behaviour users expect from a "speed" control.
- Item 7: on Hyprland, Kivy 2.3.1 (SDL2) most reliably runs through XWayland, which is blurry under fractional scaling; a native Wayland path depends on how the SDL2 wheel was built and on Kivy's event handling, which is contested. Native file dialogs via plyer depend on zenity/kdialog being installed (Omarchy ships neither by default, unverified).
- Look: KivyMD 2.0 is Material (Android-like), not a desktop design language; the Kivy core widgets are stylised and touch-oriented.
- Testing: Kivy apps can be unit-tested with its `GraphicUnitTest`, but needs a window/GL context — not researched here.

### Gaps
- No official Kivy statement on native Wayland support in 2.3.1 found; both forum sources are secondary.
- Kivy 3.0 release date unknown (no release found as of Oct 2026).
- KivyMD 2.0.0 release notes (what "2.0" means versus the long-lived 2.0.0 dev branch; M3 completeness) not retrieved beyond the changelog excerpts.
- KivyMD and Kivy type-stub/pyright situation not researched (Kivy is Cython-heavy with `.pyx` modules; Kivy properties are dynamic).

---

## Key Question 6: CustomTkinter (Tkinter)

### Takeaway
CustomTkinter 6.0.0 (June 24, 2026, MIT) is alive again after a 2.5-year gap, gives Tk a flat light/dark look with HiDPI only documented for Windows/macOS, but Tk itself has no Wayland backend (XWayland → blurry under fractional scaling on Hyprland), has no drop-target abstraction, no audio, and no type stubs beyond CPython's tkinter typeshed.

### Cited Findings
- Latest 6.0.0 released Jun 24, 2026; Python ≥3.7; license string "MIT License (Creative Commons Zero v1.0 Universal)" — [PyPI customtkinter](https://pypi.org/project/customtkinter/); piwheels mirror shows 6.0.0 (2026-06-24) above 5.2.2 (Jan 2024) — [piwheels customtkinter](https://www.piwheels.org/project/customtkinter/)
- FreeBSD port update to 6.0.0 adds `darkdetect` as runtime dependency and drops `typing-extensions` — [FreeBSD ports distinfo](https://cgit.freebsd.org/ports/commit/x11-toolkits/py-customtkinter/distinfo)
- README: widgets follow system appearance or manual light/dark mode; built-in color themes blue (default), dark-blue, green; Windows, macOS, Linux supported; "All widgets and windows support HiDPI scaling on Windows and macOS" (Linux not listed); described as "under active development"; developers Tom Schimansky and Federico Spada; MIT — [CustomTkinter Readme](https://raw.githubusercontent.com/TomSchimansky/CustomTkinter/master/Readme.md)
- Third-party activity signals: last GitHub push Feb 24, 2026 per a trend tracker; a Snyk snapshot (pre-2026) labelled it inactive — [gittrend.io](https://gittrend.io/repo/TomSchimansky/CustomTkinter); [snyk advisor](https://snyk.io/advisor/python/customtkinter)
- Tk/tkinter has no Wayland backend: a Python discourse feature request "Wayland support for TKInter" exists — [discuss.python.org](https://discuss.python.org/t/feature-request-wayland-support-for-tkinter/75198.md); XWayland apps under fractional scaling are rendered at lower resolution and pixel-stretched (blurry); only KWin decouples X11 scaling by default — [GNOME discourse](https://discourse.gnome.org/t/is-there-any-way-i-could-fix-or-mitigate-the-blur-on-applications-using-xwayland-caused-by-fractional-scaling/17052)
- Hyprland wiki documents the XWayland HiDPI workaround (`xprop` global scale + `GDK_SCALE`, `XCURSOR_SIZE`) — [Hyprland wiki XWayland](https://wiki.hypr.land/0.27.1/Configuring/XWayland)

### Inferences
- Items 1-3, 6 are feasible (CTkFrame/CTkOptionMenu/CTkEntry with `show="*"`, CTkProgressBar, `after()` polling from a thread); item 2's resizable two-pane needs the plain `ttk.PanedWindow` since CTk has no split widget; item 4 needs manual `<B1-Motion>`/`<ButtonRelease>` tracking with `winfo_containing` to find the drop column — feasible but all custom; item 5 needs an external audio library; native file dialogs via `tkinter.filedialog` (Tk's own dialog on Linux, not the portal).
- On Hyprland the whole app runs under XWayland, so sharpness and fractional scaling are worse than today's Qt6 app (which runs natively on Wayland).
- Typing: typeshed covers `tkinter`; CustomTkinter's own annotations exist but no `py.typed` audit was found — pyright strict usability unverified.

### Gaps
- 6.0.0 changelog/release notes not retrievable (what changed besides `darkdetect`).
- No source on CustomTkinter HiDPI behaviour on Linux/Wayland specifically.

---

## Key Question 7: wxPython (Phoenix)

### Takeaway
wxPython 4.3.2 (Oct 12-13, 2026, LGPL with wxWindows exception, Python 3.10-3.15) now tracks the API-unstable wxWidgets 3.3.x branch, ships no Linux wheels on PyPI (source build or distro package), uses the GTK3 port (no GTK4 port exists), so on Hyprland it runs as a native-Wayland GTK3 app with a classic desktop look.

### Cited Findings
- Latest 4.3.2 released Oct 13, 2026 (PyPI); requires Python ≥3.10, wheels for CPython 3.10-3.15 on macOS and Windows only; Linux only as 65.9 MB sdist; license LGPL-2.0-or-later WITH WxWindows-exception-3.1 — [PyPI wxPython](https://pypi.org/project/wxPython/)
- CHANGES: 4.3.2 (12-Oct-2026) updated to wxWidgets 3.3.4, Python 3.15 wheels, dropped 32-bit Windows wheels, "many improvements to the generated .pyi files", needs SIP ≥6.10; 4.3.1 (29-Jul-2026) RPATH fix on Linux (wx.richtext import); 4.3.0 (27-Jul-2026) switched to tracking wxWidgets master (3.3.x) and warns 3.3.x is "API/ABI unstable" so API changes may occur between 4.3.x releases — [Phoenix CHANGES.rst](https://raw.githubusercontent.com/wxWidgets/Phoenix/master/CHANGES.rst); [wxPython 4.3.0 news](https://wxpython.org/news/2026-07-27-wxpython-430-release/index.html)
- No GTK4 port: wxWidgets stated (Jan 2021) GTK 4's API "is so incompatible ... that huge parts of wxGTK would have to be rewritten" — [wxWidgets blog 2021](https://www.wxwidgets.org/blog/2021/01/wxwidgets-in-2020-and-beyond); an Aug 2026 wx-dev thread about Wayland session management requires "very new GTK (later than ... 3.24.52)", i.e. GTK3 — [wx-dev thread](https://groups.google.com/g/wx-dev/c/-_5tcQJT_NY)
- Wayland: wxPython forum says "wxPython works on Wayland. If there are any problems, please report them... most likely they will be upstream wxWidgets issues" — [discuss.wxpython.org](https://discuss.wxpython.org/t/ubuntu-and-wayland/40301)

### Inferences
- Capability-wise wxPython covers items 1-3, 6-7 with classic widgets (`wx.SplitterWindow`, `wx.ListCtrl`, `wx.Choice`, `wx.TextCtrl(style=wx.TE_PASSWORD)`, `wx.FileDialog` → native GTK dialog, `wx.CallAfter` for thread→UI updates); item 4 uses `wx.DropSource`/`wx.DropTarget` with custom data objects (text/custom format), workable but verbose; item 5 has `wx.adv.Sound` (no loop/speed control to the extent needed) → external audio.
- Look: GTK3 Adwaita widgets, not libadwaita; it will look like a 2015 GNOME app, which likely does not meet the "modern look" goal.
- Typing: the `.pyi` improvements in 4.3.2 are a plus; strict-mode completeness unverified.
- Linux install on Arch via `python-wxpython` distro package avoids the sdist build; packaging with PyInstaller is well-trodden.

### Gaps
- Specific GTK3-on-Wayland issues for wxPython 4.3.x not researched in depth.
- No data on wx.adv.Sound capabilities (loop/speed) retrieved; inference only.

---

## Key Question 8: Rust bindings (Iced/egui) and other notable toolkits 2024-2026 (Flet)

### Takeaway
There is no production-ready Iced or egui binding for Python: `pyiced` is archived (Aug 2023) and `IcedPyGui` 0.4.1 (June 2026) is a one-person early-stage wrapper that caps at Python <3.13. The notable non-web newcomer is Flet 1.0.x (Flutter renderer, Apache-2.0, Oct 2026), which has Draggable/DragTarget controls and an audio service with `playback_rate` and loop mode, but is not a native toolkit and renders Material widgets.

### Cited Findings
- `pyiced` repository archived by the owner on Aug 29, 2023 (read-only) — [github.com/Kijewski/pyiced](https://github.com/Kijewski/pyiced)
- `IcedPyGui` latest 0.4.1 uploaded 2026-06-03; `requires_python <3.13,>=3.10`; license "GNU"; summary "Python wrapper for Rust Iced"; releases 0.3.0/0.3.1 (2024-10-30), 0.4.0 (2025-05-08), 0.4.1 (2026-06-03) — [PyPI JSON IcedPyGui](https://pypi.org/pypi/IcedPyGui/json); author describes it as their "first published project", some widgets partial, modal discontinued — [PyPI IcedPyGui](https://pypi.org/project/IcedPyGui)
- Flet latest 1.0.5 released Oct 21, 2026; Python ≥3.10; Apache-2.0; "Flet uses Flutter to render UI"; builds standalone executables/bundles for iOS, Android, Windows, Linux, macOS and web — [PyPI flet](https://pypi.org/project/flet/)
- Flet `Draggable` (with `content_feedback`) and `DragTarget` accept drags of the same `group`; `on_accept` receives `e.src_id` to look up the dragged control; also `on_will_accept`, `on_move`, `on_leave` — [Flet Draggable](https://docs.flet.dev/controls/draggable); [Flet DragTarget](https://docs.flet.dev/controls/dragtarget)
- Flet audio (`flet_audio` service in 1.x): `playback_rate` (default 1.0; iOS/macOS limited to 0.5-2x), `release_mode` enum with `LOOP` ("plays again after completion"), `RELEASE`, `STOP` — [Flet audio](https://docs.flet.dev/audio); [ReleaseMode](https://docs.flet.dev/audio/types/releasemode)

### Inferences
- Iced/egui via Python is not a viable path for this app in 2026: IcedPyGui excludes Python 3.13 outright.
- Flet would satisfy items 1-6 functionally (drag/drop, audio loop and rate, file picker, dark mode) and packages for all three desktops, but it is a Flutter engine process driven by Python, Material-styled, not GNOME-native, and its desktop runtime is heavier than any toolkit above; it was outside the "native" scope so only lightly checked.

### Gaps
- egui Python bindings: no maintained project found in searches; not exhaustively verified.
- Flet's Linux/Wayland behaviour (Flutter Linux embedder is GTK3-based) and its pyright typing were not researched.

---

## Key Question 9: Cross-toolkit capability check against items 1-7 (summary table with evidence pointers)

### Takeaway
Only GTK4/libadwaita covers all seven items with first-party, documented APIs (DnD of Python objects, GStreamer audio with pitch-preserving rate and looping, portal file dialogs, native Wayland, Flatpak); Slint covers 1-4, 6 natively but has no audio/dialogs; Toga covers 1-3, 6-7 but has no DnD/audio abstraction and an incomplete GTK4 backend; Dear PyGui, Kivy/KivyMD, CustomTkinter and wxPython can all be made to work but each lacks either native Wayland, a drop-target model, or audio.

### Cited Findings
- Item 4 (object DnD between containers): GTK4 `Gtk.DragSource`/`Gtk.DropTarget` with GObject payloads — [PyGObject example](https://raw.githubusercontent.com/GNOME/pygobject/main/docs/tutorials/gtk4/examples/drag_and_drop.py); Slint `DragArea`/`DropArea` since 1.17.0 (2026-06-24) — [Slint CHANGELOG](https://raw.githubusercontent.com/slint-ui/slint/master/CHANGELOG.md); Dear ImGui payload-type model — [imgui DnD](https://www.mintlify.com/ocornut/imgui/advanced/drag-and-drop); Kivy `DragBehavior` only moves widgets, drop detection via `collide_point` — [Kivy DragBehavior](https://kivy.readthedocs.io/en/latest/_modules/kivy/uix/behaviors/drag.html); Toga roadmap lists no DnD — [Toga roadmap](https://toga.beeware.org/en/stable/about/roadmap/); Flet Draggable/DragTarget — [Flet DragTarget](https://docs.flet.dev/controls/dragtarget)
- Item 5 (audio loop + speed): GStreamer `scaletempo` pitch-preserving rate via seek — [scaletempo](https://gstreamer.freedesktop.org/documentation/audiofx/scaletempo.html); Kivy `Sound.loop` + provider-limited `pitch` — [Kivy audio](https://kivy.org/doc/stable/api-kivy.core.audio.html); Flet `playback_rate` + `ReleaseMode.LOOP` — [Flet audio](https://docs.flet.dev/audio); Slint 1.15-1.18 changelog has no audio entries — [Slint CHANGELOG](https://raw.githubusercontent.com/slint-ui/slint/master/CHANGELOG.md); DPG README lists no audio feature — [DPG README](https://raw.githubusercontent.com/hoffstadt/DearPyGui/master/README.md)
- Item 3 (background work): Slint event loop is a full asyncio loop — [slint README](https://raw.githubusercontent.com/slint-ui/slint/master/api/python/slint/README.md); DPG "Asynchronous function support" — [DPG README](https://raw.githubusercontent.com/hoffstadt/DearPyGui/master/README.md)
- Item 7 (Wayland): Slint winit Wayland fixes in 1.17.1/1.18.0 — [Slint CHANGELOG](https://raw.githubusercontent.com/slint-ui/slint/master/CHANGELOG.md); wxPython works on Wayland via GTK3 — [discuss.wxpython.org](https://discuss.wxpython.org/t/ubuntu-and-wayland/40301); Tk has no Wayland backend — [discuss.python.org](https://discuss.python.org/t/feature-request-wayland-support-for-tkinter/75198.md); Kivy native Wayland contested — [Purism forum](https://forums.puri.sm/t/phosh-app-developer-forum/27140?page=2); DPG Wayland compositor bug #2173 — [DearPyGui #2173](https://github.com/hoffstadt/DearPyGui/issues/2173)
- Item 7 (Python 3.13): PyGObject ≥3.10 — [PyPI](https://pypi.org/project/PyGObject/); Toga ≥3.11 — [PyPI JSON](https://pypi.org/pypi/toga/json); Slint ≥3.12 — [PyPI](https://pypi.org/project/slint/); DPG 3.8-3.14 — [PyPI](https://pypi.org/project/dearpygui/); Kivy 3.8-3.13 — [PyPI](https://pypi.org/project/Kivy/); KivyMD to 3.13 — [PyPI](https://pypi.org/project/kivymd/); wxPython 3.10-3.15 — [PyPI](https://pypi.org/project/wxPython/); IcedPyGui <3.13 — [PyPI JSON](https://pypi.org/pypi/IcedPyGui/json)
- Item 7 (typing): pygobject-stubs 2.20.0 with Gtk4/Adw/Gst — [CHANGELOG](https://raw.githubusercontent.com/pygobject/pygobject-stubs/master/CHANGELOG.md); Slint generated typed wrappers — [slint README](https://raw.githubusercontent.com/slint-ui/slint/master/api/python/slint/README.md); wxPython 4.3.2 improved `.pyi` — [CHANGES.rst](https://raw.githubusercontent.com/wxWidgets/Phoenix/master/CHANGES.rst)
- Item 7 (testing): PyGObject headless Mutter/Xvfb guide — [testing guide](https://pygobject.gnome.org/guide/testing.html); Toga dummy backend — [Toga testing](https://toga.beeware.org/en/stable/reference/platforms/testing/)

### Inferences
- Summary matrix (✓ documented first-party; ~ feasible with custom code or third-party lib; ✗ not available / contradicts goal):

| Item | GTK4+Adw | Toga | Slint-py | Dear PyGui | Kivy/KivyMD | CustomTkinter | wxPython |
|---|---|---|---|---|---|---|---|
| 1 modes/header | ✓ (Adw.HeaderBar, ViewStack) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 split + grid | ✓ (Adw split views, Gtk.Grid/ListView) | ✓ (SplitContainer, GTK3) | ✓ | ✓ | ~ | ~ (ttk.PanedWindow) | ✓ |
| 3 bg AI call | ✓ (GLib/asyncio) | ✓ (asyncio) | ✓ (asyncio loop) | ✓ | ~ (Clock) | ~ (after()) | ✓ (CallAfter) |
| 4 tag DnD | ✓ | ✗ (no API found) | ✓ (1.17+) | ✓ (payload) | ~ (manual) | ~ (manual) | ~ (DropTarget) |
| 5 audio loop/speed | ✓ (GStreamer) | ✗ | ✗ | ✗ | ~ (pitch-shift only) | ✗ | ✗ |
| 6 settings dialogs | ✓ (Adw.PreferencesDialog, PasswordEntryRow) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 7 Wayland native | ✓ | ✓ (GTK3/4) | ✓ (winit) | ~ (GLFW; bugs) | ~ (contested) | ✗ (XWayland) | ✓ (GTK3) |
| 7 native file dialog | ✓ | ✓ | ✗ | ✗ | ~ (plyer/zenity) | ~ (Tk dialog) | ✓ |
| 7 pyright stubs | ✓ (pygobject-stubs) | ? | ✓ (generated) | ? | ✗/? | ? | ✓ (.pyi) |
| Modern look | GNOME/libadwaita | host-native (GTK3) | own styles | ImGui tool-look | Material (Android) | flat Tk | GTK3 classic |

- "✗" for audio means the toolkit has no audio API; in every such case the app could keep a separate audio layer (GStreamer via PyGObject, or a PortAudio-based library), which is independent of the UI toolkit choice.

### Gaps
- Typing quality under `pyright --strict` is unverified for every toolkit; only existence of stubs/wrappers is sourced.
- Screenshots/visual comparison were not collected (image hosts not fetched); look-and-feel statements are based on textual descriptions in official READMEs.
- Nuitka packaging was not researched for any toolkit.
