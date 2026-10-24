# Drag-and-drop word alignment editor: feasibility per Python UI option (state: 2026-10-24)

Scope: how the Birkenbihl "word alignment editor" (one column per source token, draggable target-word tags
identified by token index, unassigned pool, column states normal/flagged/empty, full re-render from immutable
state, validation + Save button) plus the secondary audio bar (infinite loop, speed 0.7-1.0, local WAV/MP3) can be
built in each candidate. Method: official docs/example galleries fetched as primary sources (GitHub repo clones of
nicegui, flet, slint, pywebview, textual, GNOME/pygobject, GNOME/gtk, qt/qtbase, qt/qtdeclarative; current wheels
from PyPI: nicegui 3.18.0, flet 1.0.5, flet-audio 1.0.5, reflex-enterprise 0.9.8, textual 8.2.8, pywebview 6.2.1,
slint 1.18.1b1, PySide6-Examples 6.12.0), plus web searches for bug trackers. Note: doc.qt.io, nicegui.io,
docs.flet.dev, slint.dev, pygobject.gnome.org could not be fetched directly from this environment (proxy denial);
I read the same content from the official source repositories / wheels instead and cite the repository file paths.

Reference point, the current PySide6 implementation in this repo (read from
`src/birkenbihl/gui/widgets/`): `word_tag.py` (101 lines) starts a `QDrag` with a `QMimeData` whose text is the
target token index and calls `drag.exec(Qt.DropAction.MoveAction)`; `grid_column.py` (192 lines) and
`unassigned_pool.py` (129 lines) call `setAcceptDrops(True)`, accept in `dragEnterEvent` if `mimeData().hasText()`
and emit `word_dropped(int(event.mimeData().text()))` in `dropEvent`; column states are set with
`setStyleSheet(theme.get_error_frame_style() / get_flagged_frame_style())` and a `QPushButton("✓ Stimmt")`;
`audio_bar.py` (148 lines) uses `QMediaPlayer.setLoops(QMediaPlayer.Loops.Infinite)`. Total editor+audio
≈ 813 lines of Python, 0 lines of non-Python. Installed Qt: PySide6 6.11.2 (`uv run python -c "import PySide6"`).

---

## 1. PySide6 (QWidgets QDrag/QMimeData vs. QGraphicsView vs. QListWidget InternalMove vs. QML Drag/DropArea)

### Takeaway
QWidgets drag-and-drop is fully Python (what the repo does today, ~800 lines), identifies tags by MIME payload
(the token index) and already does the full re-render. The alternatives inside Qt either add nothing for this
layout (QGraphicsView uses the same QDrag/dropEvent API; QListWidget InternalMove only moves rows between lists and
loses the index payload) or require a second language (QML: ~75 lines of QML for the Drag/DropArea pair in the
official example). Qt has no built-in keyboard alternative to a pointer drag in any of the four APIs. Wayland
drag-and-drop in Qt has a history of crashes (fixed in point releases) and compositor-specific failures.

### Cited Findings
- Official PySide6 widget example `draggabletext.py` (117 lines, all Python) shows the canonical pattern:
  `mime_data = QMimeData()`, `mime_data.setData('application/x-hotspot', ...)`, `drag = QDrag(self)`,
  `drag.setPixmap(pixmap)`, `drop_action = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction, ...)`;
  the target does `setAcceptDrops(True)`, `dragEnterEvent: if event.mimeData().hasText(): event.setDropAction(MoveAction)`,
  `dropEvent` reads `event.mimeData()` — [PySide6-Examples 6.12.0, examples/widgets/draganddrop/draggabletext/draggabletext.py](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/examples/widgets/draganddrop/draggabletext/draggabletext.py)
- QGraphicsView: the official `dragdroprobot.py` (254 lines) uses the *same* machinery inside a scene: a
  `QGraphicsItem.mouseMoveEvent` creates `QDrag(event.widget())`, items call `setAcceptDrops(True)` and implement
  `dragEnterEvent`/`dropEvent` reading `event.mimeData().hasColor()/colorData()`; `ItemIsMovable` exists as a flag
  for free movement (not for drop semantics) — [PySide6-Examples 6.12.0, examples/widgets/graphicsview/dragdroprobot/dragdroprobot.py](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/examples/widgets/graphicsview/dragdroprobot/dragdroprobot.py);
  `QGraphicsItem.GraphicsItemFlag` includes `ItemIsMovable`, `ItemIsFocusable` (verified by introspection of PySide6 6.11.2).
- QAbstractItemView drag modes available in PySide6 6.11.2: `NoDragDrop, DragOnly, DropOnly, DragDrop, InternalMove`
  (introspection). `InternalMove` is per-view; cross-list moves require `DragDrop` and a model `mimeData()/dropMimeData()`
  implementation (Qt model/view, not covered by an example in the PySide6-Examples wheel).
