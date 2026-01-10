"""Mock SSH server for integration testing."""

import asyncio
import asyncssh


class MockSSHServer(asyncssh.SSHServer):
    """Mock SSH server that simulates a network device."""

    def connection_made(self, conn):
        """Called when a connection is made."""
        print(f"Connection from {conn.get_extra_info('peername')}")

    def connection_lost(self, exc):
        """Called when connection is lost."""
        if exc:
            print(f"Connection lost: {exc}")

    def begin_auth(self, username):
        """Begin authentication."""
        return True

    def password_auth_supported(self):
        """Password authentication is supported."""
        return True

    def validate_password(self, username, password):
        """Validate password."""
        # Accept any admin/admin123 combination
        if username == "admin" and password == "admin123":
            return True
        return False


class MockSSHServerSession(asyncssh.SSHServerSession):
    """Mock SSH session handler."""

    def __init__(self):
        self._current_mode = "exec"
        self._buffer = ""

    def connection_made(self, chan):
        """Called when the channel is opened."""
        self._chan = chan

    def shell_requested(self):
        """Shell is requested."""
        return True

    def session_started(self):
        """Session started."""
        self._chan.write("Mock Device>\r\n")

    def data_received(self, data, datatype):
        """Data received from client."""
        self._buffer += data

        # Process complete lines
        while "\n" in self._buffer or "\r" in self._buffer:
            # Find line ending
            idx_n = self._buffer.find("\n")
            idx_r = self._buffer.find("\r")

            if idx_n == -1:
                idx = idx_r
            elif idx_r == -1:
                idx = idx_n
            else:
                idx = min(idx_n, idx_r)

            line = self._buffer[:idx].strip()
            self._buffer = self._buffer[idx + 1 :]

            if line:
                self._process_command(line)

    def _process_command(self, command):
        """Process a command."""
        command = command.strip()

        if not command:
            self._send_prompt()
            return

        # Config mode commands
        if command == "configure terminal" or command == "conf t":
            self._current_mode = "config"
            self._chan.write("Entering configuration mode\r\n")
            self._send_prompt()
        elif command == "end" or command == "exit":
            if self._current_mode == "config":
                self._current_mode = "exec"
            self._send_prompt()

        # Show commands
        elif command.startswith("show running-config") or command.startswith(
            "show run"
        ):
            output = """!
! Mock Configuration
!
hostname MockDevice
!
snmp-server community public RO
snmp-server location Lab
!
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
!
end
"""
            self._chan.write(output + "\r\n")
            self._send_prompt()

        elif (
            command.startswith("show ip interface brief") or command == "show ip int br"
        ):
            output = """Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/1     192.168.1.1     YES manual up                    up
"""
            self._chan.write(output + "\r\n")
            self._send_prompt()

        # Config commands
        elif self._current_mode == "config":
            # Simulate successful config
            if "invalid" in command.lower():
                self._chan.write("% Invalid input detected\r\n")
            else:
                # Just accept the command
                pass
            self._send_prompt()

        else:
            # Unknown command
            self._chan.write(f"% Unknown command: {command}\r\n")
            self._send_prompt()

    def _send_prompt(self):
        """Send the appropriate prompt."""
        if self._current_mode == "config":
            self._chan.write("Mock Device(config)#")
        else:
            self._chan.write("Mock Device#")

    def break_received(self, msec):
        """Break received."""
        pass

    def signal_received(self, signal):
        """Signal received."""
        pass

    def terminal_size_changed(self, width, height, pixwidth, pixheight):
        """Terminal size changed."""
        pass


async def start_server(host="0.0.0.0", port=2222):
    """Start the mock SSH server."""
    await asyncssh.create_server(
        MockSSHServer,
        host,
        port,
        session_factory=MockSSHServerSession,
        server_host_keys=["/tmp/ssh_host_key"],
        keepalive_interval=15,
    )

    print(f"Mock SSH server started on {host}:{port}")

    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    # Generate host key if it doesn't exist
    try:
        with open("/tmp/ssh_host_key", "r"):
            pass
    except FileNotFoundError:
        # Generate a key
        import subprocess

        subprocess.run(["ssh-keygen", "-t", "rsa", "-f", "/tmp/ssh_host_key", "-N", ""])

    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nShutting down...")
