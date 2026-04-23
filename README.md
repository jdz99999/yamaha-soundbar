[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Yamaha Soundbar

This component allows you to control Yamaha soundbar.

Tested on Yamaha YAS-109 & YAS-209, any Yamaha soundbar based on Linkplay A118 should be supported as well. (These include ATS-1090, ATS-2090, SR-X40A, SR-X50A, ATS-X500, Please make an issue in Github if you have a different model and it's not working, or even better if it is, so we can update the compatibility list.)

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=osk2&repository=yamaha-soundbar&category=integration)

#### 1. Install custom component
 - Using HACS
 - Install manually: copy all files in `custom_components/yamaha_soundbar` to your `<config directory>/custom_components/yamaha_soundbar/` directory.

#### 2. Restart Home-Assistant.
#### 3. Add the configuration to your configuration.yaml.
#### 4. Restart Home-Assistant again.

## Upgrading from version 3.1.9 and earlier.

If you are upgrading from version 3.1.9 or earlier:
#### 1. You will need to remove the old integration which is /custom_components/linkplay/ and then install the new integration.
#### 2. You will need to update the platform configuration to `yamaha_soundbar` from `linkplay` in your `configuration.yaml` file.

## Configuration (UI)

The recommended setup is via the Home Assistant UI:

1. Settings → Devices & Services → Add Integration
2. Search for "Yamaha Soundbar"
3. Enter the IP address of your soundbar
4. The device name is auto-detected; override only if you want a different label

Source renaming, volume step, and other tunables are under the integration's "Configure" button after setup.

## Configuration (YAML, legacy)

```yaml
# Example configuration.yaml entry
media_player:
  - platform: yamaha_soundbar
    host: 192.168.1.11
    name: My Sound Bar # To name your sources (optional)
    sources:
      {
        'HDMI': 'TV', 
        'optical': 'Plexamp', 
        'bluetooth': 'Bluetooth',
      }
```

### Sound settings service

Use `yamaha_soundbar.sound_settings` to set one or more sound options in a single call.

Available fields:
- `sound_program` (string)
- `subwoofer_volume` (integer, -4 to 4)
- `surround` (boolean)
- `clear_voice` (boolean)
- `bass_extension` (boolean)
- `mute` (boolean)
- `power_saving` (boolean)

Example:

```yaml
action: yamaha_soundbar.sound_settings
data:
  entity_id: media_player.my_sound_bar
  sound_program: movie
  clear_voice: true
  surround: true
```

Current sound settings are exposed as media player attributes (`clear_voice`, `surround`, `bass_extension`, `subwoofer_volume`, `power_saving`, `sound_program`) for template entities and automations.

## Network

Reserve a DHCP lease for your soundbar in your router. The integration uses the device's UUID as its unique ID, so a changed IP won't *break* the integration permanently — but it will go unavailable until Home Assistant rediscovers it. A static lease avoids that gap entirely.

## Security note

`custom_components/yamaha_soundbar/client.pem` is the Yamaha mTLS client certificate material used by this integration to authenticate requests to the soundbar. The original extraction/source is documented by the upstream maintainer in the osk2 post: <https://osk2.medium.com/%E6%88%91%E6%98%AF%E5%A6%82%E4%BD%95%E9%A7%AD%E9%80%B2%E6%88%91%E7%9A%84%E8%81%B2%E9%9C%B8-yas-209-6a05d74a574f>.

Its control scope matches the official Yamaha Sound Bar Controller app behavior on the same LAN; anyone who can reach the soundbar and authenticate with the app-equivalent client material can issue control commands.

## License

This project is licensed under MIT license. See [LICENSE](LICENSE) file for details.
