"""The samsungtv component for encrypted models."""

DOMAIN = "samsungtv_encrypted"
PLATFORMS = ["media_player"]


async def async_setup_entry(hass, entry):
    """Set up SamsungTV Encrypted from a config entry."""
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    if hasattr(hass.config_entries, "async_forward_entry_setups"):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    else:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "media_player")
        )
    return True


async def async_unload_entry(hass, entry):
    """Unload a SamsungTV Encrypted config entry."""
    if hasattr(hass.config_entries, "async_unload_platforms"):
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return await hass.config_entries.async_forward_entry_unload(entry, "media_player")


async def async_reload_entry(hass, entry):
    """Reload SamsungTV Encrypted after options changed."""
    await hass.config_entries.async_reload(entry.entry_id)
