# Yamaha Soundbar

This component allows you to control Yamaha soundbar.

Tested on Yamaha YAS-109 & YAS-209, any Yamaha soundbar based on Linkplay A118 should be supported as well. (These include ATS-1090, ATS-2090, SR-X40A, SR-X50A, ATS-X500, Please make an issue in Github if you have a different model and it's not working, or even better if it is, so we can update the compatibility list.)

## Installation

#### 1. Install custom component
 - Using HACS
 - Install manually: copy all files in `custom_components/yamha_soundbar` to your `<config directory>/custom_components/yamaha_soundbar/` directory.

#### 2. Restart Home-Assistant.
#### 3. Add the configuration to your configuration.yaml.
#### 4. Restart Home-Assistant again.

### Configuration

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
