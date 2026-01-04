"""
Abstract base class for TV controllers.

All TV controller implementations must inherit from this class and implement
all abstract methods
"""

from abc import ABC, abstractmethod


class BaseTVController(ABC):
    """
    Abstract base class defining the interface for TV controllers.

    New protocol implementations should:
    1. Inherit from this class
    2. Implement all abstract methods
    3. Accept a config dict in __init__ and extract needed parameters
    """

    @abstractmethod
    def __init__(self, config: dict):
        """
        Initialize the TV controller with configuration.

        Args:
            config: Dictionary containing all configuration for this TV.
                   Different protocols may require different config keys.
        """
        pass

    @abstractmethod
    def power_on(self):
        """Turn the TV on."""
        pass

    @abstractmethod
    def power_off(self):
        """Turn the TV off."""
        pass

    @abstractmethod
    def toggle_power(self):
        """
        Toggle the TV power state.

        Returns:
            int: Power state code (implementation-specific)
        """
        pass

    @abstractmethod
    def volume_up(self):
        """
        Increase volume by one step."""
        pass

    @abstractmethod
    def volume_down(self):
        """Decrease volume by one step."""
        pass

    @abstractmethod
    def toggle_mute(self):
        """
        Toggle mute state.

        Returns:
            int: Mute state code (implementation-specific)
        """
        pass

    @abstractmethod
    def get_power_state(self):
        """
        Get current power state.

        Returns:
            int: Power state code (implementation-specific)
        """
        pass

    @abstractmethod
    def get_volume_value(self):
        """
        Get current volume value.

        Returns:
            int: Current volume
        """
        pass

    @abstractmethod
    def get_mute_state(self):
        """
        Get current mute state.

        Returns:
            int: Mute state code (implementation-specific)
        """
        pass

    # Optional methods with default implementations
    def standby_on(self):
        """
        Enable standby mode (if supported by protocol).
        Default implementation does nothing.
        """
        pass

    def standby_off(self):
        """
        Disable standby mode (if supported by protocol).
        Default implementation does nothing.
        """
        pass

    # Common constants that main.py expects
    POWER_OFF_DATA = 0x00
    POWER_ON_DATA = 0x01
