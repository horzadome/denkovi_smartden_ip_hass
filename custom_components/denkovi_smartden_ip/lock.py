"""Lock platform for the relays the user configured as a lock."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_LOCK
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user configured as a lock."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelayLock, {RELAY_TYPE_LOCK})


class DenkoviRelayLock(DenkoviRelayEntity, LockEntity):
    """Represent one relay as a lock.

    The lock device class reads an on state as unlocked, so a locked lock holds
    the relay off.
    """

    @property
    def is_locked(self) -> bool | None:
        """Return True when the relay is off."""
        state = self.is_on
        return None if state is None else not state

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock by turning the relay off."""
        await self._set_state(False)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock by turning the relay on."""
        await self._set_state(True)
