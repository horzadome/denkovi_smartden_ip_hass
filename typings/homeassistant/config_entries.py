"""Type declarations for the part of homeassistant.config_entries that this integration reads."""

from enum import Enum
from typing import Any

SOURCE_USER: str


class ConfigEntryState(Enum):
    """The state of a configuration entry."""

    LOADED = "loaded"
    SETUP_ERROR = "setup_error"
    MIGRATION_ERROR = "migration_error"
    SETUP_RETRY = "setup_retry"
    NOT_LOADED = "not_loaded"
    FAILED_UNLOAD = "failed_unload"
    SETUP_IN_PROGRESS = "setup_in_progress"
    UNLOAD_IN_PROGRESS = "unload_in_progress"


class ConfigEntry:
    """A configuration entry of Home Assistant."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        pass


class ConfigFlow:
    """The base class of a Home Assistant configuration flow."""

    def __init_subclass__(cls, *, domain: str | None = None, **kwargs: Any) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        pass


class OptionsFlowWithReload:
    """The base class of a Home Assistant options flow that reloads its entry."""

    def __getattr__(self, name: str) -> Any:
        pass
