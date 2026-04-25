# Yamaha Soundbar

A Home Assistant integration for Yamaha soundbars built on the Linkplay A118 module. Connects over the bar's HTTPS API with mutual TLS, polls every 10 seconds, and exposes the soundbar as a media player plus a curated set of switches, selects, numbers, and diagnostic sensors. Setup is UI-only — no YAML.

Verified on YAS-209. Expected to work (unverified) on YAS-109, ATS-1090, ATS-2090, SR-X40A, SR-X50A, and ATS-X500 — all share the same A118 module. Input mode codes are model-specific and may differ; please open an issue if your bar reports something different.

Entities exposed: 1 media player, 8 switches (Clear Voice, 3D Surround, Bass Extension, Voice Control, Power Saving, Auto Power Standby, HDMI Control, Net Standby), 2 selects (Input Source, Sound Program), 2 numbers (Volume, Subwoofer Volume), and 8 sensors (Audio Stream, Wi-Fi Signal, Input Mode, plus 5 firmware diagnostic sensors). Net Standby and the firmware sensors are disabled by default.

To install: add this repository to HACS as a custom integration repository, install Yamaha Soundbar, restart Home Assistant, then add the integration via Settings → Devices & Services → Add Integration → Yamaha Soundbar and enter the bar's IP address.

See the [README](README.md) for the full entity reference, upgrading instructions from v3.x and the legacy `linkplay` integration, known limitations (including the dimmer caveat), troubleshooting, and the security note about the bundled mTLS client certificate.
