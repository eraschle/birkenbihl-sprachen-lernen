# Web-basierte Python-UI-Frameworks als Desktop-Ersatz für PySide6 (Stand 24. Oktober 2026)

Scope: NiceGUI (incl. native/pywebview mode), Flet, Reflex, Streamlit, pywebview + hand-written HTML/HTMX/Tailwind, Eel, Gradio, pytauri/Tauri-sidecar, Electron+Python, Neutralino, and (briefly) Textual/textual-web. Checked against the seven Birkenbihl requirements (tabbed main window with mode-dependent header; VIEW two-pane resizable layout + read-only interleaved grid; CREATE form with background AI call and progress; EDIT mode with draggable word tags between columns, flagged/empty column states, validation line; audio bar with loop/speed/save-as; settings dialogs; pytest testability, single-app packaging, native dialogs, Wayland/Hyprland).

Method note: version/date facts come from the PyPI JSON API (pypi.org/pypi/<pkg>/json, queried 2026-10-24); star counts from the GitHub repo pages (read 2026-10-24); API facts from the frameworks' source files on GitHub `main`/`master` (read 2026-10-24). The official doc sites nicegui.io, flet.dev/docs.flet.dev, pywebview.flowrl.com, reflex.dev, v2.tauri.app, news.ycombinator.com and bugs.webkit.org were not reachable from the research sandbox; where I cite them it is via search-engine snippets or the documentation source files in the GitHub repos, and this is marked.

## Key question 0: Maturity data (latest version, release date, stars, license, Python 3.13, activity) per framework

### Takeaway
As of 2026-10-24, NiceGUI (3.18.0, MIT, 16.3k stars), Flet (1.0.5, Apache-2.0, 17.4k stars, 1.0.0 shipped 2026-09-14) and pywebview (6.2.1, BSD-3) are actively maintained and declare Python 3.13 support; Reflex (0.10.0, 29k stars) and Streamlit (1.66.1) are active but are web frameworks with no official desktop story; Eel is archived/unmaintained (June 2025); pytauri has had no release since v0.8.0 (Sept 2025); textual-web is a 2024 beta and Textualize the company closed in 2025.

