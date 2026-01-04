import serial
import logging
from base_tv_controller import BaseTVController

# Packet format: [header (get or set), control, command code, length of data including checksum, data, checksum]

logger = logging.getLogger(__name__)


# [Info](https://pro-bravia.sony.net/develop/integrate/rs-232c/index.html)
class SonyBraviaSerial(BaseTVController):
    HEADER_SET = 0x8C
    HEADER_GET = 0x83

    CATEGORY = 0x00

    # Power
    POWER_FUNCTION = 0x00
    POWER_OFF_DATA = 0x00
    POWER_ON_DATA = 0x01

    # Standby
    STANDBY_FUNCTION = 0x01
    STANDBY_DISABLE_DATA = 0x00
    STANDBY_ENABLE_DATA = 0x01

    # Volume
    VOLUME_FUNCTION = 0x05
    ## As opposed to directly setting the volume (not implemented)
    VOLUME_UPDOWN_DATA = 0x00
    VOLUME_UP_DATA = 0x00
    VOLUME_DOWN_DATA = 0x01

    # Mute
    MUTE_FUNCTION = 0x06
    ## Toggle
    MUTE_DATA = 0x00

    # Status codes for SET command responses
    STATUS_MESSAGES_SET = {
        0x00: "Completed (Normal End)",
        0x01: "Limit Over (value exceeds maximum)",
        0x02: "Limit Over (value below minimum)",
        0x03: "Command Canceled (data incorrect or not acceptable in current state)",
        0x04: "Parse Error (data format error or checksum error)",
    }

    # Status codes for GET command responses
    STATUS_MESSAGES_GET = {
        0x00: "Completed",
        0x03: "Command Canceled (not acceptable in current state)",
        0x04: "Parse Error (data format error or checksum error)",
    }

    def __init__(self, config: dict):
        """
        Initialize Sony Bravia serial controller.

        Required config keys:
            - port: Serial port path (e.g., "/dev/ttyUSB0")

        Optional config keys:
            - auto_enable_standby: Enable standby mode on init (default: True)
        """
        self.port = config["port"]
        auto_enable_standby = config.get("auto_enable_standby", True)

        logger.info(f"Initializing serial connection to {self.port}")
        self.serial = serial.Serial(
            self.port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
        )
        logger.info(f"Serial connection to {self.port} established")

        # Auto-enable standby mode if configured
        if auto_enable_standby:
            try:
                logger.info(f"[{self.port}] Attempting to enable standby mode...")
                self.standby_on()
                logger.info(f"[{self.port}] Standby mode enabled successfully")
            except ValueError as e:
                error_msg = str(e)
                if "No response" in error_msg:
                    logger.warning(
                        f"[{self.port}] TV is powered off - standby mode will be set when TV is turned on manually"
                    )
                elif "Parse Error" in error_msg or "Command Canceled" in error_msg:
                    # These are expected when standby mode is already enabled or not applicable
                    logger.info(
                        f"[{self.port}] Standby mode already configured or not needed"
                    )
                else:
                    logger.warning(f"[{self.port}] Could not enable standby mode: {e}")

    def _compute_data_length(self, data):
        """
        The length of the data includes the checksum data, which is length 1
        """
        return len(data) + 1

    def _compute_checksum(self, packet):
        """
        Total sum from the "Byte[1]" to the data "Byte[N+4]".
        If the value is over 0xFF (1 byte), the last byte of data is used.
        """
        total = sum(packet)
        return total % 256

    def _send_set_command(self, data, function):
        data_length = self._compute_data_length(data)
        packet = [
            self.HEADER_SET,
            self.CATEGORY,
            function,
            data_length,
            *data,
        ]
        checksum = self._compute_checksum(packet)
        packet.append(checksum)

        logger.debug(
            f"[{self.port}] Sending SET command - Function: {function:#04x}, Data: {[hex(b) for b in data]}"
        )
        logger.debug(f"[{self.port}] Full packet: {[hex(b) for b in packet]}")

        self.serial.write(bytes(packet))
        response = self.serial.read(3)

        logger.debug(
            f"[{self.port}] Response received: {[hex(b) for b in response] if response else 'NONE'}"
        )

        if len(response) != 3:
            logger.error(
                f"[{self.port}] No response from TV (expected 3 bytes, got {len(response)})"
            )
            raise ValueError("No response from TV")
        else:
            status = response[1]
            status_msg = self.STATUS_MESSAGES_SET.get(
                status, f"Unknown status: {status:#04x}"
            )

            if status != 0x00:
                # Log error responses at DEBUG level; caller will handle logging/reporting
                logger.debug(f"[{self.port}] SET command response: {status_msg}")
                raise ValueError(status_msg)
            else:
                logger.info(f"[{self.port}] SET command response: {status_msg}")

    def _send_get_command(self, function):
        data = [0xFF, 0xFF]
        packet = [
            self.HEADER_GET,
            self.CATEGORY,
            function,
            *data,
        ]
        checksum = self._compute_checksum(packet)
        packet.append(checksum)

        logger.debug(f"[{self.port}] Sending GET command - Function: {function:#04x}")
        logger.debug(f"[{self.port}] Full packet: {[hex(b) for b in packet]}")

        self.serial.write(bytes(packet))
        response = self.serial.read(3)

        logger.debug(
            f"[{self.port}] Response header received: {[hex(b) for b in response] if response else 'NONE'}"
        )

        if len(response) != 3:
            logger.error(
                f"[{self.port}] No response from TV (expected 3 bytes, got {len(response)})"
            )
            raise ValueError("No response from TV")
        else:
            status = response[1]
            status_msg = self.STATUS_MESSAGES_GET.get(
                status, f"Unknown status: {status:#04x}"
            )

            if status == 0x00:
                return_data_size = response[2]
                return_data = self.serial.read(return_data_size)
                logger.debug(
                    f"[{self.port}] Data received: {[hex(b) for b in return_data]}"
                )
                return return_data
            else:
                # Log error responses at DEBUG level; caller will handle logging/reporting
                logger.debug(f"[{self.port}] GET command response: {status_msg}")
                raise ValueError(status_msg)

    def power_on(self):
        self._send_set_command([self.POWER_ON_DATA], self.POWER_FUNCTION)

    def power_off(self):
        self._send_set_command([self.POWER_OFF_DATA], self.POWER_FUNCTION)

    def standby_on(self):
        """Enable standby mode (allows TV to wake via serial)."""
        self._send_set_command([self.STANDBY_ENABLE_DATA], self.STANDBY_FUNCTION)

    def standby_off(self):
        """Disable standby mode (TV will go to deep standby on power off)."""
        self._send_set_command([self.STANDBY_DISABLE_DATA], self.STANDBY_FUNCTION)

    def toggle_power(self):
        power_state = self.get_power_state()
        if power_state == self.POWER_OFF_DATA:
            self.power_on()
            return self.POWER_ON_DATA
        elif power_state == self.POWER_ON_DATA:
            self.power_off()
            return self.POWER_OFF_DATA

    def volume_up(self):
        self._send_set_command(
            [self.VOLUME_UPDOWN_DATA, self.VOLUME_UP_DATA], self.VOLUME_FUNCTION
        )

    def volume_down(self):
        self._send_set_command(
            [self.VOLUME_UPDOWN_DATA, self.VOLUME_DOWN_DATA], self.VOLUME_FUNCTION
        )

    def toggle_mute(self):
        self._send_set_command([self.MUTE_DATA], self.MUTE_FUNCTION)
        mute_state = self.get_mute_state()
        return mute_state

    def get_power_state(self):
        return_data = self._send_get_command(self.POWER_FUNCTION)
        power_state = return_data[0]
        return power_state

    def get_volume_value(self):
        return_data = self._send_get_command(self.VOLUME_FUNCTION)
        volume_value = return_data[1]
        return volume_value

    def get_mute_state(self):
        return_data = self._send_get_command(self.MUTE_FUNCTION)
        mute_state = return_data[1]
        return mute_state
