from __future__ import annotations

from typing import Optional

from capabilities import CapabilityMatrix
from providers.base import BaseProvider
from providers.linux import LinuxProvider
from providers.windows import WindowsProvider


def get_provider(capabilities: CapabilityMatrix) -> BaseProvider:
    if capabilities.is_windows:
        return WindowsProvider(capabilities)
    return LinuxProvider(capabilities)