- QML drag-and-drop official example: `DragTile.qml` (≈55 lines: `MouseArea { drag.target: tile; onReleased: parent =
  tile.Drag.target !== null ? tile.Drag.target : root }`, `Drag.keys: [root.colorKey]`, `Drag.active:
  mouseArea.drag.active`, `Drag.hotSpot`) and `DropTile.qml` (≈15 lines: `DropArea { keys: [colorKey]; Rectangle {
  color: dragTarget.containsDrag ? "grey" : ... } }`) — [qtdeclarative examples/quick/draganddrop/tiles/DragTile.qml](https://github.com/qt/qtdeclarative/blob/dev/examples/quick/draganddrop/tiles/DragTile.qml),
  [DropTile.qml](https://github.com/qt/qtdeclarative/blob/dev/examples/quick/draganddrop/tiles/DropTile.qml)
- `DropArea` is "an invisible item which receives events when other items are dragged over it"; filtering is by
  `keys`; signals `entered`, `exited`, `positionChanged`, `dropped`. The docs contain nothing about keyboard
  operation — [DropArea QML Type](https://doc.qt.io/qt-6/qml-qtquick-droparea.html)
- `QDrag.exec()` on Linux/macOS "returns control without stopping the event loop"; "If any loops or operations are
  called while a drag operation is active, it will block the drag operation" — [PySide6 QDrag docs](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDrag.html)
- Wayland: QTBUG-87624 "Wayland client crash when QDrag is used" (crash if windows are shown/hidden during a drag;
  fix commits on dev/6.2/5.15 listed, status still shown as backlog on the tracker mirror) —
  [QTBUG-87624](https://bugreports.qt.io/browse/QTBUG-87624); QTBUG-112161 "forbidden cursor under Wayland only",
  fixed by "Client: Always populate mimedata in drags" merged to dev/6.6/LTS — [QTBUG-112161](https://bugreports.qt.io/browse/QTBUG-112161);
  QTBUG-115757 regression: segfault on drag-and-drop with Wayland in Qt 6.5.1–6.5.2, fixed upstream ("client: Fix
  crash on dnd updates after client facing drag ends"), shipped by Arch in qt6-wayland 6.5.2-2 and proper fix in 6.5.3 —
  [Arch FS#79345](https://bugs.archlinux.org/task/79345)
- Qt on Wayland (mutter): "Drag&Drop not working in Qt-Applications" after Fedora 38 Beta, works on sway —
  [GNOME mutter issue 2715](https://gitlab.gnome.org/GNOME/mutter/-/issues/2715); after a reorder drag on Wayland,
  Qt 6 UI stopped responding to hover until another click, "when starting the app with -platform xcb, the problem does
  not occur" — [QTBUG-109826](https://bugreports.qt.io/browse/QTBUG-109826)
- Hyprland specifically: no Qt-specific DnD bug report found; the one Arch thread found says GTK file managers
  mis-handle Ctrl-drag on Hyprland while "pcmanfm-qt does work" — [Arch BBS 310894](https://bbs.archlinux.org/viewtopic.php?id=310894)
- Audio: `QMediaPlayer` in PySide6 6.11.2 exposes `setLoops`, `Loops` (incl. `Infinite`), `setPlaybackRate`,
  `playbackRate`, `playbackRateChanged` (introspection); the repo already uses `QMediaPlayer.Loops.Infinite`
  (`audio_bar.py` line 117). The Qt multimedia backend printed `qt.multimedia.symbolsresolver: Couldn't resolve
  pipewire-0.3 symbols` in this container, i.e. the FFmpeg backend falls back when PipeWire is absent.

### Inferences
- Non-Python code: QWidgets 0 lines; QGraphicsView 0 lines (but the scene layout/wrapping has to be done by hand,
  there is no flow layout in QGraphicsScene); QListWidget 0 lines but cannot carry the per-tag index payload without a
  custom model; QML ≈ 70–150 lines of QML for tile + drop area + the column/flow layout, plus Python ↔ QML
  signal plumbing. For the Birkenbihl grid the QML route is a rewrite of the whole editor in QML.
- Keyboard alternative: none of the Qt drag APIs offer one; a "select tag with focus, press number key / arrow to
  move to column N" model must be written by hand in Python (QWidgets: focusable `WordTag` + `keyPressEvent`;
  effort small, ~50–100 lines). Same holds for all other candidates below.
- Effort to keep: 0 (exists). Effort for QGraphicsView rewrite ≈ 2–4 days; QML rewrite ≈ 1–2 weeks (new language,
  Python ↔ QML model bridging).
- Flicker: the repo already rebuilds the whole grid after each drop; Qt widgets re-created synchronously under
  `setUpdatesEnabled(False)`/layout rebuild do not flicker visibly, which is consistent with the current app behaviour
  (no flicker complaint found in repo). Not independently sourced.

### Gaps
- Current status of QTBUG-87624 on the official tracker could not be verified (only a test mirror page came back).
- No source found on Qt Quick/QWidget drag-and-drop under Hyprland specifically.
- `doc.qt.io/qt-6/dnd.html` (QWidgets DnD overview) could not be fetched; the qtbase sparse clone did not contain
  `dnd.qdoc` at the path tried.

---

## 2. NiceGUI (make_sortable / SortableJS, raw HTML5 drag events, ui.audio)

### Takeaway
Since 3.11.0 (2026-04-24) NiceGUI ships SortableJS as a built-in: `container.make_sortable(group='shared',
on_end=...)` with cross-container groups; the Python handler gets `item`, `source`, `target` **Element objects** plus
`old_index`/`new_index`, so tags are identified by element, not text, with zero custom JS. The older
`examples/trello_cards` shows the alternative with raw HTML5 `dragstart/dragover.prevent/drop` events and no JS
either. `ui.audio` has `loop` but no `playbackRate` parameter (one line of `run_javascript` needed).

### Cited Findings
- `SortableElement.make_sortable(options=None, *, on_end=None, animation=0.15, handle=None, group=None,
  ghost_class='opacity-50') -> Sortable`: "Make this container sortable via drag-and-drop using SortableJS ...
  :param group: shared group name or config dict for cross-container dragging ... :param on_end: callback invoked when
  a sort operation ends (fires on the source container only, even for cross-container moves) ... *Added in version
  3.11.0*"; caveat: "Setting a custom HTML ID on the container (e.g. via `.props('id="my-list"')`) is not supported
  and will break the internal slot synchronization" — [nicegui/elements/mixins/sortable_element.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/mixins/sortable_element.py) (read from nicegui 3.18.0 wheel)
- Mixed into `ui.column`, `ui.row`, `ui.grid`, `ui.card`, `ui.scroll_area`, `ui.expansion` (grep of the wheel:
  `elements/column.py`, `row.py`, `grid.py`, `scroll_area.py`, `expansion.py` import the mixin).
- Event payload: `SortableEventArguments(item: Element, source: Element, target: Element, old_index: int,
  new_index: int)`; the controller resolves `e.args['item_id']`, `from_id`, `to_id` via `client.elements[...]`
  and by default already executes `e.item.move(target_container=e.target, target_index=e.new_index)` on the Python
  side so the server-side element tree matches the DOM — [nicegui/elements/sortable/sortable.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/sortable/sortable.py),
  [nicegui/events.py `SortableEventArguments`](https://github.com/zauberzeug/nicegui/blob/main/nicegui/events.py)
- The JS side is 61 lines shipped with NiceGUI (`sortable.js`): `Sortable.create(element, {...options, onEnd: evt =>
  {... element.dispatchEvent(new CustomEvent("sortend", {detail: {item_id, from_id, to_id, old_index, new_index}}))}})`
  and it patches NiceGUI's Vue slot `ids` arrays so a cross-container move does not get reverted by the next render;
  it re-binds on `vnodeMounted` — [nicegui/elements/sortable/sortable.js](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/sortable/sortable.js)
- Official demo (website docs): `column1.make_sortable(group='shared'); column2.make_sortable(group='shared')`,
  "Only direct children of the container are sortable; nested containers can be made sortable independently",
  `handle='.handle'` restricts dragging to a handle, `sortable.enable()/disable()` —
  [website/documentation/content/sortable_documentation.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/sortable_documentation.py)
- 3.11.0 release (2026-04-24): "Add make_sortable() to enable drag-and-drop sorting on container elements like
  ui.column, ui.row, ui.card, and many more" — [Zenodo record of the v3.11.0 release](https://zenodo.org/records/19735381)
- Pre-3.11 pattern without JS: `examples/trello_cards/draganddrop.py` (62 lines) uses `card.props('draggable')`,
  `self.on('dragstart', ...)`, `column.on('dragover.prevent', ...)`, `column.on('drop', ...)` and module-level
  `dragged`/`target` variables, then `dragged.move(self, index)` — [examples/trello_cards/draganddrop.py](https://github.com/zauberzeug/nicegui/blob/main/examples/trello_cards/draganddrop.py)
- `Element.move(target_container=None, target_index=-1, *, target_slot=None)` moves an element between
  containers server-side — [nicegui/element.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/element.py)
- `ui.audio(src, *, controls=True, autoplay=False, muted=False, loop=False)` with methods `seek(seconds)`, `play()`,
  `pause()`; the Vue component is `<audio :controls :autoplay :muted :src>` with methods `seek/play/pause` only —
  no playback-rate API — [nicegui/elements/audio.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/audio.py),
  [nicegui/elements/audio.js](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/audio.js)
- Native (desktop window) mode is pywebview: `import webview; window = webview.create_window(**window_kwargs);
  webview.start(**start_args)` — [nicegui/native/native_mode.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/native/native_mode.py);
  on Linux pywebview's default backend is GTK3 + WebKit2GTK 4.1/4.0 (see section 5).
- SortableJS keyboard accessibility: a third-party project states "SortableJS's accessibility gap has been an open,
  frequently requested issue since 2017" — [sorta11y README](https://cdn.jsdelivr.net/npm/sorta11y@0.1.0-alpha.1/README.md)
  (secondary source; the SortableJS issue itself was not retrieved).
- NiceGUI native-mode Linux issues found are about multiprocessing start method (SemLock error on Ubuntu 24.04,
  NiceGUI 2.2.0) and a file dialog, not Wayland — [nicegui#3815](https://github.com/zauberzeug/nicegui/issues/3815),
  [nicegui#1430](https://github.com/zauberzeug/nicegui/issues/1430)

### Inferences
- Mapping to the editor: each source-word column = `ui.column().make_sortable(group='words', on_end=handler)`, the
  pool = another sortable column in the same group, each tag = `ui.chip`/`ui.label` created with the token index
  stored on the Python element (`tag.token_index = i`). Handler: `handler(e)` → `e.item.token_index`,
  `e.target.column_index` → new immutable `GridState` → rebuild. Zero custom JS/HTML; CSS via Tailwind/Quasar
  classes (`.classes('border-2 border-orange-500')`) and `ui.button('✓ Stimmt')` conditionally created.
- Full re-render: `grid.clear()` + rebuild inside the container sends a delta update over the websocket; NiceGUI's
  default `on_end` already moved the element server-side, so a rebuild right after is consistent. Because the drop
  already happened in the DOM before Python sees it, a *rejected* drop (validation failure) needs a rebuild to
  snap back; the ~1 round trip (websocket, localhost) is well below perceptible flicker for 3–25 columns and
  5–40 tags (my estimate; no benchmark found).
- Boundary data: integers (`item_id`, `from_id`, `to_id`, indices) only; text never crosses, so repeated words stay
  distinct.
- Audio speed: `ui.run_javascript(f'getElement({audio.id}).$el.playbackRate = {speed}')` (one line), or subclass
  `ui.audio` with a 10-line Vue component adding `setPlaybackRate(rate) { this.$el.playbackRate = rate }` — the
  HTML `<audio>` element supports `loop` and `playbackRate` natively.
- Keyboard-only path: not provided by SortableJS; implement as keyboard handler on focusable tags (`tabindex`,
  `on('keydown')`) with Python moving the element — same hand-written effort as elsewhere.
- Effort estimate: 2–4 days for the editor (fast feedback loop, hot reload), 0.5 day audio bar; risk is in native
  mode (pywebview/WebKitGTK Wayland bugs, see section 5), not in the drag code. Browser mode has none of those risks.

### Gaps
- No performance measurement of `clear()`+rebuild with ~50 elements found; only inference.
- Did not find a NiceGUI issue about HTML5 drag events under WebKitGTK/Wayland in native mode (search returned none).

---

## 3. Flet (Draggable / DragTarget, Chip rows, flet-audio, FilePicker)

### Takeaway
Flet 1.0.5 has first-class `Draggable`/`DragTarget` controls; the drop handler receives `e.src` (the Draggable
control object, resolved from `src_id`) and both controls carry a free-form `data` field, so a tag can carry its
token index as a Python object with zero Dart/JS. The official "drag_and_drop_ordering_declarative" example is
exactly a cross-container item mover with declarative re-render. `flet-audio` has `playback_rate` and
`ReleaseMode.LOOP`. Flet desktop on Linux is a Flutter/GTK3 app; the embedder in Flet's repo no longer pins X11,
but mainline Flutter's Wayland status remained unconfirmed by the sources reached.

### Cited Findings
- `Draggable(content, group="default", content_when_dragging=None, content_feedback=None, axis=None,
  affinity=None, max_simultaneous_drags=None, on_drag_start=None, on_drag_complete=None)`: "For a DragTarget to
  accept an incoming drop from a Draggable, they must both be in the same group" — [flet/controls/core/draggable.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/draggable.py) (flet 1.0.5 wheel)
- `DragTarget(content, group="default", on_will_accept, on_accept, on_leave, on_move)`; event dataclasses
  `DragWillAcceptEvent(src_id, src: Draggable, accept: bool)`, `DragTargetEvent(src_id, src: Draggable,
  local_position: Offset, global_position: Offset)`, `DragTargetLeaveEvent(src_id, src)`; `src` is resolved in
  `__post_init__` via `self.page.get_control(self.src_id)` — [flet/controls/core/drag_target.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/drag_target.py)
- Every control has `data: Any` ("Arbitrary data of any type", not serialized: `skip_field()`) —
  [flet/controls/base_control.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/base_control.py)
- Official example (imperative): `on_will_accept` sets `e.control.content.border = ft.Border.all(2, BLACK_45 if
  e.accept else RED); e.control.update()`, `on_accept` reads `e.src.content.bgcolor`, `on_leave` clears the border —
  [examples/controls/core/drag_target_and_draggable/drag_and_drop_containers/main.py](https://github.com/flet-dev/flet/blob/main/sdk/python/examples/controls/core/drag_target_and_draggable/drag_and_drop_containers/main.py)
- Official example (declarative, cross-container ordering): `@ft.observable @dataclass class Group: items: list[Item]`,
  `@ft.component def ItemView(item)` renders `ft.Draggable(group="items", data=item, content=ft.DragTarget(group="items",
  data=item, on_will_accept=lambda e: set_is_item_over(e.accept and e.src.data != item), on_accept=on_accept, ...))`
  and `on_accept` does `item.move_item_at(e.src.data, item)` — i.e. identity by Python object, UI re-rendered from
  observable state — [examples/.../drag_and_drop_ordering_declarative/main.py](https://github.com/flet-dev/flet/blob/main/sdk/python/examples/controls/core/drag_target_and_draggable/drag_and_drop_ordering_declarative/main.py)
- CHANGELOG: `DragTargetEvent.x/y/offset` removed (deprecated 0.85.0), use `local_position`/`global_position`
  ([#6693]) — [flet CHANGELOG.md](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md)
- `flet_audio.Audio(ft.Service)`: `src: str | bytes`, `playback_rate: Number = 1.0` ("iOS and macOS have limits
  between 0.5x and 2x"), `release_mode: ReleaseMode = RELEASE`, `ReleaseMode.LOOP` = "Automatically restarts playback
  from the beginning every time it completes, creating a continuous loop", async `play(position=0)`, `pause()`,
  `resume()`, `release()`, `seek()`, `get_duration()`, `get_current_position()`, events `on_position_change`,
  `on_state_change` — [flet-audio 1.0.5 audio.py / types.py](https://github.com/flet-dev/flet-audio);
  the docs mirror says LOOP "keeps buffered data and replays the audio after it finishes" — [flet.dev ReleaseMode](https://flet.dev/docs/services/audio/types/releasemode)
- `FilePicker(Service)` with `async save_file(...)` and `async pick_files(...)` —
  [flet/controls/services/file_picker.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/services/file_picker.py)
- Flet's Linux runner (`client/linux/my_application.cc`) contains no `gdk_set_allowed_backends` call and comments
  "If running on Wayland assume the header bar will work" and "Native Wayland sessions have no window-icon protocol
  GTK 3 can use" — [client/linux/my_application.cc](https://github.com/flet-dev/flet/blob/main/client/linux/my_application.cc)
- Older Flutter templates pinned `gdk_set_allowed_backends("x11")` with a reference to flutter/flutter#57932
  (Wayland support) — [flutter_gallery linux/main.cc (mirror)](https://flutter.googlesource.com/mirrors/flutter/+/a8354ff165eda6174ae423dca3b65c10fa952f4c/dev/integration_tests/flutter_gallery/linux/main.cc);
  Canonical's 2020 statement: GTK embedder "currently only supports X11. Wayland support is in the works" —
  [Ubuntu discourse](https://discourse.ubuntu.com/t/flutter-wayland-support-under-development/17195)
- Flutter's own drag-and-drop (Draggable/DragTarget) is implemented inside the Flutter rendering layer, not via
  the toolkit DnD protocol — the examples above work identically in browser and desktop; a Linux file-drop plugin
  had to fix "[Linux] do not work on Wayland" separately — [desktop_drop changelog](https://www.pub.dev/packages/desktop_drop/versions/0.1.2/changelog)

### Inferences
- Non-Python code: 0. Columns = `ft.Column([header, ft.DragTarget(group='words', content=ft.Container(ft.Column(tags)))])`
  inside a horizontally scrolling `ft.Row(scroll=...)`; tags = `ft.Draggable(group='words', data=token_index,
  content=ft.Chip(...))`. Column states = `Container.border = Border.all(2, ORANGE/RED)` and a conditional
  `ft.Button("✓ Stimmt")`. Flet's "declarative" `@ft.component`/`use_state`/`@ft.observable` (1.0) is the natural fit
  for "re-render the whole grid from an immutable state object".
- Because Flutter draws the drag feedback itself (no OS DnD session), Wayland/Hyprland compositor DnD bugs do not
  apply to intra-window drags; what remains is general Flutter-on-Wayland windowing stability (unverified).
- Audio: `fta.Audio(src=path, playback_rate=0.8, release_mode=ReleaseMode.LOOP)`; set `playback_rate` then `update()`
  to change speed. Loop + rate are both supported on Linux via the audioplayers Flutter plugin (not independently
  verified for Linux rate support — see gaps).
- Keyboard alternative: Flutter's Draggable has no keyboard sensor; implement focus + `on_key_event` on the chip
  (hand-written, same as elsewhere).
- Effort estimate: 3–5 days for the editor including learning the 1.0 declarative API; 0.5–1 day audio + FilePicker.

### Gaps
- Could not confirm whether mainline Flutter's GTK embedder runs natively on Wayland today (flutter/flutter#57932
  not fetched) nor whether `playback_rate` works on the Linux audioplayers backend.
- docs.flet.dev not reachable; API facts are from the 1.0.5 wheel source and repository examples.

---

## 4. Reflex (react-dnd via reflex-enterprise, or wrapping dnd-kit yourself)

### Takeaway
Reflex's only ready-made drag-and-drop is `rxe.dnd.draggable`/`rxe.dnd.drop_target` in the **proprietary**
`reflex-enterprise` package (wraps react-dnd; requires a Reflex Cloud auth token; free tier must show a "Built with
Reflex" badge). It is Python-only API with a `dict` payload reaching state, but drag items must be `@rx.memo`
components. The open-source path is writing a custom React component wrapper around dnd-kit/react-dnd (JS
required). Reflex is a web framework: no desktop shell and no local-file audio without serving the file.

### Cited Findings
- `Draggable(BaseDnDDiv)`: `type: Var[str]` ("Checked by the drop target `accept` prop"), `item: Var[JsObj | ...]`
  ("recommended to simply include an identifier"), `on_end: rx.EventHandler[passthrough_event_spec(dict[str, Any])]`,
  rendered with `opacity=rx.cond(params.is_dragging, 0.5, 1)`; `DropTarget(BaseDnDDiv)`: `accept: Var[str | list[str]]`,
  `on_drop: rx.EventHandler[passthrough_event_spec(dict[str, Any])]`, `on_hover`, `can_drop`; collected params
  `is_over`, `can_drop`, `item` — [reflex_enterprise/components/dnd/dnd.py](https://pypi.org/project/reflex-enterprise/) (0.9.8 wheel, 736 lines)
- Libraries pulled in: `react-dnd` (`useDrag`, `useDrop`, `DndProvider`), `react-dnd-html5-backend`,
  `react-dnd-touch-backend` (same file, lines 31–86).
- Docs: "Functions that define draggables need the `@rx.memo` decorator" (to avoid compilation error); "draggable and
  drop_target will add the rxe.dnd.provider automatically to the app wrapping components tree" —
  [reflex.dev enterprise drag-and-drop](https://reflex.dev/docs/enterprise/drag-and-drop)
- License: `License-Expression: LicenseRef-Proprietary`; EULA: "To use the Software, you must have a valid
  authentication token ('Auth Token') issued by the Reflex Cloud service"; non-paid tiers exporting an app must
  display the "Built with Reflex" badge; no reverse engineering / redistribution —
  [reflex-enterprise LICENSE (wheel)](https://pypi.org/project/reflex-enterprise/)
- dnd-kit (React): `useDraggable` requires a unique `id`, `DragDropProvider` handles interactions and `onDragEnd`;
  keyboard sensor is a default sensor ("activator element ... must be able to receive focus", Space/Enter to pick up,
  arrows move 25px or to the nearest sortable) — [dnd-kit keyboard sensor docs](https://docs.dndkit.com/api-documentation/sensors/keyboard),
  [@dnd-kit/react](https://next.dndkit.com/react)
- No existing open-source Reflex wrapper for dnd-kit was found by search (only the enterprise react-dnd module).

### Inferences
- Non-Python code with reflex-enterprise: 0 lines, but each column is a `drop_target(accept='word', on_drop=State.on_drop)`
  and each tag a memoized `draggable(type='word', item={'index': i})`; `on_drop` receives the `item` dict → state
  update → React re-render (React keyed by element id → no flicker). Identity by index in the `item` dict.
- Without enterprise: a custom `rx.Component` wrapping `@dnd-kit/react` requires writing the React component in
  JS/TSX (≈100–200 lines) plus the Python wrapper (≈50 lines) — the "how much JS" answer is "a real React component".
- Audio: `rx.audio` wraps react-player (`loop`, `playback_rate` props exist in react-player) but local WAV/MP3 must be
  served from `assets/` or an upload dir; desktop packaging is not a Reflex feature.
- Keyboard: dnd-kit gives it for free (if wrapped); react-dnd (enterprise) does not.
- Effort estimate: enterprise route 3–5 days + licensing decision; dnd-kit wrapper route 1–2 weeks and ongoing JS
  maintenance; plus a Node toolchain at dev time.

### Gaps
- `rx.audio` loop/playbackRate props not verified from source (reflex core not downloaded); treat as unconfirmed.
- No pricing figures found for Reflex Pro/Team tiers.

---

## 5. pywebview or Tauri shell with HTML/HTMX/Alpine/Svelte/React frontend

### Takeaway
A webview shell makes the editor a web page: drop handling is in JS (HTML5 DnD or SortableJS or dnd-kit) and only a
small JSON message (`{token_index, target_column}`) crosses to Python via `window.pywebview.api.<method>()`
(promise-based, threads) or `window.state` (6.0 shared state). pywebview on Linux uses GTK3 + WebKit2GTK by default
(Qt WebEngine optional), so HTML5 drag-and-drop inherits WebKitGTK's Wayland DnD bugs (an unresolved July-2026 drop
bug on WebKitGTK 2.52.5/GTK 4.22 Wayland, and a GTK4-era regression where `dragover`/`drop` never reached JS). The
`<audio>` element gives `loop` and `playbackRate` natively.

### Cited Findings
- Python ↔ JS: "exposing an instance of a Python class to the `js_api` parameter of `create_window`. All the
  callable methods of the class will be exposed to the JS domain as `pywebview.api.method_name`"; or
  `window.expose(func)` at runtime; "Exposed function returns a promise that is resolved to its result value ...
  Exposed functions are executed in separate threads and are not thread-safe"; wait for `window.pywebviewready`;
  `window.evaluate_js(code, callback=None)` returns JS values converted to Python types; NEW 6.0 `window.state` /
  `pywebview.state` two-way shared state (top-level keys only) — [docs/guide/interdomain.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/interdomain.md)
- DOM events from Python (5.0+): `element.on('click', handler)`, `DOMEventHandler(on_drag, prevent_default=True, ...)`
  on `dragover`; "pywebview enhances the `drop` event to support full file path information" —
  [docs/guide/dom.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/dom.md)
- Engines: GTK → WebKit2 (min >2.2), QT → QtWebEngine/QtWebKit; `PYWEBVIEW_GUI=qt` or `webview.start(gui='qt')`
  forces Qt on Linux — [docs/guide/web_engine.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/web_engine.md);
  the GTK backend requires `Gtk 3.0`, `WebKit2 4.1` (fallback 4.0) and bridges via
  `register_script_message_handler('jsBridge')` + `script-message-received` and `evaluate_javascript` —
  [webview/platforms/gtk.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/gtk.py) (6.2.1 wheel)
- WebKitGTK Wayland DnD: bug 320301 (filed July 2026) — files dragged from a file manager do not drop onto a standard
  HTML drop zone on WebKitGTK 2.52.5 / GTK 4.22.4 / GNOME Wayland, status NEW — [WebKit bug 320301](https://bugs.webkit.org/show_bug.cgi?id=320301);
  bug 215032 (2020) — after the GTK4-preparation rework "dragstart fired, but dragover and drop did not" reach JS —
  [WebKit bug 215032](https://bugs.webkit.org/show_bug.cgi?id=215032); 2016 crash `gdk_wayland_drag_context_manage_dnd`,
  a 2017 comment says DnD "generally worked on Wayland by then" — [WebKit bug 166431](https://bugs.webkit.org/show_bug.cgi?id=166431)
- Hyprland + GTK: "Any file browser, Nautilus or Thunar works. But once I am in Hyprland simply nothing happens and I
  do not receive the drop event" (GTK4 app) — [GNOME Discourse 32192](https://discourse.gnome.org/t/drag-and-drop-not-getting-event-files-when-using-hyprland-works-on-wayland-x11-any-clue/32192)
- Tauri on Linux uses wry/WebKitGTK; a wry PR fixed "drop events never fired on Wayland" —
  [tauri-apps/wry#1408](https://github.com/tauri-apps/wry/pull/1408). pytauri ("Tauri binding for Python through
  Pyo3", Apache-2.0, pypi v0.8.0 as of 2025-09, repo last pushed 2025-12-13) — [pytauri on depscope](https://depscope.dev/pkg/pypi/pytauri),
  [goodfirstissue listing](https://www.goodfirstissue.org/pytauri/pytauri)
- HTML5 Drag-and-Drop API "is sadly not supported by touch devices" (not a requirement here) — [tobento js-sortable](https://github.com/tobento-ch/js-sortable)
- Chromium (relevant if Qt WebEngine backend is chosen): Wayland/Ozone drag problems reported 2024 (KDE bug 482142,
  Chromium issue 336449364), "worked under Xwayland" — [KDE bug 482142 thread](https://mail.kde.org/pipermail/kfm-devel/2024-May/050686.html),
  [Arch BBS 293731](https://bbs.archlinux.org/viewtopic.php?id=293731)
- Keyboard: dnd-kit ships a keyboard sensor (see section 4); SortableJS has none (see section 2).

### Inferences
- Non-Python code: HTML + CSS for the grid (≈100 lines) plus JS: ~40 lines with raw HTML5 DnD (`draggable`,
  `dataTransfer.setData('text/plain', tokenIndex)`, `drop` → `pywebview.api.move(tokenIndex, columnIndex)`), or
  ~30 lines with SortableJS `group` + `onEnd` → `pywebview.api.move(evt.item.dataset.index, evt.to.dataset.column)`.
  Re-render: Python returns the new grid as JSON/HTML; with HTMX/Alpine the page swaps the grid fragment (flicker-free
  for this size); with Svelte/React a build toolchain joins the project.
- Important nuance: HTML5 DnD *within one window* still goes through the toolkit's DnD session in WebKitGTK (the
  "forbidden cursor"/no-drop class of bugs), so a pointer-event based library (dnd-kit, or SortableJS with
  `forceFallback: true`, which uses mouse events instead of native DnD) avoids compositor DnD entirely — this is the
  standard mitigation; not separately sourced for WebKitGTK.
- Audio: `<audio loop>` + `audio.playbackRate = 0.8`; local file served via pywebview's `http_server=True` or
  `file://`. Save-as: `window.create_file_dialog(SAVE_DIALOG)` (pywebview API; not re-verified here).
- Effort estimate: 1 week (pywebview + HTMX/Alpine, no bundler) to 2 weeks (Svelte/React + dnd-kit + bundler).
  Tauri/pytauri adds Rust toolchain and is a young project (0.8.0).

### Gaps
- No report found specifically on *intra-page* HTML5 drag-and-drop in WebKitGTK on Wayland (the found bugs are
  about file drops from other apps and a 2020 regression); treat the risk as plausible, not proven.
- pytauri 2026 release status unknown (only 2025 data found).

---

## 6. GTK4 + libadwaita (PyGObject): Gtk.DragSource / Gtk.DropTarget, FlowBox/Box columns, CSS, GStreamer; Slint Python

### Takeaway
GTK4 lets a `Gtk.DragSource` transfer an arbitrary GObject/Python value via `Gdk.ContentProvider.new_for_value(...)`
and a `Gtk.DropTarget.new(type, Gdk.DragAction.MOVE)` receives it in the `drop` signal as the object itself (the
official PyGObject tutorial does exactly this with a `FlowBoxChild`), so a tag object carrying its token index
crosses the boundary with no serialization and no non-Python code; states are CSS classes. Audio: GTK4's
`Gtk.MediaFile` has `loop` but speed requires a GStreamer `playbin` seek with `rate`. Slint 1.17 (June 2026) added
`DragArea`/`DropArea` with a Python `DataTransfer.user_data` for in-process payloads, but the UI itself is written in
the `.slint` language.

### Cited Findings
- Official PyGObject GTK4 tutorial example (120 lines, all Python): `drag_controller = Gtk.DragSource();
  drag_controller.connect("prepare", self.on_drag_prepare)`; `on_drag_prepare` returns
  `Gdk.ContentProvider.new_union([Gdk.ContentProvider.new_for_value(self), Gdk.ContentProvider.new_for_value(self.name)])`;
  `on_drag_begin`: `ctrl.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)`; target:
  `drop_controller = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY);
  drop_controller.set_gtypes([SourceFlowBoxChild, Gdk.FileList, str]); drop_controller.connect("drop", self.on_drop)`;
  `def on_drop(self, _ctrl, value, _x, _y): if isinstance(value, SourceFlowBoxChild): ...` —
  [docs/tutorials/gtk4/examples/drag_and_drop.py](https://github.com/GNOME/pygobject/blob/main/docs/tutorials/gtk4/examples/drag_and_drop.py),
  [tutorial text](https://pygobject.gnome.org/tutorials/gtk4/drag-and-drop.html)
- Tutorial: "Generally connecting to `drop` is only needed, this signal will receive the value sended by the
  Gtk.DragSource"; `set_gtypes` list order "establish the priorities"; signals `accept, drop, enter, leave, motion`;
  `drag-end`, `drag-cancel` on the source — same tutorial file `drag-and-drop.rst`.
- GTK reference: "GtkDropTarget provides a simple API, and only provides the data when it has been completely
  transferred"; `Gtk.DropControllerMotion` gives motion events during DnD for hover styling —
  [gtk4 drag-and-drop.md](https://docs.gtk.org/gtk4/drag-and-drop.html); `DropTarget.get_value()` "NULL if the data
  has not been loaded yet" — [property DropTarget.value](https://docs.gtk.org/gtk4/property.DropTarget.value.html)
- Pitfall report: Python drop target whose `drop` never fired because the accepted GType did not match the provided
  value — [natorsc/python-gtk-pygobject issue 5](https://github.com/natorsc/python-gtk-pygobject/issues/5)
- GNOME HIG: every action should be possible with the keyboard; drag-and-drop is called out as needing extra thought,
  no concrete alternative pattern given — [GNOME HIG keyboard](https://developer.gnome.org/hig/guidelines/keyboard.html)
- Wayland/Hyprland: GTK4 app receives no drop event under Hyprland while Nautilus/Thunar work (same Discourse thread as
  section 5); GTK3 DnD broke under sway after an upgrade and was fixed by downgrading — [Arch FS#62401](https://bugs.archlinux.org/task/62401.html);
  Firefox/Wayland drags "silently get stuck" because the compositor never reports the cancelled drag — [mutter #1658](https://gitlab.gnome.org/GNOME/mutter/-/issues/1658)
- GStreamer rate+loop in Python: playback-speed tutorial — seek events with `rate` propagate through the pipeline;
  community `playbin` loopers use `about-to-finish` or segment seeks, with the caveat that "the playback rate resets to
  normal after the first iteration" and re-applying the rate inside the handler hung the player —
  [GStreamer playback-speed tutorial (mirror)](https://git.fasttube.de/FaSTTUBe/GST-Tensordecoder-ov_ep/raw/commit/fade3ed53ea8e00ac999813353514ca2e6956298/markdown/tutorials/basic/playback-speed.md),
  [gst-trick-mode-looping-2.py](https://git.ao2.it/experiments/gstreamer.git/blob/203a0636e9c0690a9e1f4edc6d1b06d9971c03b3:/gst-trick-mode-looping-2.py)
- Slint 1.17 (2026-06-24): "This release brings drag and drop ... A DragArea marks the drag source and a DropArea
  marks the target. The payload is an opaque data-transfer value that you construct and read in your host language";
  `can-drop` returns a `DragAction` during hover, `dropped` on release — [Slint 1.17 blog](https://slint.dev/blog/slint-1.17-released);
  docs: `DragArea { data: Api.make-data(); allow-move: true; drag-finished(action) => {...} }`, `DropArea {
  can-drop(event) => event.proposed-action; dropped(event) => { Api.accept-drop(event.data); return event.proposed-action; } }`,
  with a Python tab using `@slint.callback(global_name="Api", name="string-to-transfer")` returning `DataTransfer()` —
  [docs/guide/development/drag-and-drop.mdx](https://github.com/slint-ui/slint/blob/master/docs/astro/src/content/docs/guide/development/drag-and-drop.mdx)
- Slint Python 1.18.1b1 stubs: `DataTransfer.user_data: object | None` — "Use this when the drag-and-drop ... stays
  inside the current Python application and you want to avoid serializing to plain text or an image";
  `DropEvent(data, position, proposed_action)`; `DragAction.{none,copy,move,link}` — [api/python/slint/slint/slint.pyi](https://github.com/slint-ui/slint/blob/master/api/python/slint/slint/slint.pyi) (slint 1.18.1b1 wheel)

### Inferences
- GTK4 mapping: `WordTag(Gtk.Button or Adw.Bin)` with `token_index`; `DragSource` providing `new_for_value(self)`
  (a GObject) → `DropTarget.new(WordTag, Gdk.DragAction.MOVE)` on each column `Gtk.Box`/`Gtk.FlowBox` and the pool;
  `on_drop(ctrl, value: WordTag, x, y)` → new state → rebuild columns (`box.remove_all()` is available in GTK 4.12+;
  otherwise iterate children). States: `column.add_css_class('flagged')` / `'error'` with a `Gtk.CssProvider` for
  `.flagged { border: 2px solid @orange_3 }`; `Gtk.Button(label="✓ Stimmt")` shown via `set_visible`. Horizontal
  wrap: `Gtk.FlowBox` of columns or `Gtk.ScrolledWindow(hscrollbar_policy=AUTOMATIC)`.
- Non-Python: 0 lines if widgets are built in code; optionally a `.ui`/Blueprint file for layout (not required).
- Audio: `Gtk.MediaFile.new_for_filename()` + `set_loop(True)` covers loop; 0.7–1.0 speed needs a `Gst.ElementFactory.make('playbin')`
  with `seek(rate, Gst.Format.TIME, flags, ...)`, looping via `about-to-finish`/EOS re-seek with rate re-applied
  (≈60–100 lines, fiddly per the sources). Alternative: since Piper/ElevenLabs output is a file and speed is already a
  synthesis parameter in this project (`AudioSettings.speech_speed`), GUI-side rate control could be dropped.
- Wayland: GTK4 is the native toolkit of the Wayland reference stack, but the Hyprland "no drop event" report shows
  compositor-specific failures exist for GTK too; drops inside one window go through the same Wayland DnD protocol.
- Keyboard: GTK4 has no DnD keyboard sensor; implement with `Gtk.EventControllerKey` on focusable tags.
- Slint: the whole grid is written in `.slint` markup (hundreds of lines) plus Python callbacks; for a Python developer
  this is comparable in foreign-code volume to the QML route. Slint Python is still pre-1.0 (`1.18.1b1`).
- Effort estimate GTK4: 1–2 weeks (new toolkit, PyGObject typing is weak for pyright strict, GStreamer plumbing);
  Slint: 2+ weeks.

### Gaps
- GTK4 `Gtk.MediaStream` playback-rate API: could not confirm from source whether a rate property exists (gtk clone
  did not include `gtk/gtkmediastream.c`); assume none.
- PyGObject 3.5x/GTK 4.2x specific DnD bugs on Hyprland not found beyond the Discourse thread.
- Slint `DragArea` keyboard operation and Wayland backend behaviour not documented in the sources read.

---

## 7. Textual (TUI): is drag-and-drop possible or does keyboard "pick up / put down" replace it?

### Takeaway
Textual 8.2.8 has mouse events (`MouseDown`, `MouseMove`, `MouseUp`) and `Widget.capture_mouse()`/`release_mouse()`
but no drag-and-drop abstraction, no draggable widget and no example; the only "drag" in the codebase is scrollbar
dragging and text selection. A word-alignment editor in Textual would be a keyboard-first "select tag → press column
number/arrow → confirm" model, with mouse click-to-select/click-to-place at most. Audio playback would have to be an
external process.

### Cited Findings
- `Widget.capture_mouse(capture=True)`: "When captured, mouse events will go to this widget even when the pointer is
  not directly over the widget"; `release_mouse()` — [textual/widget.py](https://github.com/Textualize/textual/blob/main/src/textual/widget.py) (8.2.8 wheel, lines 4614–4630)
- Events `MouseMove`, `MouseDown`, `MouseUp` (bubble, verbose), `MouseCapture`, `Enter`, `Leave` —
  [textual/events.py](https://github.com/Textualize/textual/blob/main/src/textual/events.py); docs page for mouse
  capture: "when a mouse has been captured, all further mouse events will be sent to the capturing widget" —
  [textual.textualize.io/events/mouse_capture](https://textual.textualize.io/events/mouse_capture/)
- grep of the 8.2.8 wheel for "drag": only `scrollbar.py` ("Message sent when click and dragging handle"),
  `_text_area.py` ("Handles click and drag to expand and contract the selection"), `_input.py`, document selection —
  no `Draggable`, no `Drop`, no DnD API.
- FAQ: "Textual supports text selection for most widgets, via click and drag. Press ctrl+c to copy." (the only
  drag feature documented) — [docs/FAQ.md](https://github.com/Textualize/textual/blob/main/docs/FAQ.md)
- Web searches for Textual drag-and-drop widgets/issues returned no Textual-specific result (two queries).

### Inferences
- A mouse "drag" could be emulated: `on_mouse_down` on a tag → `capture_mouse()` → track `MouseMove` (cell
  coordinates) → on `MouseUp` hit-test the column under the pointer (`screen.get_widget_at(x, y)`) → move. This is
  ~80–150 lines of hand-written Python with no visual drag image beyond changing styles; feasible but non-idiomatic.
- The idiomatic model is keyboard: tags are focusable widgets, `Enter` picks up, `←/→` or digit keys choose the
  column, `Enter` drops, `Esc` cancels; states via CSS classes (`.flagged { border: heavy $warning }`). This is also
  the accessibility pattern every GUI candidate lacks out of the box.
- Audio: no media API in Textual; spawn `pw-play`/`ffplay -loop 0 -af atempo=0.8` or use `python-vlc`/`sounddevice`
  from Python (not sourced; general knowledge).
- Effort estimate: 3–5 days for a keyboard editor; mouse emulation +2 days.

### Gaps
- No Textual community package for drag-and-drop found; absence of evidence, not proof none exists.

---

## Cross-cutting answers to the key questions

### Takeaway
Only the web-based options move drop handling into JS; every native option keeps it in Python. All candidates can
identify tags by index (payload = Python object, GObject, integer id or `{index}` dict). None offers a built-in
keyboard alternative to dragging except dnd-kit (web) — everywhere else it is ~50–150 lines of hand-written focus +
key handling. Wayland DnD risk is highest where the OS drag protocol is used (Qt widgets/QML, GTK4, WebKitGTK-based
shells incl. NiceGUI native mode, pywebview, Tauri) and lowest where the framework draws the drag itself (Flet/Flutter,
and web pages using pointer-event libraries such as dnd-kit or SortableJS `forceFallback`).

### Cited Findings
- Where drop handling runs / what crosses the boundary (from the sources above):
  - PySide6: Python; `QMimeData` text (token index) — repo `word_tag.py`/`grid_column.py`.
  - NiceGUI: JS (SortableJS, shipped 61 lines) → websocket `{item_id, from_id, to_id, old_index, new_index}` → Python
    `SortableEventArguments` with Element objects — [sortable.js](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/sortable/sortable.js).
  - Flet: Flutter client → `src_id` → Python `e.src` (Draggable control) + `e.src.data` (any Python object) —
    [drag_target.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/drag_target.py).
  - Reflex (enterprise): React (react-dnd) → `on_drop(item: dict)` into state — [dnd.py](https://pypi.org/project/reflex-enterprise/).
  - pywebview: JS → `pywebview.api.method(args)` promise → Python thread — [interdomain.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/interdomain.md).
  - GTK4: Python; `Gdk.ContentProvider.new_for_value(python_gobject)` → `drop(ctrl, value, x, y)` —
    [drag_and_drop.py](https://github.com/GNOME/pygobject/blob/main/docs/tutorials/gtk4/examples/drag_and_drop.py).
  - Slint: `.slint` DragArea/DropArea → Python callback with `DataTransfer.user_data` — [slint.pyi](https://github.com/slint-ui/slint/blob/master/api/python/slint/slint/slint.pyi).
  - Textual: Python mouse events only — [widget.py capture_mouse](https://github.com/Textualize/textual/blob/main/src/textual/widget.py).
- Audio loop + rate: Qt `QMediaPlayer.setLoops(Infinite)` + `setPlaybackRate` (introspection, PySide6 6.11.2);
  HTML `<audio loop>` + `playbackRate` (NiceGUI `loop=` param, no rate param — [audio.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/audio.py));
  flet-audio `release_mode=LOOP` + `playback_rate` ([flet-audio](https://github.com/flet-dev/flet-audio));
  GStreamer seek `rate` ([playback-speed tutorial](https://git.fasttube.de/FaSTTUBe/GST-Tensordecoder-ov_ep/raw/commit/fade3ed53ea8e00ac999813353514ca2e6956298/markdown/tutorials/basic/playback-speed.md)).
- Keyboard DnD: dnd-kit keyboard sensor exists ([docs](https://docs.dndkit.com/api-documentation/sensors/keyboard));
  SortableJS none since 2017 ([sorta11y README](https://cdn.jsdelivr.net/npm/sorta11y@0.1.0-alpha.1/README.md));
  Qt `DropArea` docs silent ([DropArea](https://doc.qt.io/qt-6/qml-qtquick-droparea.html)); GNOME HIG flags DnD as a
  keyboard problem without a pattern ([HIG](https://developer.gnome.org/hig/guidelines/keyboard.html)).
- Wayland evidence summary: Qt (QTBUG-87624, -112161, -115757, mutter#2715, QTBUG-109826); GTK (Discourse 32192
  Hyprland, Arch FS#62401 sway, mutter#1658); WebKitGTK (bugs 320301, 215032, 166431); Chromium/Ozone (KDE 482142);
  Flutter intra-window DnD is toolkit-independent (examples identical across platforms), only file drops needed a
  Wayland fix ([desktop_drop changelog](https://www.pub.dev/packages/desktop_drop/versions/0.1.2/changelog)).

### Inferences
- Lines of non-Python code to write (estimates): PySide6 widgets 0; QGraphicsView 0; QML ~100–150 QML; NiceGUI 0
  (optional ~10 JS for playbackRate); Flet 0; Reflex-enterprise 0 (proprietary) / Reflex+dnd-kit ~150–250 JS/TSX;
  pywebview ~150–300 HTML/CSS/JS; GTK4 0 (optional .ui/Blueprint); Slint ~300+ .slint; Textual 0.
- Realistic effort (editor + audio bar, developer new to the framework except Qt): PySide6 keep = 0; NiceGUI 3–5 d;
  Flet 4–6 d; GTK4 1.5–2.5 wk; pywebview+HTMX 1–1.5 wk; Reflex 1–2 wk + licence question; Slint 2–3 wk; Textual 1 wk
  (keyboard-only, external audio).

### Gaps
- No framework-level benchmark of "full re-render after each drop" was found for any candidate; flicker statements
  are inferences from architecture (keyed virtual DOM / Flutter element tree / synchronous widget rebuild).
- Hyprland-specific drag-and-drop status for Qt 6.11, GTK 4.2x and Flutter could not be established from primary
  bug trackers; only scattered user reports exist.