### Cited Findings
- NiceGUI: latest PyPI release 3.18.0 on 2026-10-07; `requires_python >=3.10,<4`; license expression MIT; PyPI classifiers list Python 3.10, 3.11, 3.12, 3.13 and 3.14; 24 releases in the 12 months before 2026-10-24 — [PyPI nicegui](https://pypi.org/project/nicegui/)
- NiceGUI GitHub: 16.3k stars, 964 forks, 16 open issues, MIT; tagline "Create web-based user interfaces with Python. The nice way." — [github.com/zauberzeug/nicegui](https://github.com/zauberzeug/nicegui)
- NiceGUI tech stack: "Python/FastAPI backend, Vue/Quasar frontend, socket.io for communication"; Tailwind CSS auto-complete support — [NiceGUI README](https://github.com/zauberzeug/nicegui/blob/main/README.md)
- NiceGUI's optional `native` extra pins `pywebview>=5.0.1,<7` — [nicegui pyproject.toml](https://github.com/zauberzeug/nicegui/blob/main/pyproject.toml)
- NiceGUI 3.0.0 was released 2025-10-03; 3.12.1 (fixing the Linux native-mode file-dialog hang, see Q4) on 2026-05-21 — [PyPI nicegui](https://pypi.org/project/nicegui/)
- Flet: latest PyPI release 1.0.5 on 2026-10-21; `requires_python >=3.10`; license expression Apache-2.0; 43 releases in the preceding 12 months; 1.0.0 uploaded 2026-09-14; 0.80.0 (the 1.0 beta) on 2025-12-25; 0.86.0 on 2026-07-14; 0.28.3 (last pre-rewrite line) on 2025-05-20. The PyPI metadata carries no "Programming Language :: Python :: 3.x" classifiers — [PyPI flet](https://pypi.org/project/flet/)
- `flet-audio` 1.0.5 released 2026-10-21, Apache-2.0, `requires_python >=3.10` — [PyPI flet-audio](https://pypi.org/project/flet-audio/)
- Flet GitHub: 17.4k stars, 735 forks, Apache-2.0, 263 open issues — [github.com/flet-dev/flet](https://github.com/flet-dev/flet)
- Flet README: "Build cross-platform apps in Python. No frontend experience required", "No Dart, Swift, Kotlin, HTML, or JavaScript required", "150+ built-in controls", Python >= 3.10 badge, `flet build` packaging, pytest integration tests with `flet test` — [Flet README](https://github.com/flet-dev/flet/blob/main/README.md)
- Secondary coverage dates the Flet 1.0 stable announcement to September 15, 2026 and quotes founder Feodor Fitsner calling it ready for production apps — [byteiota](https://byteiota.com/flet-1-0-one-python-codebase-six-platforms/); the 1.0 beta blog said 0.80.0 "is not a drop-in upgrade — it includes breaking changes" — [flet.dev blog (snippet)](https://flet.dev/blog/flet-1-0-beta); 1.0.0 removed all previously deprecated APIs (e.g. `ElevatedButton`→`Button`, `app()`→`run()`) — [flet.dev breaking changes v1.0.0 (snippet)](https://flet.dev/docs/updates/breaking-changes/v1-0-0/removed-deprecated-apis)
- Flet deprecation policy: deprecated APIs are removed after three minor releases — [flet.dev compatibility policy (snippet)](https://flet.dev/docs/release/compatibility-policy)
- Reflex: 0.10.0 on 2026-10-08; `requires_python >=3.11,<4.0`; Apache-2.0; classifiers 3.11–3.15; 90 releases in the preceding 12 months; 0.9.0 on 2026-04-20 — [PyPI reflex](https://pypi.org/project/reflex/)
- Reflex GitHub: 29.0k stars, 1.8k forks, Apache-2.0, 251 issues; the README describes "full-stack web apps in pure Python" and does not mention desktop apps or desktop packaging — [github.com/reflex-dev/reflex](https://github.com/reflex-dev/reflex)
- `reflex-enterprise` 0.9.8 released 2026-10-22, license metadata `LicenseRef-Proprietary` — [PyPI reflex-enterprise](https://pypi.org/project/reflex-enterprise/)
- Streamlit: 1.66.1 on 2026-10-21; `requires_python >=3.11`; Apache-2.0; classifiers 3.11–3.15; 23 releases in 12 months — [PyPI streamlit](https://pypi.org/project/streamlit/)
- pywebview: 6.2.1 on 2026-04-15; BSD 3-Clause; PyPI metadata `requires_python >=3.8` but the installation guide says "pywebview requires Python 3.10 or newer"; classifiers 3.10–3.13; only 2 releases in the 12 months before 2026-10-24 (6.1 on 2025-10-21, 6.2 on 2026-04-13, 6.2.1 on 2026-04-15; 6.0 on 2025-08-08) — [PyPI pywebview](https://pypi.org/project/pywebview/), [installation.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/installation.md)
- pywebview GitHub: 6.1k stars, 643 forks, 11 open issues, 2,472 commits — [github.com/r0x0r/pywebview](https://github.com/r0x0r/pywebview)
- pywebview is a one-maintainer project (Roman Sirokov) that advertises paid consulting and sponsorship — [pywebview README](https://github.com/r0x0r/pywebview/blob/master/README.md)
- Eel: 0.18.2 on 2025-06-22 (0 releases since); MIT; repo archived by owner on Jun 22, 2025, read-only, with a Caution banner "This project is effectively unmaintained"; 6.7k stars — [PyPI eel](https://pypi.org/project/eel/), [github.com/python-eel/Eel](https://github.com/python-eel/Eel)
- Gradio: 6.30.0 on 2026-10-08; Apache-2.0; `requires_python >=3.10`; classifiers 3.10–3.13; 44 releases/yr; 6.0.0 on 2025-11-21 — [PyPI gradio](https://pypi.org/project/gradio/)
- pytauri: 0.8.0 on PyPI 2025-09-01, GitHub release v0.8.0 on 2 Sep (2025); Apache-2.0; `requires-python >=3.9`; no PyPI classifiers; 0 releases in the 12 months before 2026-10-24; `pytauri-wheel` 0.8.0 on 2025-09-02 — [PyPI pytauri](https://pypi.org/project/pytauri/), [pytauri releases](https://github.com/pytauri/pytauri/releases), [pytauri pyproject](https://github.com/pytauri/pytauri/blob/main/python/pytauri/pyproject.toml), [PyPI pytauri-wheel](https://pypi.org/project/pytauri-wheel/)
- pytauri "Used By" lists a single project (Digger Solo) and calls itself "a fairly young project"; it is "not officially endorsed or supported" by the Tauri Program — [pytauri README](https://github.com/pytauri/pytauri/blob/main/README.md)
- Neutralinojs: v6.10.0 released 06 Oct (2026) marked Latest, nightly on 24 Oct — [neutralinojs releases](https://github.com/neutralinojs/neutralinojs/releases); v6.10.0 adds a shell `commandAllowList` — [release notes source](https://github.com/neutralinojs/neutralinojs.github.io/blob/main/docs/release-notes/framework.md)
- Textual: 8.2.8 on 2026-06-30; MIT; `requires_python >=3.9,<4.0`; classifiers 3.10–3.14; 32 releases/yr; 8.0.0 on 2026-02-16 — [PyPI textual](https://pypi.org/project/textual/)
- textual-web: 0.8.0 on 2024-08-30 (no release since); MIT; 1.5k stars; README: "Currently in a beta phase — help us test!" — [PyPI textual-web](https://pypi.org/project/textual-web/), [github.com/Textualize/textual-web](https://github.com/Textualize/textual-web)
- textual-serve: 1.1.3 on 2025-11-01, MIT — [PyPI textual-serve](https://pypi.org/project/textual-serve/)
- Textualize "wrapped up as a company in 2025, but as an Open Source project we are still going strong" (Will McGugan, 2025-12-07) — [textualize.io blog (snippet)](https://www.textualize.io/blog/the-future-of-textual); a community post expects "significantly less velocity" — [waylonwalker.com (snippet)](https://dev.waylonwalker.com/thoughts-633/)
- Packaging tools for reference: PyInstaller 6.22.3 on 2026-09-12 (`requires_python >=3.8,<3.16`, GPLv2+ with exception); Nuitka 4.3.1 on 2026-10-17 (AGPL-3) — [PyPI pyinstaller](https://pypi.org/project/pyinstaller/), [PyPI nuitka](https://pypi.org/project/nuitka/); the incumbent PySide6 is at 6.12.0 (2026-10-08, LGPL-3/GPL) — [PyPI pyside6](https://pypi.org/project/pyside6/)
- Comparison sites put NiceGUI and Flet neck-and-neck in popularity (~15.7k vs ~16k in spring 2026) — [libhunt NiceGUI vs Flet](https://python.libhunt.com/compare-nicegui-vs-flet)

### Inferences
- Of the candidates, only NiceGUI, Flet, pywebview (and the web-only Reflex/Streamlit/Gradio) are both actively released and explicitly Python-3.13-compatible; pytauri's 13-month release gap and Eel's archival are maturity red flags for a new project.
- Flet's 1.0 line is only ~6 weeks old (2026-09-14) and follows a full rewrite with breaking changes; expect API churn in community examples (many still show pre-1.0 `ft.colors`/`ElevatedButton` code).

### Gaps
- Could not retrieve GitHub star counts for pytauri or Neutralinojs (repo pages did not show them in the fetched content); the GitHub API was not reachable from the sandbox.
- Flet's PyPI metadata has no Python-version classifiers, so 3.13 support is inferred from `requires_python >=3.10` and the CHANGELOG mentioning fixes for "Python 3.13.0" (see Q6 findings), not from an explicit classifier.

## Key question 1: Drag & drop of word tags between columns — native or via a small JS library, and how much JavaScript is forced on the developer

### Takeaway
Flet has first-class `Draggable`/`DragTarget` controls with zero JavaScript; NiceGUI can do cross-column drag & drop in pure Python using HTML5 drag events (its official `trello_cards` example) or, for sorting within a column, a custom Vue component with a few dozen lines of JS; pywebview/Eel/Neutralino/Tauri shells require the developer to write the whole DnD in HTML/JS (SortableJS or similar); Reflex's DnD lives in the proprietary `reflex-enterprise` package; Streamlit only has a third-party sortable component.

### Cited Findings
- NiceGUI official example "trello_cards": columns are `ui.column` subclasses that register `self.on('dragover.prevent', ...)`, `self.on('dragleave', ...)`, `self.on('drop', ...)`; cards are `ui.card` subclasses with `.props('draggable')` and `self.on('dragstart', ...)`; the drop handler calls `dragged.move(self, index)` — the whole mechanism is ~60 lines of Python and contains no JavaScript file — [draganddrop.py](https://github.com/zauberzeug/nicegui/blob/main/examples/trello_cards/draganddrop.py), [main.py](https://github.com/zauberzeug/nicegui/blob/main/examples/trello_cards/main.py)
- NiceGUI custom Vue components: the official `custom_vue_component` example consists of a 25-line `counter.js` (Vue single-object component with `template`, `props`, `data`, `methods`, `this.$emit(...)`) plus a 14-line Python wrapper — [counter.js](https://github.com/zauberzeug/nicegui/blob/main/examples/custom_vue_component/counter.js), [counter.py](https://github.com/zauberzeug/nicegui/blob/main/examples/custom_vue_component/counter.py)
- NiceGUI has a `ui.chip` element (text, icon, color, text_color, on_click) suitable as a word tag — [chip.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/chip.py)
- Flet `Draggable`: fields `content`, `group: str = "default"`, `content_when_dragging`, `content_feedback`, `axis`, `affinity`, `max_simultaneous_drags`, `on_drag_start`, `on_drag_complete`; "For a DragTarget to accept an incoming drop from a Draggable, they must both be in the same group" — [draggable.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/draggable.py)
- Flet `DragTarget`: fields `content`, `group`; events `DragWillAcceptEvent` (`src_id`, `src: Draggable`, `accept`), `DragTargetEvent` (`src`, `local_position`, `global_position`), `DragTargetLeaveEvent`; the event's `src` is resolved via `page.get_control(src_id)` — [drag_target.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/drag_target.py)
- Flet cookbook "Drag and Drop" documents the pattern (same group, `on_accept` with `e.src_id`, `on_will_accept`/`on_leave` for highlighting) — [docs.flet.dev cookbook (snippet)](https://docs.flet.dev/cookbook/drag-and-drop)
- Flet performance report (May 2026): "DragTarget() lacks event throttling", 200 modules lag while 1000 run smoothly without it — [flet discussion #6494](https://github.com/flet-dev/flet/discussions/6494)
- pywebview provides two-way JS↔Python: `js_api` class exposed as `pywebview.api.method_name`, `window.expose(func)`, `window.evaluate_js(code, callback)`, shared `window.state`/`pywebview.state` (new in 6.0); "Exposed functions are executed in separate threads" — [interdomain.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/interdomain.md). pywebview itself has no UI widgets; the README describes it as "a lightweight native webview wrapper" — [pywebview README](https://github.com/r0x0r/pywebview/blob/master/README.md)
- Reflex: drag & drop is provided by `rxe.dnd` in `reflex_enterprise`, built on react-dnd; draggables must be wrapped with `@rx.memo` — [reflex.dev enterprise DnD (snippet)](https://reflex.dev/docs/enterprise/drag-and-drop.md); `reflex-enterprise` is published with `LicenseRef-Proprietary` — [PyPI reflex-enterprise](https://pypi.org/project/reflex-enterprise/); wrapping other npm React components requires subclassing `rx.Component` with `library`/`tag` — [reflex.dev wrapping React (snippet)](https://reflex.dev/docs/wrapping-react/overview.md)
- Streamlit: `streamlit-sortables` (138 stars) offers `sort_items(..., multi_containers=True)` to move items between containers; Streamlit core has no DnD control — [github.com/ohtaman/streamlit-sortables](https://github.com/ohtaman/streamlit-sortables)
- Eel: "Eel hosts a local webserver, then lets you annotate functions in Python so that they can be called from Javascript, and vice versa"; the frontend is plain HTML/JS/CSS — [Eel README](https://github.com/python-eel/Eel/blob/master/README.md)
- Neutralinojs: apps are written "using JavaScript, HTML and CSS"; other languages attach via a WebSocket "extensions" IPC — [Neutralino README](https://github.com/neutralinojs/neutralinojs/blob/main/README.md), [extensions overview](https://github.com/neutralinojs/neutralinojs.github.io/blob/main/docs/how-to/extensions-overview.md)
- pytauri: frontend calls Python via `pyInvoke("greet", body)` from `tauri-plugin-pytauri-api` (TypeScript); "almost don't need to write Rust code", but the UI is a web frontend; alternatively it "Can be integrated with nicegui/gradio/FastAPI" (example `nicegui-app`) — [pytauri README](https://github.com/pytauri/pytauri/blob/main/README.md)
- Textual: the official roadmap lists no drag-and-drop; TUI widgets only — [textual roadmap (snippet)](https://textual.textualize.io/roadmap/)

### Inferences
- For the Birkenbihl EDIT grid (tags droppable into any source-word column or an "unassigned" pool), Flet's `Draggable`/`DragTarget` with one shared `group` maps directly: each column and the pool is a `DragTarget`, each word a `Draggable(content=ft.Chip(...))`; validation can run in `on_accept`. Zero JS.
- In NiceGUI the same can be built in pure Python with the `trello_cards` HTML5-DnD pattern (columns = drop targets, `ui.chip` with `.props('draggable')`), with Tailwind classes for the orange/red column states. If smooth reordering inside a column is wanted, a small Vue wrapper around SortableJS (comparable to the 25-line counter example) would be needed — that is the only JS.
- pywebview/Eel/Neutralino/Tauri shells require the developer to own the whole frontend (HTML + Tailwind + SortableJS/HTMX glue), i.e. the most non-Python code of all options.

### Gaps
- No NiceGUI example using SortableJS was found in the repo paths I could fetch (`examples/sortable_list/*` returned 404); whether such an official example exists is unverified.
- Could not open reflex.dev directly to confirm the licence terms/pricing of `reflex-enterprise`; the PyPI `LicenseRef-Proprietary` metadata is the only primary evidence.

## Key question 2: Long-running background work (asyncio, threads, processes) and UI updates from it

### Takeaway
NiceGUI (`await run.io_bound()`, `run.cpu_bound()`, `background_tasks.create()`) and Flet (`page.run_task()`, `page.run_thread()`, async handlers) both have first-class, documented non-blocking patterns that fit a 5–60 s pydantic-ai call; pywebview runs exposed Python functions in separate threads and pushes results back via `evaluate_js`/`state`; the other shells leave this to the developer's own server/IPC code.

### Cited Findings
- NiceGUI `run.io_bound(callback, *args, **kwargs)`: "Run an I/O-bound function in a separate thread", returns `None` when cancelled/shutting down (NiceGUI 4.0 will raise `CancelledError` instead); `run.cpu_bound` uses a `ProcessPoolExecutor`; `run.process_pool_start_method` can be set to `'spawn'`; "NiceGUI 4.0 will default to 'spawn'" — [run.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/run.py)
- NiceGUI docs: "`io_bound` function for running I/O-bound tasks in a separate thread … returns a future that can be awaited" (`await run.io_bound(httpx.get, URL)`); cpu_bound: "By default, the process pool uses the platform's multiprocessing start method — 'fork' on Linux up to Python 3.13, which is unsafe in threaded processes" — [section_action_events.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_action_events.py)
- NiceGUI `background_tasks.create()` runs an async function in the background; exceptions go to `app.on_exception`; passing a `context` (container element or client) routes exceptions to the page's `ui.on_exception` (added 3.18.0) — [section_configuration_deployment.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_configuration_deployment.py)
- Flet `Page.run_task(handler, *args)`: "Run handler coroutine as a new Task in the event loop associated with the current page" (raises `TypeError` if not a coroutine function); `Page.run_thread(handler, *args)`: "Run handler function as a new Thread in the executor associated with the current page" — [page.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/page.py)
- Flet's Audio/FilePicker methods are `async def` (e.g. `await audio.play()`, `await file_picker.save_file(...)`), i.e. the control API is asyncio-native in 1.0 — [audio.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet-audio/src/flet_audio/audio.py), [file_picker.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/services/file_picker.py)
- Flet's older blog described UI event handlers running "in new threads", which the team considered expensive, and asked for first-class async — [flet.dev blog "Flet mobile update" (snippet)](https://flet.dev/blog/flet-mobile-update/)
- Flet user reports (2026): "The biggest issue I've encountered with Flet is performance", mitigated by "reducing refresh frequency and scope" — [discussion #6095](https://github.com/flet-dev/flet/discussions/6095); UI freezes "after hundreds of components refresh at once", suspected Flutter flooding Python with events — [discussion #6494](https://github.com/flet-dev/flet/discussions/6494)
- pywebview: `webview.start(func=None, args=None, …)` runs a Python function after the GUI loop starts; exposed functions "are executed in separate threads and are not thread-safe"; results flow back with `evaluate_js` (sync return, or callback for promises) or `window.state` — [api/README.md](https://github.com/r0x0r/pywebview/blob/master/docs/api/README.md), [interdomain.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/interdomain.md)
- pytauri "Natively support async python (asyncio, trio or anyio)"; commands are `async def` with Pydantic bodies — [pytauri README](https://github.com/pytauri/pytauri/blob/main/README.md)
- Eel README has an "Asynchronous Python" section and uses a Bottle webserver + websockets — [Eel README](https://github.com/python-eel/Eel/blob/master/README.md)

### Inferences
- Since the Birkenbihl `TranslationService` already uses pydantic-ai (asyncio), NiceGUI's `await service.translate(...)` inside an async click handler, or Flet's `page.run_task(...)`, would run the 5–60 s call without blocking; a spinner can be toggled before/after the `await`. Piper TTS (CPU/IO heavy, synchronous) maps to `run.io_bound`/`run.cpu_bound` (NiceGUI) or `page.run_thread` (Flet).
- NiceGUI's warning that the default `fork` start method is unsafe in threaded processes matters for `run.cpu_bound` on Linux with Python 3.13; setting `run.process_pool_start_method = 'spawn'` avoids the known SemLock/spawn mismatch class of bugs (cf. nicegui issues #3815, #1430 in Q4/Q6).

### Gaps
- Flet's dedicated "async apps" cookbook page could not be fetched (path returned 404 in the repo); behaviour is taken from source docstrings only.

## Key question 3: Audio — play a local file with infinite loop and a playback-rate setting

### Takeaway
Flet's `flet-audio` package exposes `playback_rate` and `release_mode=ReleaseMode.LOOP` directly in Python (GStreamer needed on Linux); NiceGUI's `ui.audio` has a `loop` parameter plus `play/pause/seek` but no playback-rate method, so a one-line `ui.run_javascript` setting `playbackRate` on the `<audio>` element is required; any hand-written HTML shell (pywebview/Eel/Neutralino/Tauri) can use `<audio loop>` and `audio.playbackRate` trivially; Streamlit and Gradio have `loop` but no rate control; Textual has nothing.

### Cited Findings
- NiceGUI `ui.audio(src, controls=True, autoplay=False, muted=False, loop=False)` with methods `seek(seconds)`, `play()`, `pause()`; "src: URL or local file path of the audio source"; events via generic `on()` (MDN audio events) — [audio.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/audio.py); the Vue component renders `<audio :controls :autoplay :muted :src>` and implements only `seek/play/pause` (no `playbackRate`) — [audio.js](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/audio.js)
- Flet `Audio` (`flet_audio`, a `ft.Service`): `src` may be "A URL or local asset file path; A base64 string; Raw bytes"; `playback_rate: ft.Number = 1.0` ("iOS and macOS have limits between 0.5x and 2x"); `release_mode: ReleaseMode = ReleaseMode.RELEASE`; `volume`, `balance`; async `play(position)`, `pause()`, `resume()`, `release()`, `seek(position)`, `get_duration()`, `get_current_position()`; supported formats per the underlying `audioplayers` Flutter plugin; "Autoplay works in desktop, mobile apps and Safari browser, but doesn't work in Chrome/Edge" — [audio.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet-audio/src/flet_audio/audio.py)
- Flet `ReleaseMode.LOOP`: "Automatically restarts playback from the beginning every time it completes, creating a continuous loop. All resources are kept buffered." (also `RELEASE`, `STOP`) — [types.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet-audio/src/flet_audio/types.py)
- Flet Linux packaging docs: "GStreamer libraries must be installed if your Flet app uses Audio control"; libmpv for Video; package names differ on Fedora and Arch — [docs.flet.dev/publish/linux (snippet)](https://docs.flet.dev/publish/linux)
- Flet changelog 1.0.5 era: fix for "Audio playback failure without a source" merged Oct 11, 2026 (PR #6956) — [flet issues search](https://github.com/flet-dev/flet/issues?q=wayland%20OR%20hyprland); long-open "`libmpv.so.1` not found despite install" (#2823, open since Mar 2024, 36 comments) — same listing
- Streamlit `st.audio(..., loop=False, autoplay=...)`: `loop` "automatically seek back to the start upon reaching the end" — [docs.streamlit.io st.audio (snippet)](https://docs.streamlit.io/develop/api-reference/media/st.audio)
- Gradio `gr.Audio(autoplay=False, loop=False, playback_position=0, …)`: "loop: If True, the audio will loop when it reaches the end" — [gradio audio.py](https://github.com/gradio-app/gradio/blob/main/gradio/components/audio.py)

### Inferences
- NiceGUI: speed selector 0.7/0.85/1.0 needs something like `ui.run_javascript(f'getElement({audio.id}).$el.playbackRate = {speed}')` (or a 20-line custom Vue element subclassing the audio component); loop is a constructor flag, so toggling loop at runtime likewise requires `audio.props('loop')`/`props(remove='loop')` or JS. Serving the generated WAV requires `app.add_media_files()`/`app.add_static_files()` or passing a local path (the element accepts a local file path).
- Flet covers play-sentence/play-text/stop/loop/speed entirely in Python, but on Arch the user must have GStreamer runtime libraries installed (and the packaged app's users too).
- Streamlit and Gradio have no playback-rate parameter in the fetched/snippeted signatures — a disqualifier for item 5 unless a custom component is written.

### Gaps
- Could not verify whether `ui.audio` in NiceGUI 3.18 gained any `set_playback_rate` helper beyond the fetched `main` source (it has none in `audio.py`/`audio.js` on `main` as of 2026-10-24).
- Flet's `playback_rate` docstring says it "Should ideally be set when creating the constructor"; whether changing it live while playing works on Linux/GStreamer is not documented in the file.

## Key question 4: Native file-save dialogs on Linux/Wayland

### Takeaway
pywebview (and therefore NiceGUI native mode) exposes `create_file_dialog(FileDialog.SAVE, save_filename=…)` backed by a GTK `FileChooserDialog` (or Qt); Flet's `FilePicker.save_file()` returns a path on desktop but requires Zenity on Linux; Tauri's dialog plugin uses GTK dialogs by default with an XDG-portal option (also needing zenity); web-only frameworks (Reflex, Streamlit, Gradio) can only trigger browser downloads.

### Cited Findings
- pywebview API: `window.create_file_dialog(dialog_type=FileDialog.OPEN, directory='', allow_multiple=False, save_filename='', file_types=())` — "Create an open file (`webview.FileDialog.OPEN`), open folder (`FileDialog.FOLDER`) or save file (`webview.FileDialog.SAVE`) dialog" — [api/README.md](https://github.com/r0x0r/pywebview/blob/master/docs/api/README.md)
- pywebview GTK backend implements SAVE via `gtk.FileChooserAction.SAVE`, `dialog.set_current_name(save_filename)`; `create_file_dialog` has a re-entrancy guard — [platforms/gtk.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/gtk.py)
- NiceGUI native mode: `app.native.main_window` "is an async version of `Window` from pywebview" (so `await app.native.main_window.create_file_dialog(...)` is available) — [section_configuration_deployment.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_configuration_deployment.py)
- NiceGUI issue #1430 "Getting a 'connection lost' error when trying to use the file picker in native mode" (opened Aug 2023, closed Jun 10, 2026): root cause was a multiprocessing fork/spawn mismatch in reload mode on Linux ("On CPython 3.11.5 and later this raised a RuntimeError. On earlier versions it failed silently and the put call hung"); fixed in NiceGUI 3.12.1 (PRs #6045/#6065), "reproduced and verified fixed on Ubuntu with GTK"; one user reported the Qt backend showed a blank white window and switched to GTK — [nicegui #1430](https://github.com/zauberzeug/nicegui/issues/1430)
- NiceGUI's `app.native.on('drop', …)` provides OS file paths of files dropped onto the window (`e.args['files']`) — [native_config.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/native/native_config.py), [native_mode.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/native/native_mode.py)
- Flet `FilePicker`: "On Linux, this control requires Zenity when running Flet as a desktop app. It is not required when running Flet in a browser."; `async save_file(dialog_title, file_name, initial_directory, file_type, allowed_extensions, src_bytes) -> Optional[str]`: "On desktop, this method opens a dialog for the user to select a location and file name. If `src_bytes` is provided, those bytes are written to the selected file"; `src_bytes` is mandatory in web/mobile modes — [file_picker.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/services/file_picker.py)
- Flet 1.0.3 fixed `FilePicker.upload()` uploading the wrong file; issue #5829 "FilePicker ignores initial directory in same-named subfolder" closed Oct 8, 2026 — [flet CHANGELOG](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md), [flet issues search](https://github.com/flet-dev/flet/issues?q=wayland%20OR%20hyprland)
- Tauri `tauri-plugin-dialog` (v2): "Native system dialogs for opening and saving files", Linux supported; "By default, this plugin uses gtk to show dialogs, however since v2.5.0 you can switch to using XDG Desktop Portal" (feature `xdg-portal`), which requires `zenity` and a portal backend; requires Rust ≥ 1.90 — [plugins-workspace dialog README](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/dialog/README.md)
- Neutralinojs native API includes "showing dialog boxes" via its JS client — [extensions overview](https://github.com/neutralinojs/neutralinojs.github.io/blob/main/docs/how-to/extensions-overview.md)
- Streamlit's standalone-executable request #1370 is open with label "status:unlikely" (added Jul 19, 2026) — [streamlit #1370](https://github.com/streamlit/streamlit/issues/1370)

### Inferences
- On Omarchy (Arch + Hyprland, GTK-based portal stack), the GTK `FileChooserDialog` from pywebview/NiceGUI-native is the most direct route; Flet's Zenity dependency is an extra runtime requirement to document/install (`zenity` is in Arch's extra repo, but this was not verified in a source).
- In NiceGUI browser mode (not native), the only "save" is a browser download (`ui.download`), which is not a native dialog — the native-mode window is needed to satisfy item 5/7.
- pytauri could use Tauri's dialog plugin only if pytauri exposes a binding for it; the fetched README lists only the notification plugin as an example (see Gaps).

### Gaps
- Could not verify which Tauri plugins have Python bindings in `pytauri-plugins` (the pyproject/README paths I tried returned 404).
- No source found on Flet FilePicker behaviour specifically under Wayland/Hyprland (only the Zenity requirement).

## Key question 5: Wayland/Hyprland support — which renderer each uses and known problems

### Takeaway
On Linux, pywebview/NiceGUI-native, Tauri/pytauri and Neutralino all render through WebKitGTK (pywebview can alternatively use Qt WebEngine), inheriting WebKitGTK's well-documented DMA-BUF/compositing crashes on some driver/compositor combinations (including a Hyprland report) with the `WEBKIT_DISABLE_DMABUF_RENDERER=1` workaround; Flet uses Flutter's GTK3 embedder (runs natively on Wayland, header bar by default) and has open Linux window-sizing/frameless issues plus 2026 Impeller-on-Wayland regressions upstream; Eel uses the installed Chrome/Chromium in app mode.

### Cited Findings
- pywebview renderer table: GTK → "WebKit2 (minimum version >2.2)"; QT → "QtWebEngine / QtWebKit"; selection via `PYWEBVIEW_GUI` env var or `webview.start(gui='qt')` — [web_engine.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/web_engine.md); on Linux the Qt backend is forced automatically when `KDE_FULL_SESSION` is set, otherwise GTK is tried first then Qt — [guilib.py](https://github.com/r0x0r/pywebview/blob/master/webview/guilib.py); Linux install: `pip install pywebview[gtk]` (needs PyGObject, `gir1.2-webkit2-4.1`, "WebKit2 version 2.22 or greater") or `pywebview[qt]`/`[pyside6]` — [installation.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/installation.md)
- NiceGUI native mode: "Native mode requires a browser engine with ES module and import map support (Chrome 89+). On Linux, ensure you have a modern browser engine — e.g. an up-to-date WebKitGTK or Qt-based backend"; the window runs in a separate multiprocessing process; a PR merged 2026-03-28 warns when the engine lacks ES-module support — [section_configuration_deployment.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_configuration_deployment.py), [nicegui PR #5909](https://github.com/zauberzeug/nicegui/issues?q=wayland%20OR%20hyprland%20OR%20webkitgtk)
- NiceGUI Linux native-mode issues: #3815 (Ubuntu 24.04) SemLock fork/spawn RuntimeError on a minimal `ui.run(native=True)` app, workaround `reload=False` — [nicegui #3815](https://github.com/zauberzeug/nicegui/issues/3815); #2419 "Ubuntu22.04: Native Mode failed" and #2406 closed Jan 2024; #5639 "UI displays incorrectly in native mode" closed Jan 2026 — [issues search](https://github.com/zauberzeug/nicegui/issues?q=wayland%20OR%20hyprland%20OR%20webkitgtk); a 2023 maintainer statement said native mode had no automated tests because no good way to test it automatically had been found — [search summary of nicegui discussions](https://github.com/zauberzeug/nicegui/discussions/1714)
- pywebview Wayland-tagged issues (all closed): #1311 "Moving window and selecting screen does not work on Wayland" (closed stale Apr 2024); #1697 "Icon not set when gui=qt under Wayland" (closed stale Oct 2025); #1668 "[GTK] Dragging in frameless mode does not work" (closed stale Oct 2025); #1778 "Mouse Movements with QT causes crash" (opened Feb 1, 2026 on Bazzite/NVIDIA, Python 3.14.2, pywebview 6.1; fixed Feb 2, 2026) — the reporter ran with `GDK_BACKEND=x11` "because the project documentation said pywebview doesn't work well with Wayland" — [pywebview issues "wayland"](https://github.com/r0x0r/pywebview/issues?q=wayland), [pywebview #1778](https://github.com/r0x0r/pywebview/issues/1778)
- pywebview 6.2 changelog: "QT Fix resize problem", "QT Fix mousemove exception", "GTK Fix menu rendering", "GTK Fix background color not being applied correctly" — [docs/CHANGELOG.md](https://github.com/r0x0r/pywebview/blob/master/docs/CHANGELOG.md)
- WebKitGTK on Wayland: Tauri's Linux graphics troubleshooting page says problems appear most often on NVIDIA GPUs; symptoms are blank windows, flicker/crash on resize, console "AcceleratedSurfaceDMABuf was unable to construct a complete framebuffer" or "Gdk … Error 71 (Protocol error) dispatching to Wayland display", attributed to the DMABUF renderer requesting buffer formats the driver doesn't offer; tracked in tauri-apps/tauri#9394 — [v2.tauri.app linux-graphics (snippet)](https://v2.tauri.app/develop/debug/linux-graphics/); common workaround `WEBKIT_DISABLE_DMABUF_RENDERER=1`, alternatives `WEBKIT_DISABLE_COMPOSITING_MODE=1`, `__NV_DISABLE_EXPLICIT_SYNC=1` — [Defguard troubleshooting](https://docs.defguard.net/support-1/troubleshooting-guides/desktop-client/client-crashes-immediately-on-launch-with-error-71-protocol-error-dispatching-to-wayland-display); a May 2025 WebKit bug reports a WebKitGTK Flatpak app crashing immediately on Hyprland with Error 71 — [WebKit bug 293602 (snippet)](https://bugs.webkit.org/show_bug.cgi?id=293602); Yaak (Tauri) users reported blank-screen crashes on Arch + Hyprland with `EGL_BAD_PARAMETER` — [yaak feedback](https://yaak.app/feedback/posts/fix-blank-screen-crash-on-linux-due-to-wayland-nvidia-etc)
- Neutralinojs "uses the existing web browser library in the operating system (Eg: gtk-webkit2 on Linux)" — [Neutralino README](https://github.com/neutralinojs/neutralinojs/blob/main/README.md)
- Flet's Linux runner (`client/linux/my_application.cc`) is a GTK application: "If running on Wayland assume the header bar will work"; it only disables the GTK header bar on X11 when the WM is GNOME Shell; it contains no `gdk_set_allowed_backends("x11")` restriction — [flet my_application.cc](https://github.com/flet-dev/flet/blob/main/client/linux/my_application.cc). Flutter's "[linux] Support Wayland in GTK embedding" issue #57932 was closed as completed on Oct 21, 2020 (PR #66519) — [flutter #57932](https://github.com/flutter/flutter/issues/57932)
- Flet Linux/Wayland issues: #5332 "Wayland" (Ubuntu 24.04, Flet 0.28.3): could not center the window or set its initial size on Wayland, frameless rounded corners showed a thin black frame; closed by reporter Oct 25, 2025 without a stated fix — [flet #5332](https://github.com/flet-dev/flet/issues/5332); #1735 "Window sizing issues on Linux" (open since Aug 2023): with `page.window.title_bar_hidden = True` minimum size is ignored, retested on KDE Plasma 6.5.3 Wayland Dec 2025 (window shrank to ~99×20 px), reproduced by maintainer Feb 2026 — [flet #1735](https://github.com/flet-dev/flet/issues/1735); #6923 "transparent window rendering as a solid black box on Linux" fixed Oct 8, 2026 (1.0.4); #1134 "Failed to read XDG desktop portal settings" open since Mar 2023; #5656 "GDK-CRITICAL GL context assertion on Linux" closed Feb 2026; PR #6916 (Oct 9, 2026) "Flutter upgrade and desktop rendering … enables Impeller rendering on desktop" — [flet issues search](https://github.com/flet-dev/flet/issues?q=wayland%20OR%20hyprland), [flet CHANGELOG](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md)
- Flutter upstream, Oct 2026: "[Linux] Impeller (default since 3.47) causes jank on pointer-driven repaints on AMD radeonsi/Mesa (Wayland); Skia opt-out is smooth" (#194433, closed Oct 20, 2026); "[Linux][Wayland] Stable 3.47 disposes sibling framebuffers in the wrong GL context" (#194840, open); "[Linux] GTK embedder leaks native memory every frame … (Wayland, sibling texture path)" (#192603, open) — [flutter issues search](https://github.com/flutter/flutter/issues?q=is%3Aissue%20wayland%20linux%20embedder%20sort%3Aupdated-desc)
- Eel opens the app in Chrome/Chromium "in App Mode (with the --app cmdline flag)" if installed — [Eel README](https://github.com/python-eel/Eel/blob/master/README.md)
- Hyprland is a wlroots-based dynamic tiling Wayland compositor — [Hyprland wiki](https://wiki.hypr.land/hypr-ecosystem/user/hyprtoolkit/); Omarchy is "a beautiful, fun & agentic Linux distribution by DHH" — [Omarchy README](https://github.com/basecamp/omarchy/blob/master/README.md)
- General Hyprland scaling notes: XWayland apps look blurry on HiDPI unless XWayland scaling is disabled and toolkit vars set — [Hyprland wiki XWayland](https://wiki.hypr.land/0.56.0/Configuring/Advanced-and-Cool/XWayland/)

### Inferences
- No source reports a Hyprland-specific pywebview, NiceGUI or Flet bug; the risk is indirect: WebKitGTK's DMABUF path (pywebview-GTK/NiceGUI-native/Tauri/Neutralino) on NVIDIA+Wayland, and Flutter's fresh Impeller-on-Wayland regressions (Flet ≥1.0.4 bundles Impeller on desktop per PR #6916). On an AMD/Intel Omarchy box the WebKitGTK route is likely fine; a documented env-var fallback exists.
- pywebview-Qt (Qt WebEngine = Chromium) is an alternative Linux backend if WebKitGTK misbehaves, and it would keep the existing PySide6 dependency in play — but it is the backend with the most 2025–2026 Wayland bug reports (#1697, #1778).
- Flet windows under Hyprland will be native Wayland GTK windows (no XWayland blur), but frameless/custom-title-bar designs hit the open #1735 bug; the default GTK header bar is the safe choice.

### Gaps
- The pywebview docs I could fetch (installation, web_engine, usage, debugging, api, CHANGELOG) contain no mention of "Wayland", so the #1778 reporter's claim that "the project documentation said pywebview doesn't work well with Wayland" could not be located.
- No first-hand report of NiceGUI native mode or Flet on Hyprland/Omarchy specifically was found; the WebKit Hyprland crash report (bug 293602) concerns a Flatpak app, not pywebview.
- Could not open bugs.webkit.org or v2.tauri.app directly; those facts rest on search snippets.

## Key question 6: Packaging story (PyInstaller / Nuitka / flet build / flet pack / tauri)

### Takeaway
NiceGUI ships `nicegui-pack` (a PyInstaller wrapper) and documents native-mode packaging pitfalls; Flet has `flet build linux` (Flutter toolchain, bundles Python runtime) and `flet pack` (PyInstaller); pywebview documents PyInstaller and Nuitka for Linux; pytauri bundles python-build-standalone through tauri-cli; Streamlit's only desktop route is third-party (stlite+Electron or community PyInstaller wrappers); Reflex has none.

### Cited Findings
- NiceGUI: "NiceGUI apps can also be bundled into an executable with `nicegui-pack` which is based on PyInstaller" (`nicegui-pack --onefile --name "myapp" main.py`); options `--windowed`, `--onefile` (slower start), `--onedir`, `--clean`, `--noconfirm`; main script should use `ui.run(reload=False, port=native.find_open_port(), ...)`; "In native mode, NiceGUI automatically finds an open port … particularly useful when packaging your app with PyInstaller"; warns that `app.native.window_args` set under `if __name__ == '__main__':` are ignored because the native window runs in a separate process; packaged apps must place `freeze_support()` correctly — [section_configuration_deployment.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_configuration_deployment.py), [scripts/pack.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/scripts/pack.py)
- NiceGUI native-mode storage caveat: multiple packaged instances share `.nicegui` storage and "silently overwrite each other's writes" unless `NICEGUI_STORAGE_PATH` differs — same doc
- NiceGUI discussion #1714 "Native mode, but packaged/frozen" (2023) reported `app.native.window_args` lost after PyInstaller freezing, with a February 2026 follow-up still reporting it — [nicegui discussion #1714](https://github.com/zauberzeug/nicegui/discussions/1714); NiceGUI 3.x warns once when non-picklable `app.native.*` values cannot be forwarded to the window process (issue #6082) — [native_mode.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/native/native_mode.py)
- Flet: `flet build` "supports building for desktop (macOS, Linux, Windows), web" — [flet-cli build.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet-cli/src/flet_cli/commands/build.py); `flet pack` packages "using PyInstaller", arguments after `--` go to PyInstaller — [flet-cli pack.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet-cli/src/flet_cli/commands/pack.py); 1.0.2 updated `serious_python` to 5.0.0 and stopped packaging venvs/`.git` into builds; 1.0.4 "Add app-icon support for Linux bundles" and "Linux taskbar identity and desktop entry" fixes (Sep 2026); "`flet run` crashing with inotify watch limit reached on Linux" fixed 1.0.4 — [flet CHANGELOG](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md), [flet issues search](https://github.com/flet-dev/flet/issues?q=wayland%20OR%20hyprland)
- Flet Linux build prerequisites: GTK 3, GStreamer, mpv/libmpv, libsecret, clang/llvm, lld, cmake, ninja; "package names differ on Fedora and Arch" — [docs.flet.dev/publish/linux (snippet)](https://docs.flet.dev/publish/linux); #4520 "Linux executable not working" (closed Feb 2025, 12 comments) — issues search above
- pywebview freezing: "Windows / Linux: Use pyinstaller … Pyinstaller picks all the dependencies found in pywebview, even if you don't use them" (exclude PyQt if unused); Linux may need `--add-binary /usr/lib/x86_64-linux-gnu/libpython3.x.so:.`; "nuitka can be used for freezing as well" — [freezing.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/freezing.md); "pywebview does not bundle a heavy GUI toolkit or web renderer with it keeping the executable size small" — [README](https://github.com/r0x0r/pywebview/blob/master/README.md)
- pytauri: "pytauri can be distributed as a Python wheel or compiled into a standalone executable (a regular Tauri application)"; bundles python-build-standalone under `src-tauri/pyembed`; "Need Rust compiler, but almost don't need to write Rust code", or `pytauri-wheel` without Rust; "Use Cython to protect your source code" — [build-standalone.md](https://github.com/pytauri/pytauri/blob/main/docs/usage/tutorial/build-standalone.md), [pytauri README](https://github.com/pytauri/pytauri/blob/main/README.md)
- Streamlit: `@stlite/desktop` wraps a Pyodide/WASM port of Streamlit in Electron (electron-builder; README example pins `electron` 34.3.0); its maintainer notes stlite lags Streamlit and "when your app doesn't work on Wasm, stlite can't be the option" — [stlite desktop README](https://github.com/whitphx/stlite/blob/main/packages/desktop/README.md), [discuss.streamlit.io (snippet)](https://discuss.streamlit.io/t/streamlit-wasm-electron-desktop-app/31655); community `streamlit-desktop-app` wraps Streamlit in a native window with PyInstaller support — [github.com/ohtaman/streamlit-desktop-app](https://github.com/ohtaman/streamlit-desktop-app); official request #1370 labelled "status:unlikely" (Jul 2026) — [streamlit #1370](https://github.com/streamlit/streamlit/issues/1370)
- Eel README has a "Building distributable binary with PyInstaller" section — [Eel README](https://github.com/python-eel/Eel/blob/master/README.md)
- Neutralino: `neu build` "(No compilation - takes less than a second)"; Python backend would be a separate extension process started by the Neutralino binary — [Neutralino README](https://github.com/neutralinojs/neutralinojs/blob/main/README.md), [extensions overview](https://github.com/neutralinojs/neutralinojs.github.io/blob/main/docs/how-to/extensions-overview.md)

### Inferences
- NiceGUI-native and pywebview produce small PyInstaller bundles that depend on the system WebKitGTK (fine on Omarchy, where webkit2gtk is a system package) — but the resulting binary is not portable to systems without WebKitGTK/PyGObject.
- Flet's `flet build linux` yields a self-contained app (Flutter engine + Python runtime) at the cost of a Flutter/Dart toolchain plus clang/cmake/ninja on the build machine; `flet pack` is the lighter PyInstaller path.
- Electron+Python and Neutralino+Python always mean two runtimes (Node/Electron or Neutralino binary + a frozen Python sidecar) and a JS frontend — the heaviest packaging and the most non-Python code.

### Gaps
- No primary source fetched for a generic "Electron + Python sidecar" template (HN/npm pages unreachable); only stlite's Electron usage is cited.
- Nuitka with NiceGUI native mode is not documented in the sources read.

## Key question 7: Testability from pytest

### Takeaway
NiceGUI has a pytest plugin with a fast browser-less `user` fixture (async, `asyncio_mode = auto`) and a Selenium `screen` fixture; Flet 1.0 has `flet test` with a `FletTestApp`/`Tester` API (find_by_text/key, tap, drag, enter_text, screenshots) driving a real Flutter client; pywebview/Eel/shells have no pytest tooling, so UI tests would need Playwright/Selenium against the served HTML plus unit tests of the Python API.

### Cited Findings
- NiceGUI: "The NiceGUI package provides a pytest plugin which can be activated via `-p nicegui.testing.plugin`"; `screen` fixture = headless browser (slow), `user` fixture = "fully simulated in Python (fast)"; `main_file` set via `main.py` name, `pytest.ini` option or `@pytest.mark.nicegui_main_file`; requires `asyncio_mode = auto`; example `await user.open('/'); await user.should_see('Click me'); user.find(ui.button).click()` — [section_testing.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_testing.py); the `user` fixture "cuts away the browser and replaces it by a lightweight simulation", the `screen` fixture uses Selenium and "is currently only tested with the Chrome driver" — [nicegui.io/documentation/user (snippet)](https://nicegui.io/documentation/user), [screen (snippet)](https://nicegui.io/documentation/screen)
- Flet: README — "Write integration tests with pytest and run them against your packaged app with `flet test`. Tap buttons, enter text, and verify user flows on desktop and mobile, with screenshot comparisons" — [Flet README](https://github.com/flet-dev/flet/blob/main/README.md); `FletTestApp` "launches the Python Flet app, starts the Flutter test process", supports golden screenshots (`FLET_TEST_GOLDEN`, similarity threshold) — [flet_test_app.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/testing/flet_test_app.py); `Tester` methods: `pump`, `pump_and_settle`, `find_by_text`, `find_by_text_containing`, `find_by_key`, `find_by_tooltip`, `find_by_icon`, `find_by_semantics_identifier`, `take_screenshot`, `tap`, `mouse_click`, `drag(finder, offset)`, `drag_from`, `long_press`, `enter_text`, `mouse_hover`, `teardown` — [tester.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/testing/tester.py); `flet test -k screenshot -- -x --maxfail=1` passes args to pytest (1.0.2) — [flet CHANGELOG](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md)
- pywebview: no testing section in the guide index (`docs/guide/` contains installation, usage, debugging, freezing, interdomain, web_engine…) — [pywebview docs tree](https://github.com/r0x0r/pywebview/tree/master/docs)

### Inferences
- The Birkenbihl project already runs pytest with `asyncio_mode = auto` (per CLAUDE.md), which is exactly what NiceGUI's `user` fixture requires; its service-layer injection (`translator_factory`) would keep the UI tests AI-free.
- Flet's tester drives a real Flutter process, so tests are slower and need the Flet desktop client available in CI; drag-and-drop is testable via `Tester.drag`.
- NiceGUI native-mode specifics (pywebview window, native file dialog) are not covered by either fixture (maintainers acknowledged no automated native-mode tests in 2023; no newer statement found).

### Gaps
- Could not fetch Flet's "integration testing" docs page (repo path 404) to confirm whether `flet test` works headless on Linux CI without a display.

## Key question 8: What developers reported in 2025–2026 about switching from Qt to NiceGUI/Flet (pain points, performance, "feels like a website")

### Takeaway
Primary 2025–2026 reports are thin: Flet users praise the all-Python model but document performance/throttling problems in highly interactive screens (including `DragTarget`), unclear imperative/declarative boundaries and churn through the 1.0 rewrite; NiceGUI discussions concern native-mode plumbing (fork/spawn, frozen `window_args`, blank windows with the wrong backend) rather than look-and-feel; comparison articles consistently frame NiceGUI as "web UI that can be wrapped" and Flet as the more "native-feeling" desktop option.

### Cited Findings
- Flet discussion #6494 (May 13, 2026): "some Flet components lack a throttling mechanism … communication congestion"; `DragTarget()` lacks throttling; `InteractiveViewer` throttles but returns incorrect data; UI freezes after hundreds of components refresh; `@ft.control` has weak callback support; "the unclear integration between imperative and declarative approaches"; "too few declarative code examples"; no maintainer reply — [flet #6494](https://github.com/flet-dev/flet/discussions/6494)
- Flet discussion #6095 (Jan 30, 2026): "The biggest issue I've encountered with Flet is performance"; rich-text/IME and real-time video are hard to build; asks for docs organised by need; "I really like Flet and don't want to learn another framework"; no maintainer reply — [flet #6095](https://github.com/flet-dev/flet/discussions/6095)
- Hacker News "Flet 1.0" thread: one commenter found it "great for a fairly complex app at work" and noted that for "complex, quickly updating control then you can write a Flutter control (in Dart) and wrap it in a Flet control for better performance"; another: "I wish it were further along in development" — [HN item 49746290 (snippet)](https://news.ycombinator.com/item?id=49746290)
- Older HN remark: a Flet developer argued it "might be easier for backend devs as it doesn't assume any web experience at all" — [libhunt comparison (snippet)](https://python.libhunt.com/compare-nicegui-vs-flet)
- pythonguis.com 2026 FAQ: NiceGUI "built on top of Vue.js and Quasar, giving your applications a polished Material Design look"; recommends PyQt6/PySide6, Tkinter or wxPython for desktop-only apps and Flet as versatile multi-platform choice — [pythonguis.com](https://www.pythonguis.com/faq/which-python-gui-library/)
- NiceGUI maintainer (GitHub discussion #1306, "pyqt") was "not aware of" any wrapper mapping PyQt widgets to NiceGUI; suggested embedding NiceGUI in a Qt WebEngine view as a hybrid — [nicegui discussion #1306](https://github.com/zauberzeug/nicegui/discussions/1306)
- NiceGUI native-mode threads: #2737 "Running in native mode results in a blank window" (Windows MSHTML default; fixed by EdgeChromium/Qt) — [nicegui discussion #2737](https://github.com/zauberzeug/nicegui/discussions/2737); #1674 "Native mode window displays but no content" (macOS fork behaviour) — [nicegui discussion #1674](https://github.com/zauberzeug/nicegui/discussions/1674); #5462 (Nov 2025) a user found native mode suits a single window and ran separate pywebview windows pointing at NiceGUI pages for multi-window — [nicegui discussion #5462](https://github.com/zauberzeug/nicegui/discussions/5462)
- A 2026 comparison article and the Talk Python episode on NiceGUI 3.0 describe native mode as a fit for kiosk-style apps or users who expect a desktop feel — [pistack.xyz 2026-08-29](https://www.pistack.xyz/posts/2026-08-29-python-ui-frameworks-streamlit-gradio-nicegui-comparison/), [Talk Python #525](https://talkpython.fm/episodes/show/525/nicegui-goes-3.0)
- Flet mobile-update blog (older): desktop setup was "three cooperating processes" which the team called redundant for desktop — [flet.dev blog (snippet)](https://flet.dev/blog/flet-mobile-update/)

### Inferences
- The recurring Flet complaint is per-event round trips between Flutter and Python under heavy interaction; the Birkenbihl grid (tens of word tags per sentence, not hundreds of live-updating widgets) is well below the reported trouble threshold (200 DragTargets lagging).
- No source literally says NiceGUI "feels like a website"; the closest evidence is that it is browser-first by design and that native mode is a pywebview wrapper around the same web page.

### Gaps
- No Reddit thread or blog post describing an actual PySide6→NiceGUI or PySide6→Flet migration in 2025–2026 was found; the HN "Flet 1.0" thread could not be opened (news.ycombinator.com unreachable), only two comments were obtained via search snippets.

## Key question 9: Capability check against Birkenbihl requirements 1–7 per framework

### Takeaway
Only NiceGUI (in native mode) and Flet plausibly satisfy all seven requirements with little or no JavaScript; a pywebview + hand-written HTML/HTMX/Tailwind frontend satisfies them too but shifts most UI code into HTML/JS; Reflex/Streamlit/Gradio fail on native desktop window + file dialogs + packaging; Eel is unmaintained; pytauri/Electron/Neutralino require a JS frontend; Textual cannot do audio or pointer drag & drop.

### Cited Findings
- Req. 1 (tabs, header, resizable panes): NiceGUI `ui.splitter` "divides the screen space into resizable sections … Based on Quasar's Splitter component", slots `before`, `after`, `separator` — [splitter.py](https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/splitter.py); Flet 1.0.3 fixed `Tabs` `selected_index`/`length` handling and child state-loss when siblings toggle visibility — [flet CHANGELOG](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md)
- Req. 2–4 (grids, DnD, states): see Q1 findings (NiceGUI HTML5-DnD example; Flet Draggable/DragTarget); Tailwind classes available in NiceGUI — [NiceGUI README](https://github.com/zauberzeug/nicegui/blob/main/README.md); Flet "150+ built-in controls … Material and Cupertino" — [Flet README](https://github.com/flet-dev/flet/blob/main/README.md)
- Req. 3 (background AI call + progress): see Q2 findings
- Req. 5 (audio bar): see Q3 findings (Flet `playback_rate` + `ReleaseMode.LOOP`; NiceGUI `loop` + JS for rate; HTML5 `<audio>` in shells)
- Req. 5/7 (native save dialog): see Q4 findings
- Req. 6 (settings dialogs, password field): NiceGUI and Flet both ship dialog/select/input controls (not separately verified beyond the element lists in their READMEs/docs)
- Req. 7 (pytest, packaging, Wayland): see Q5–Q7
- Textual: TUI; `textual-web` serves TUI apps in a browser (beta, 2024) and `textual-serve` 1.1.3 (2025-11-01) — [textual-web README](https://github.com/Textualize/textual-web/blob/main/README.md), [PyPI textual-serve](https://pypi.org/project/textual-serve/)
- Gradio: component library for ML demos with `gr.Audio(loop=…)`, no desktop/native window or dialog API found in the fetched source — [gradio audio.py](https://github.com/gradio-app/gradio/blob/main/gradio/components/audio.py)

### Inferences (capability matrix, ✓ = documented, ~ = possible with extra work, ✗ = not available)
| Framework | 1 Tabs/header/splitter | 2 VIEW grid | 3 CREATE + bg task | 4 EDIT DnD tags | 5 Audio loop+speed | 5/7 Native save dialog | 6 Settings | 7 pytest / packaging / Wayland | Non-Python code required |
|---|---|---|---|---|---|---|---|---|---|
| NiceGUI (native) | ✓ (`ui.tabs`, `ui.splitter`) | ✓ | ✓ (`await`, `run.io_bound`) | ✓ pure-Python HTML5 DnD (~ SortableJS via small Vue comp.) | ~ loop ✓, rate via 1-line JS | ✓ via pywebview `create_file_dialog` (fixed 3.12.1) | ✓ | ✓ user fixture / ✓ nicegui-pack / ✓ WebKitGTK or Qt | ~0–30 lines JS, Tailwind class strings |
| Flet | ✓ (`Tabs`; no built-in splitter found) | ✓ | ✓ (`run_task`/`run_thread`) | ✓ `Draggable`/`DragTarget` | ✓ `flet-audio` (GStreamer) | ✓ `FilePicker.save_file` (needs Zenity) | ✓ | ✓ `flet test` / ✓ `flet build`/`pack` / ✓ GTK3 embedder, open sizing bugs | none (Dart only for custom controls) |
| pywebview + HTML/HTMX/Tailwind | ✓ (hand-written) | ✓ | ✓ (threads + `evaluate_js`) | ✓ SortableJS/HTML5 DnD in JS | ✓ `<audio loop>` + `playbackRate` | ✓ `FileDialog.SAVE` | ✓ | ✗ no fixtures (Playwright) / ✓ PyInstaller, Nuitka / ✓ WebKitGTK or Qt | all HTML/CSS/JS of the UI |
| Reflex | ✓ web | ✓ | ✓ | ~ proprietary `rxe.dnd` or wrap react-dnd | ~ `rx.audio` + JS | ✗ browser download only | ✓ | ✗ no desktop packaging | npm/React wrapping for DnD |
| Streamlit | ~ (`st.tabs`, no splitter) | ~ | ~ rerun model | ~ third-party `streamlit-sortables` | ~ `loop` only, no rate | ✗ | ✓ | ✗ official (#1370 unlikely); stlite+Electron | JS for custom components |
| Gradio | ~ | ~ | ✓ | ✗ | ~ `loop`, no rate | ✗ | ~ | ✗ | — (not plausible) |
| Eel | ✓ hand-written | ✓ | ✓ | ✓ JS | ✓ HTML5 | ~ Python-side tk/other dialog | ✓ | PyInstaller; archived 2025 | all HTML/JS |
| pytauri / Tauri sidecar | ✓ hand-written (or NiceGUI inside) | ✓ | ✓ async commands | ✓ JS | ✓ HTML5 | ✓ dialog plugin (binding unverified) | ✓ | ✗ fixtures / ✓ tauri-cli bundle / WebKitGTK | TS frontend + Rust toolchain; 0 releases in 13 months |
| Electron + Python | ✓ hand-written | ✓ | ✓ IPC | ✓ JS | ✓ HTML5 | ✓ Electron dialog | ✓ | Node toolchain + frozen sidecar | all JS + Node |
| Neutralino + Python ext. | ✓ hand-written | ✓ | ✓ WebSocket ext. | ✓ JS | ✓ HTML5 | ✓ native API | ✓ | `neu build` + sidecar; WebKitGTK | all JS |
| Textual / textual-web | ~ TUI tabs | ~ text grid | ✓ asyncio | ✗ pointer DnD | ✗ | ✗ | ✓ | ✓ pytest `Pilot` (not verified here) | none |

- Flet: no built-in resizable splitter control surfaced in the search ("The search didn't return any Flet-specific results"); a draggable divider via `GestureDetector` updating two containers' `expand` ratios is the usual fallback — [search summary](https://pub.dev/packages/drag_split_panels) (Flutter package, not Flet)

### Gaps
- Flet resizable split pane: absence of a built-in control is inferred from a null search result, not from Flet docs.
- Reflex `rx.audio` capabilities and Textual's `Pilot` test API were not verified in this research (out of fetch reach / not fetched).

## Key question 10: How the code looks — illustrative snippets (draggable chip; background task with spinner)

### Takeaway
Both NiceGUI and Flet express a draggable word tag and a spinner-guarded background AI call in roughly 15–25 lines of plain Python each; the snippets below are illustrative compositions of the documented APIs cited above (not copied from the projects).

### Cited Findings
- NiceGUI drag pattern (official): `self.props('draggable')`, `self.on('dragstart', …)`, column `self.on('dragover.prevent', …)`, `self.on('drop', …)`, `dragged.move(target_container, index)` — [draganddrop.py](https://github.com/zauberzeug/nicegui/blob/main/examples/trello_cards/draganddrop.py)
- NiceGUI background pattern (official): `async def handle_click(): result = await run.io_bound(fn, …); ui.notify(...)`; `ui.button('Download', on_click=handle_click)` — [section_action_events.py](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_action_events.py)
- Flet drag pattern (official): `Draggable(group=…, content=…, content_feedback=…)`, `DragTarget(group=…, content=…, on_accept=…, on_will_accept=…, on_leave=…)`, `e.src` resolves the source control — [draggable.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/draggable.py), [drag_target.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/core/drag_target.py)
- Flet background pattern (official): `page.run_task(coro, …)` / `page.run_thread(fn, …)` — [page.py](https://github.com/flet-dev/flet/blob/main/sdk/python/packages/flet/src/flet/controls/page.py)
- pywebview bridge (official): `webview.create_window(..., js_api=Api())`, `window.expose(func)`, `pywebview.api.func()` returns a promise, `window.evaluate_js(...)` — [interdomain.md](https://github.com/r0x0r/pywebview/blob/master/docs/guide/interdomain.md)

### Inferences (illustrative code composed from the cited APIs)

NiceGUI — draggable word chip dropped into a source-word column (pure Python, HTML5 DnD; Tailwind classes for flagged/empty state):
```python
from nicegui import ui

dragged: ui.chip | None = None

class WordColumn(ui.column):
    def __init__(self, source_word: str, on_drop) -> None:
        super().__init__()
        self.classes('min-w-24 p-2 rounded border-2 border-red-400')   # empty = red
        ui.label(source_word).classes('font-bold')
        self.on('dragover.prevent', lambda: self.classes(add='bg-blue-100'))
        self.on('dragleave', lambda: self.classes(remove='bg-blue-100'))
        self.on('drop', lambda: self._accept(on_drop))

    def _accept(self, on_drop) -> None:
        global dragged
        if dragged is not None:
            dragged.move(self)                 # re-parent the chip
            on_drop(dragged.text, self)        # service.update_sentence_alignment(...)
            dragged = None

def word_chip(text: str) -> ui.chip:
    chip = ui.chip(text).props('draggable').classes('cursor-move')
    chip.on('dragstart', lambda: globals().__setitem__('dragged', chip))
    return chip
```

NiceGUI — background AI call with spinner (does not block the event loop; pydantic-ai call is awaited directly, Piper via `run.io_bound`):
```python
from nicegui import run, ui

async def create_translation(service, request) -> None:
    spinner.set_visibility(True); create_button.disable()
    try:
        translation = await service.translate(request)            # 5–60 s, async pydantic-ai
        audio_path = await run.io_bound(audio_service.speak, translation.sentences[0])  # sync Piper in a thread
        ui.notify('Fertig')
    finally:
        spinner.set_visibility(False); create_button.enable()

spinner = ui.spinner(size='lg'); spinner.set_visibility(False)
create_button = ui.button('Erstellen', on_click=lambda: create_translation(service, request))
```

Flet — draggable word chip and drop columns (same `group`), with column state colours:
```python
import flet as ft

def word_chip(text: str) -> ft.Draggable:
    return ft.Draggable(group="words", content=ft.Chip(label=ft.Text(text)),
                        content_feedback=ft.Chip(label=ft.Text(text), bgcolor=ft.Colors.BLUE_100))

def word_column(source_word: str, on_moved) -> ft.DragTarget:
    col = ft.Column([ft.Text(source_word, weight=ft.FontWeight.BOLD)])
    box = ft.Container(content=col, padding=8, border=ft.Border.all(2, ft.Colors.RED_400))  # empty = red

    def accept(e: ft.DragTargetEvent) -> None:
        chip = e.src                       # the Draggable that was dropped
        chip.parent.controls.remove(chip)  # leave old column / pool
        col.controls.append(chip)
        box.border = ft.Border.all(2, ft.Colors.ORANGE_400)   # flagged = orange until confirmed
        on_moved(chip, source_word); e.page.update()

    return ft.DragTarget(group="words", content=box, on_accept=accept,
                         on_will_accept=lambda e: setattr(box, "bgcolor", ft.Colors.BLUE_50),
                         on_leave=lambda e: setattr(box, "bgcolor", None))
```

Flet — background AI call with `ProgressRing`:
```python
async def on_create(e: ft.Event[ft.Button]) -> None:
    progress.visible = True; e.control.disabled = True; e.page.update()
    try:
        translation = await service.translate(request)   # async pydantic-ai
        e.page.run_thread(audio_service.speak, translation.sentences[0])  # sync Piper off the loop
    finally:
        progress.visible = False; e.control.disabled = False; e.page.update()

progress = ft.ProgressRing(visible=False)
page.add(ft.Button("Erstellen", on_click=on_create), progress)
```

pywebview — the Python side is only a bridge; the chip, the SortableJS wiring and the spinner live in HTML/JS:
```python
import webview

class Api:
    def translate(self, title, text, src, tgt, provider):      # called as pywebview.api.translate(...) → Promise
        return service.translate(...).model_dump()               # runs in a pywebview worker thread

    def save_audio(self, wav_path):
        target = window.create_file_dialog(webview.FileDialog.SAVE, save_filename='satz.wav')
        ...

window = webview.create_window('Birkenbihl', 'index.html', js_api=Api())
webview.start(gui='gtk')   # or 'qt'; PYWEBVIEW_GUI env var also works
```
(`index.html` would contain Tailwind markup, `<audio loop>` with `audio.playbackRate = 0.85`, and `new Sortable(column, {group: 'words', onEnd: ...})` — none of which is Python.)

### Gaps
- These snippets were not executed; exact attribute names in Flet 1.0.5 (e.g. `ft.Border.all`, `ft.Colors`) follow the 1.0 breaking-changes guide but could not be run in the sandbox.
- NiceGUI's `ui.chip` has no documented `draggable` parameter; using `.props('draggable')` follows the `ui.card` pattern of the official example.
