[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Yamaha Soundbar

A Home Assistant integration for Yamaha soundbars built on the Linkplay A118 module. Connects over the bar's HTTPS API with mutual TLS, polls device state every 10 seconds via a single shared coordinator, and exposes the soundbar as a media player plus a set of switches, selects, numbers, and diagnostic sensors. Setup is UI-only — no YAML.

## Compatibility

| Model | Status |
| --- | --- |
| YAS-209 | Fully verified on hardware |
| YAS-109 | Same A118 module as YAS-209; expected to work, input mode codes may differ |
| ATS-1090 / ATS-2090 | Same module, expected to work, unverified |
| SR-X40A / SR-X50A | Same module, expected to work, unverified |
| ATS-X500 | Same module, expected to work, unverified |

If your model isn't listed, it almost certainly uses the same A118 module — please open an issue with the output of `getPlayerStatus` from your bar so the compatibility list and input-mode mappings can be extended.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jdz99999&repository=yamaha-soundbar&category=integration)

### HACS (preferred)

1. In HACS → Integrations, add this repository as a custom repository (category: Integration).
2. Install "Yamaha Soundbar".
3. Restart Home Assistant.

### Manual

Copy the contents of `custom_components/yamaha_soundbar/` into `<config_dir>/custom_components/yamaha_soundbar/` and restart Home Assistant.

## Configuration (UI)

1. Settings → Devices & Services → **Add Integration**
2. Search for **Yamaha Soundbar**
3. Enter the IP address of your soundbar
4. The device name is auto-detected from the bar; override only if you want a different label

Source renaming, volume step, and other tunables live behind the integration's **Configure** button after setup.

## Entities

### Media player

One `media_player` entity handles playback (play/pause/skip), the volume slider, source selection, mute, and media metadata. This is the v3-era entity; its internals have not yet been refactored onto the new client/coordinator path — that's a planned future change.

### Switches

| Entity | Default | Notes |
| --- | --- | --- |
| Clear Voice | enabled | |
| 3D Surround | enabled | |
| Bass Extension | enabled | |
| Voice Control | enabled | |
| Power Saving | enabled | |
| Auto Power Standby | enabled | |
| HDMI Control | enabled | |
| Net Standby | **disabled** | Toggling off can soft-brick the integration's network access. Enable only if you understand what NET standby does on Linkplay devices. |

### Selects

- **Input Source** — `Bluetooth` / `TV` / `HDMI` / `Net`. Mode codes verified on YAS-209 (41 / 43 / 49 / 31); other models may report different integers for the same physical inputs.
- **Sound Program** — `movie` / `music` / `sports` / `tv program` / `game` / `stereo`.

### Numbers

- **Subwoofer Volume** — integer, range −4 to +4.
- **Volume** — integer, range 0 to 100. This is the Linkplay-side volume scale, distinct from the `Master volume` field that `YAMAHA_DATA_GET` reports.

### Sensors

| Entity | Category | Default | Notes |
| --- | --- | --- | --- |
| Audio Stream | normal | enabled | Reports the current audio format on HDMI/optical inputs (`PCM`, `Dolby Digital`, `DTS`, `OFF`). |
| Wi-Fi Signal | diagnostic | enabled | RSSI in dBm. |
| Input Mode | normal | enabled | ENUM sensor exposing the same data as the Input Source select. Cleaner to bind state-change automation triggers to. |
| System Firmware | diagnostic | **disabled** | |
| A118 Firmware | diagnostic | **disabled** | |
| MCU Firmware | diagnostic | **disabled** | |
| DSP Firmware | diagnostic | **disabled** | |
| HDMI Firmware | diagnostic | **disabled** | |

The five firmware sensors are disabled by default to avoid registry clutter on a stock install. Enable per-sensor under the device page if you want them dashboarded or exposed to alerts.

## Upgrading

### From v3.x to v4.x

v4 removes the YAML platform setup. To upgrade:

1. Remove any YAML configuration block referring to this integration. Example block to **delete**:

   ```yaml
   media_player:
     - platform: yamaha_soundbar
       host: 192.168.1.11
       name: My Sound Bar
       sources:
         { 'HDMI': 'TV', 'optical': 'Plexamp', 'bluetooth': 'Bluetooth' }
   ```

2. Restart Home Assistant.
3. Add the integration through the UI (Settings → Devices & Services → Add Integration → Yamaha Soundbar).
4. Existing entity unique IDs are derived from the device UUID, so the entities and their automations / dashboards re-create cleanly under the new config-entry-based instance.

### From the very old `linkplay` integration

If you're upgrading from the legacy `linkplay` custom component (predecessor of this integration):

1. Remove `custom_components/linkplay/` from your config directory.
2. Install `yamaha_soundbar` (see Installation above).
3. In any old `configuration.yaml` block, change `platform: linkplay` to `platform: yamaha_soundbar`, then follow the v3 → v4 steps above to drop YAML entirely.

## Known limitations

- **Dimmer (front display brightness) doesn't work on YAS-209.** The bar accepts the set command and returns `OK`, but the actual display brightness doesn't change. Verified across multiple key/value variants. Not exposed as an entity until a working command is found.
- **Sound program `sport` (singular) silently fails on this firmware.** The correct value is `sports` (plural). The select uses the correct value; this is only a concern if you're sending raw service calls.
- **Audio Stream usually reads `OFF` on TV setups.** Most TVs don't enable Dolby/DTS passthrough by default, so the bar correctly reports no encoded stream. Enable passthrough in your TV's audio output settings if you want to see other values.
- **Input mode codes are model-specific.** The `41 / 43 / 49 / 31` mapping was verified on YAS-209. Other Linkplay-A118 models may report different integers for the same physical inputs. If your bar's input mode sensor doesn't match reality, please open an issue with the output of `getPlayerStatus` from your bar.

## Network

Reserve a DHCP lease for your soundbar in your router. The integration uses the device's UUID as its unique ID, so a changed IP won't *break* the integration permanently — but it will go unavailable until Home Assistant rediscovers it. A static lease avoids that gap entirely.

## Security note

`custom_components/yamaha_soundbar/client.pem` is the Yamaha mTLS client certificate material used by this integration to authenticate requests to the soundbar. The original extraction/source is documented by the upstream maintainer in the osk2 post: <https://osk2.medium.com/%E6%88%91%E6%98%AF%E5%A6%82%E4%BD%95%E9%A7%AD%E9%80%B2%E6%88%91%E7%9A%84%E8%81%B2%E9%9C%B8-yas-209-6a05d74a574f>.

Its control scope matches the official Yamaha Sound Bar Controller app behavior on the same LAN; anyone who can reach the soundbar and authenticate with the app-equivalent client material can issue control commands.

## Troubleshooting

To enable debug logging, add this block to `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.yamaha_soundbar: debug
```

Logs land in `home-assistant.log` under your config directory, or live under Settings → System → Logs.

To file a bug, open an issue at <https://github.com/jdz99999/yamaha-soundbar/issues> and include the diagnostics dump from the integration page (Settings → Devices & Services → Yamaha Soundbar → three-dot menu → **Download diagnostics**). The dump captures device state, firmware versions, and recent error history with PII redacted.

## Contributing

This project is a fork of [osk2/yamaha-soundbar](https://github.com/osk2/yamaha-soundbar) with substantial v4 additions: the EntityDescription-driven switch / select / number / sensor platforms, the shared `_yamaha_codec` payload helper, the coordinator-driven polling, and the test scaffolding. Pull requests welcome — for non-trivial changes, please open an issue first to align on direction.

## License

This project is licensed under MIT license. See [LICENSE](LICENSE) file for details.
