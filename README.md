[![](https://img.shields.io/github/release/sermayoral/ha-samsungtv-encrypted/all.svg?style=for-the-badge)](https://github.com/sermayoral/ha-samsungtv-encrypted/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/license/sermayoral/ha-samsungtv-encrypted?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40sermayoral-red?style=for-the-badge)](https://github.com/sermayoral)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

# HomeAssistant - SamsungTV Encrypted SSDP Component

This is a custom component to allow control of Encrypted SamsungTV devices in [HomeAssistant](https://home-assistant.io). 
This should work on H and J 2014/2015 models (according to [PySmartCrypto](https://github.com/eclair4151/SmartCrypto)
specs). Is a modified version of the built-in [samsungtv](https://www.home-assistant.io/integrations/samsungtv/), with
some extra features.

# Installation (There are two methods, with HACS or manual)

### 1. Easy Mode

We support [HACS](https://hacs.netlify.com/). Go to "STORE", search "SamsungTV Encrypted SSDP" and install.

### 2. Manual

Install it as you would do with any homeassistant custom component:

1. Download `custom_components` folder.
2. Copy the `samsungtv_encrypted` direcotry within the `custom_components` directory of your homeassistant installation. 
The `custom_components` directory resides within your homeassistant configuration directory.
**Note**: if the custom_components directory does not exist, you need to create it.
After a correct installation, your configuration directory should look like the following.

    ```
    └── ...
    └── configuration.yaml
    └── custom_components
        └── samsungtv_encrypted
            └── __init__.py
            └── media_player.py
            └── manifest.json
            └── get_token.py
            └── PySmartCrypto
                └── pysmartcrypto.py
    ```

# Configuration

## Recommended: Home Assistant UI

1. Install the integration and restart Home Assistant.
2. Keep the TV turned on and reachable on the network.
3. Go to **Settings -> Devices & services**.
4. If Home Assistant discovers the TV, select the discovered SamsungTV Encrypted SSDP device.
5. If discovery does not find the TV, use **Add integration -> SamsungTV Encrypted SSDP** and enter the host/IP and port.
6. Enter the PIN shown on the TV when Home Assistant asks for it.

The integration stores the encrypted token and session id in Home Assistant's config entry. Running `get_token.py`
manually is no longer needed for the normal setup path.

The TV name is taken from SSDP/UPnP discovery when available. The MAC address is detected from the local ARP cache
after the TV has been contacted and is exposed as a diagnostic sensor. It is not required for normal control.

## Legacy: get_token.py and YAML

The old setup path is still available for installations that prefer YAML or need custom script actions.

1. Use `get_token.py` to get your Samsung TV token (use `--port 8080`). Store TOKEN (CTX) and SESSION_ID output. Your TV
must be turned on and connected to the network with the specific IP. The terminal where you executed `get_token.py` will
ask for the PIN shown on the TV.

**Note**: In some models the TOKEN can expire after a time (maybe a week, month), or even be invalidated due to a loss of
TV power. In that case you have to repeat this process again.

2. Enable the component by editing `configuration.yaml`:

### Example configuration.yaml

```yaml
media_player:
  - platform: samsungtv_encrypted
    host: IP_ADDRESS
    token: TOKEN
    sessionid: SESSION_ID
    port: 8080
```

**Note**: This is the same as the configuration for the built-in
[Samsung Smart TV](https://www.home-assistant.io/integrations/samsungtv/) component, except for the custom variables.

### Custom variables

- **token:** (string) (Required) This contains the token of your encrypted TV.
- **sessionid:** (string) (Required) This contains the session id of your encrypted TV.
- **key_power_off:** (string) (Optional) Some TV models use an encrypted command to turn off the TV different from the
  command used by default. Try `KEY_POWER` here if `KEY_POWEROFF` does not work.
  <br>Default value: `KEY_POWEROFF`
- **turn_on_action:** (script) (Optional) Script formatted command to turn on the TV.
- **turn_off_action:** (script) (Optional) Script formatted command to turn off the TV.

Example `turn_on_action`:

```yaml
- platform: samsungtv_encrypted
  ...
  turn_on_action:
    - service: kodi.call_method
      data:
        entity_id: media_player.kodi
        method: Addons.ExecuteAddon
        addonid: script.json-cec
        params:
          command: turn_on 0
```

Example `turn_off_action`:

```yaml
- platform: samsungtv_encrypted
  ...
  turn_off_action:
    - service: switch.turn_on
      target:
        entity_id: switch.samsung_tv_power
```

# Additional Features

### Source selection

The integration exposes the TV-reported `source` and `source_list` through the Home Assistant media player entity.
Only sources reported by the TV as connected are offered for selection.

### Diagnostic sensors

The integration also exposes read-only diagnostic sensors for the configured host, port, and detected MAC address.

### Send Keys

Send keys using a native Home Assistant service:

```
service: media_player.play_media
```

```json
{
  "entity_id": "media_player.samsungtv",
  "media_content_type": "send_key",
  "media_content_id": "KEY_CODE"
}
```
**Note**: Change "KEY_CODE" by desired key_code.

Multiple keys can be sent sequentially by joining them with `+`, for example `KEY_VOLUP+KEY_CHUP`.

You can get lots of key codes [here](https://github.com/roberodin/ha-samsungtv-custom#key-codes)

Here you can see an example of a Home Assistant script using the media_player.play_media service:
```
tv_channel_down:
  alias: Channel down
  sequence:
  - service: media_player.play_media
    data:
      entity_id: media_player.samsung_tv55
      media_content_type: "send_key"
      media_content_id: KEY_CHDOWN
```

# Working Models

- **H4500**
- **H5500**
- **H6200**
- **H6400**
- **HU7100**
- **HU7500**
- **HU8500**
- **HU8550**
- **J6350**

# Not Working Models

- **J8000**

# Contribution

Feel free to contribute with other working models and to submit fixes and improvements to the code.

Recent maintenance of this fork used AI-assisted development with human review, local checks, and hardware feedback from
real Home Assistant testing. Changes are recorded in `NOTICE`.

# Note from sermayoral (previous integration developer)

If you like this custom component and it is useful for you, please consider supporting me:

<a href="https://www.buymeacoffee.com/XAF0dnBOG" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

<a href="https://www.paypal.me/sermayoral" target="_blank"><img src="https://pluspng.com/img-png/-460.png" alt="Donate with PayPal" width="170" height="36" ></a>
