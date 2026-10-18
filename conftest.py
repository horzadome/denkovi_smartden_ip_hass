"""Shared test configuration."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load this custom integration in every test."""
    return


@pytest.fixture(autouse=True)
def socket_for_marked_tests(request):
    """Let a test marked `enable_socket` open a socket.

    `pytest_homeassistant_custom_component` disables sockets in `pytest_runtest_setup`
    without reading the marker, so the marker only wins when `pytest_socket` happens to be
    registered after that plugin. This fixture re-enables the socket after every
    `pytest_runtest_setup` hook has run, so the marker works in any order.
    """
    if request.node.get_closest_marker("enable_socket") is None:
        yield
        return

    import pytest_socket

    pytest_socket.enable_socket()
    yield
