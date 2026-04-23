# Yamaha Soundbar — Agent Handoff Notes

You are working on a Home Assistant custom integration. This file is your persistent memory across sessions. Read it at the start of every session, and update it (bottom section first) when you learn something that would have helped you on day one.

Repository location for this working copy:
- Upstream clone: `C:\Users\jfull\source\yamaha-soundbar-osk2`
- Upstream URL: `https://github.com/osk2/yamaha-soundbar`

---

## 1. What this project is

A Home Assistant integration for Yamaha soundbars built on the Linkplay A118 module — YAS-109, YAS-209, ATS-1090/2090, SR-X40A/X50A, ATS-X500, and any future Yamaha bar using the same module.

It exists as a separate integration (rather than riding on Home Assistant's core `linkplay` integration) for exactly one reason: **Yamaha-branded firmware only exposes HTTPS on :443 with mutual TLS**, where stock Linkplay firmware exposes plain HTTP on :49152. The client certificate was extracted from the official Yamaha "Sound Bar Controller" APK by the upstream maintainer (osk2) and documented in [this blog post](https://osk2.medium.com/%E6%88%91%E6%98%AF%E5%A6%82%E4%BD%95%E9%A7%AD%E9%80%B2%E6%88%91%E7%9A%84%E8%81%B2%E9%9C%B8-yas-209-6a05d74a574f). Without that cert, no HTTP call to the device ever succeeds.

Before you do anything significant, verify a few assumptions that shape the whole codebase:

- Does the user have `yamaha_client.crt` and `yamaha_client.key` in `custom_components/yamaha_soundbar/`? If yes, mTLS path works. If no, it fails with `YamahaAuthError` and the integration is useless for Yamaha-branded bars. The older HTTP-on-49152 path is kept as a fallback only for hypothetical unlocked firmware — treat it as best-effort, not primary.
- Is `python-linkplay` actually installed at the version the manifest pins? Run `pip show python-linkplay` before touching `api.py`.

---

## 2. Architecture, at a glance

```
┌──────────────────────────────────────────────────────────────┐
│  Home Assistant                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ...         │
│  │media_player│  │  switch x8 │  │ sensor x4  │              │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘              │
│        │               │               │                     │
│        └───────────────┴───────────────┘                     │
│                        │                                     │
│                 ┌──────▼──────────┐                          │
│                 │ YamahaCoordinator│  ◀── UPnP NOTIFYs push  │
│                 │ (adaptive poll) │      refresh triggers    │
│                 └──────┬──────────┘                          │
│                        │                                     │
│                 ┌──────▼──────────┐                          │
│                 │  YamahaClient   │                          │
│                 │ (python-linkplay│                          │
│                 │  + Yamaha mTLS) │                          │
│                 └──────┬──────────┘                          │
└────────────────────────┼─────────────────────────────────────┘
                         │  HTTPS :443 (mTLS)
                         ▼
                   ┌─────────────┐
                   │ Soundbar    │
                   └─────────────┘
```

Hard rules:
- All network I/O lives in `api.py`. Coordinator and entities never touch aiohttp directly.
- One `DataUpdateCoordinator` per device. Entities are `CoordinatorEntity` subclasses that read `self.coordinator.data`.
- UPnP eventing is an optimisation, not a requirement. If it fails to subscribe, the integration still works via polling.
- Never block the event loop. `asyncio.sleep`, not `time.sleep`. `async with`, not `with open`. No `requests`, ever.

---

## 3. Current state of the v4 rewrite (as of last handoff)

### What exists on disk (target scaffold)
```
custom_components/yamaha_soundbar/
├── __init__.py            # setup/teardown; INCOMPLETE — see bugs
├── manifest.json          # v4.0.0, quality_scale silver, ssdp+zeroconf
├── const.py               # all constants; stable
├── api.py                 # YamahaClient, mTLS endpoint, state parsing
├── coordinator.py         # DataUpdateCoordinator + UPnP + circuit breaker
├── entity.py              # base CoordinatorEntity
├── config_flow.py         # user/zeroconf/ssdp/reconfigure + options; HAS BUG
├── media_player.py        # main entity; grouping is HALF-BAKED
├── switch.py              # 8 switches via EntityDescription pattern
├── number.py              # subwoofer volume
├── select.py              # sound program + dimmer
├── sensor.py              # audio stream + firmware versions
├── binary_sensor.py       # muted + standby
├── button.py              # reboot
├── update.py              # firmware version reporter
├── diagnostics.py         # redacted state dump for bug reports
├── services.py            # snapshot/restore/announce/preset/send_command
└── services.yaml          # service schemas shown in HA UI
```

Status note (2026-04-24): `api.py`, `coordinator.py`, and `entity.py` stubs exist and are instantiated in `media_player.async_setup_entry`, but they are not yet load-bearing for runtime state updates. `media_player.py` still owns most network I/O.

### What's missing entirely (for the v4 scaffold)
- `translations/ja.json` (the user is in Osaka, nice-to-have)
- Tests (`tests/`) — not a single test file exists yet
- `README.md`, `hacs.json` update, `info.md` update
- `.github/workflows/validate.yml` (hassfest + HACS validate + ruff + mypy)
- `.github/ISSUE_TEMPLATE/bug_report.yml` and `feature_request.yml`
- `.github/dependabot.yml`
- `.pre-commit-config.yaml`
- `pyproject.toml` with ruff/mypy config
- `blueprints/automation/yamaha_soundbar/*.yaml` (doorbell-duck, TV-HDMI-autoswitch, night-mode)

---

## 4. Known bugs in the partial scaffold — fix these before adding features

These are real problems from the v4 scaffold target. Do not paper over them; fix them properly.

1. **`config_flow.py` circular import.** The file imports `DEFAULT_USE_MTLS` from `.const` at the bottom of the module to "break a cycle," but `USER_SCHEMA` at the top references it. Load order will `NameError`. Move the import to the top; if a real cycle exists, resolve it by moving `USER_SCHEMA` construction into `async_step_user` so the schema is built lazily.

2. **`__init__.py` never registers services.** The import `from .services import async_register_services` is present but the function is never called. Call it once in `async_setup_entry` after the first entry is set up, guarded by `if not hass.services.has_service(DOMAIN, ...)` (the function already self-guards, so calling every setup is fine).

3. **`__init__.py` has placeholder exception shims.** `ConfigEntryNotReady_safe` / `ConfigEntryAuthFailed_safe` exist only because of avoiding a late import. Replace them with direct imports of `ConfigEntryNotReady` and `ConfigEntryAuthFailed` from `homeassistant.exceptions` at the top of the file.

4. **`media_player.py` grouping is half-baked.** `_find_peer` returns a `_ShimPeer` that isn't really an entity. Multiroom grouping via `async_join_players` / `async_unjoin_player` needs a real implementation against `python-linkplay`'s `LinkPlayController` / `multiroom` API. Verify the actual method names in `python-linkplay` before writing this.

5. **`api.py` subclasses `LinkPlayApiEndpoint`.** Verify the actual base class name, constructor signature, and required methods in the installed `python-linkplay` package. It may be `LinkPlayEndpoint` and may require different kwargs/methods.

6. **`services.py` `ServiceCall` constructor.** Recent HA versions require a `hass` argument and context. Replace fabricated nested `ServiceCall(...)` calls in announce flow with direct helper calls.

7. **`api.py` `_endpoint.request` is private.** If `services.py` reaches into `coord.client._endpoint.request(...)` for send_command, add a public `raw_command(cmd: str)` method on `YamahaClient` and use that.

8. **Volume scaling in `announce` is wrong.** If service code multiplies `0..1` by a hardcoded device scale, replace with `media_player` `async_set_volume_level(0..1)` path so scaling remains centralized.

9. **`coordinator.py` UPnP subscription handle readability.** If `_upnp_unsubscribe` is a lambda wrapping `asyncio.gather`, replace with explicit list storage of unsubscribe callables and iterate in `async_shutdown`.

---

## 5. Coding conventions

- `from __future__ import annotations` at the top of every module.
- Type hints everywhere. `list[str]` not `List[str]`. `dict[str, Any]` not `Dict`.
- Every entity sets `_attr_has_entity_name = True` and uses `_attr_translation_key` for its name. No hardcoded English strings on entities.
- Multi-entity platforms use the frozen-dataclass `EntityDescription` pattern so adding a new entity is a single entry in a tuple.
- Use `DataUpdateCoordinator` + `CoordinatorEntity`. No per-entity polling, ever.
- Use `async_forward_entry_setups` (plural), not the deprecated singular form.
- Config flow errors are translation keys (`cannot_connect`, `invalid_auth`, `unknown`) that must exist in `strings.json` under `config.error`.
- Options flow reloads the entry via `entry.add_update_listener(...)`.
- When catching broad exceptions, log with `exc_info=True` or re-raise. Never silently swallow.
- Log at `DEBUG` for flow-of-control. `INFO` for user-visible state changes. `WARNING` for recoverable problems. `ERROR` only when something is actually broken.
- Device `unique_id` is the Linkplay device UUID (from `getStatusEx`), falling back to MAC, falling back to host. Never use the IP alone.

---

## 6. Commands you will actually run

Set up the dev environment (one-time):
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install homeassistant pytest-homeassistant-custom-component \
            python-linkplay async-upnp-client \
            ruff mypy pre-commit
pre-commit install
```

Validate the integration locally:
```bash
ruff check custom_components/yamaha_soundbar
ruff format --check custom_components/yamaha_soundbar
mypy custom_components/yamaha_soundbar
python3 -m script.hassfest --integration-path custom_components/yamaha_soundbar
python3 -c "import json; json.load(open('hacs.json'))"
pytest tests/ -v
```

---

## 7. Yamaha / Linkplay gotchas

- `YAMAHA_DATA_SET` requires JSON payload verbatim in query string, not URL-encoded.
- There is no true power-off; only NET standby behavior.
- Polling may wake bars from standby on some firmware.
- UPnP NOTIFY is unreliable on A118; treat as a trigger for polling only.
- Accepted sound program names are lowercase Yamaha values (`stereo`, `music`, `sport`, `tv`, `game`, `movie`).
- Sources are model-dependent; device-reported source list is authoritative.
- Lowercase MAC before `CONNECTION_NETWORK_MAC`.
- Recommend DHCP reservation in README.

---

## 8. Roadmap, prioritised

### Slice A — make it load clean
- Fix the 9 bugs in section 4.
- Ensure `strings.json` + `translations/en.json` are complete.
- Add `async_register_services` call in setup flow.
- Run hassfest until passing.

### Slice B — test coverage
- Add `tests/conftest.py`, config-flow/init/coordinator tests.
- Target >= 90% (silver), >= 95% (gold).

### Slice C — project hygiene
- Add CI workflows, issue templates, dependabot, pre-commit, pyproject config.

### Slice D — installability polish
- Add blueprints, Japanese translation, rewritten README.

### Slice E — upstream
- Propose Yamaha profile support in `python-linkplay`.
- If merged, propose Yamaha integration support in HA core linkplay.

---

## 9. When in doubt

- References priority: HA dev docs, HA core source, `python-linkplay` source, osk2 medium post.
- Compare against nearby HA integrations (`linkplay`, `sonos`, `squeezebox`) for patterns.
- If installed `python-linkplay` differs from assumptions in local code, update this integration to match actual package API.

---

## 10. Session log (append, newest at top)

<!--
Format:
### YYYY-MM-DD – brief title
- What you did
- What you learned that contradicts or extends this doc
- What's blocked
-->

### 2026-04-24 – cleanup pass
- Bumped manifest to 4.0.0-alpha.1, quality_scale bronze, added zeroconf/ssdp/codeowners/integration_type/loggers.
- Fixed 6 bugs: config_flow decorator order, error mapping for missing cert, SSL context caching, per-entry data bucket, get_event_loop → get_running_loop, option A wired stub trio.
- **Correction (2026-04-24):** The decorator order applied in this session for `async_get_options_flow` was `@callback` outer / `@staticmethod` inner — that is backwards. The HA-canonical order (per HA dev docs and every core integration) is `@staticmethod` outer, `@callback` directly above the `def`. Reverted to the correct order in a follow-up fix. The previous session prompt had it wrong.
- README: removed obsolete Todo, added Configuration (UI), added Network section, added Security note for client.pem.
- Verified: `python3 -c "import json; print(json.dumps(json.load(open('custom_components/yamaha_soundbar/manifest.json')), indent=2))"` printed manifest with required fields; `python -m compileall custom_components/yamaha_soundbar` passed; `rg "get_event_loop\\(" custom_components/yamaha_soundbar --glob "*.py"` returned no matches; `rg "from \\.api|from \\.coordinator|from \\.entity" custom_components/yamaha_soundbar --glob "*.py"` showed real consumers; `rg -i "todo|config_flow.*todo" README.md` returned no matches; `rg "Configuration \\(UI\\)" README.md` returned one match; `rg "Security note" README.md` returned one match.
- Skipped or could not verify: could not verify Task 2a UI "Configure" button behavior without a running Home Assistant UI session; could not verify Task 2b end-to-end add-flow message text in HA UI; could not verify Task 2c one-minute SSL log frequency in HA runtime; could not verify Task 2d service call behavior against live integration/services in HA Developer Tools.
- Next session: begin actual v4 platform work (start with `switch.py` + extracting one entity off media_player.py — the smallest possible vertical slice that proves the api/coordinator/entity trio is load-bearing).
- Deferred (no drive-by refactor): `media_player.py` still performs direct HTTP I/O and should be migrated to coordinator/client in the next session.

### 2026-04-24 – initial migration pass
- Added initial migration files in upstream clone: `const.py`, `config_flow.py`, `strings.json`, and `translations/en.json`; switched manifest `config_flow` to `true`; replaced `__init__.py` with config-entry setup path and service registration in `async_setup_entry`.
- Added `services.py` with `async_register_services`, added `media_player.async_setup_entry` support, and normalized shared state to `hass.data[DOMAIN]["entities"]` for both config-entry and legacy service paths.
- Added foundation modules `api.py` (`YamahaClient` + `raw_command`), `coordinator.py` (`YamahaCoordinator`), and `entity.py` (`YamahaCoordinatorEntity`) as the bridge toward the v4 architecture.
- Checked environment package state: `pip show python-linkplay` resolves to installed package `python_linkplay` version `0.0.0` on this machine, which is likely not the expected upstream API baseline for planned `api.py` work.
- Learned that this is still an intermediate state between v3 and the intended v4 architecture; while `api.py`/`coordinator.py` now exist, network I/O still primarily lives in `media_player.py` and platform splits (`switch`/`sensor`/`binary_sensor`/`button`/`update`) are not yet implemented in this clone.
- Blocked only by implementation scope now (no missing branch); next step is migrating entity update logic to coordinator/client and then splitting the remaining platforms from monolithic `media_player.py`.

### 2026-04-24 – upstream clone + state reality check
- Cloned upstream repo from `https://github.com/osk2/yamaha-soundbar` into `C:\Users\jfull\source\yamaha-soundbar-osk2` and established this file as persistent handoff memory.
- Learned the current upstream `master` tree is not the described v4 scaffold yet: it does not contain `api.py`, `coordinator.py`, `services.py`, `entity.py`, or other listed modules, so section 3 currently reflects a target scaffold rather than present upstream layout.
- Blocked on starting Slice A exactly as written until the v4 scaffold branch/commit is identified or created in this repo.

### 2026-04-18 – handoff from chat UI
- Scaffold landed with known bugs enumerated in section 4.
- Partial: Python modules + services.yaml + manifest.json. Missing: strings/translations/tests/CI/docs/blueprints.
- Next session: fix the 9 bugs, write strings.json + translations/en.json, get hassfest passing locally. Don't add features until the thing loads cleanly in HA.
