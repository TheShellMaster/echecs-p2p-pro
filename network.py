import socket
import threading
import json
import time
from queue import Queue
from constants import UDP_PORT, TCP_PORT, MAGIC_DISCOVERY

class NetworkManager:
    def __init__(self):
        self.tcp_socket = None
        self.connection = None
        self.is_host = False
        self.running = True
        self.server_name = "Partie P2P"
        self.msg_queue = Queue()
        self._servers_lock = threading.Lock()
        self.discovered_servers = {}  # ip -> name
        self.udp_broadcast_sock = None
        self.udp_listen_sock = None
        self._accept_thread = None
        self._broadcast_thread = None
        self._discovery_thread = None

    def set_server_name(self, name):
        self.server_name = name or "Partie P2P"

    def get_discovered_servers(self):
        with self._servers_lock:
            return dict(self.discovered_servers)

    def host_game(self, server_name="Partie P2P"):
        self.close()
        self.is_host = True
        self.server_name = server_name or "Partie P2P"
        self.running = True

        # Setup TCP Server with retry in case of quick re-host
        for attempt in range(5):
            try:
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.tcp_socket.bind(('0.0.0.0', TCP_PORT))
                self.tcp_socket.listen(1)
                self.tcp_socket.settimeout(0.5)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(0.1)

        # Start broadcasting and accepting
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._broadcast_thread.start()
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def discover_games(self):
        with self._servers_lock:
            self.discovered_servers.clear()
        self.running = True
        threading.Thread(target=self._discovery_loop, daemon=True).start()

    def connect_to(self, ip):
        self.close()
        self.is_host = False
        self.running = True
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((ip, TCP_PORT))
            self.connection = self.tcp_socket
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def send_move(self, uci_move):
        self._send({"type": "move", "data": uci_move})

    def send_chat(self, sender, text):
        self._send({"type": "chat", "sender": sender, "text": text})

    def send_config(self, time_limit, server_name=""):
        self._send({"type": "config", "time_limit": time_limit, "server_name": server_name})

    def send_timeout(self, loser_color_name):
        self._send({"type": "timeout", "loser": loser_color_name})

    def send_resign(self):
        self._send({"type": "resign", "data": None})

    def send_rematch(self):
        self._send({"type": "rematch", "data": None})

    def _send(self, payload):
        if self.connection:
            try:
                data = json.dumps(payload).encode('utf-8')
                self.connection.sendall(data + b"\n")
            except Exception as e:
                print(f"Send error: {e}")

    def get_messages(self):
        msgs = []
        while not self.msg_queue.empty():
            msgs.append(self.msg_queue.get())
        return msgs

    def _broadcast_loop(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_broadcast_sock = udp_sock
        while self.running and not self.connection:
            try:
                payload = json.dumps({
                    "magic": MAGIC_DISCOVERY.decode('utf-8'),
                    "name": self.server_name
                }).encode('utf-8')
                udp_sock.sendto(payload, ('<broadcast>', UDP_PORT))
            except Exception:
                pass
            time.sleep(1.5)
        try:
            udp_sock.close()
        except Exception:
            pass

    def _discovery_loop(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            try:
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
        try:
            udp_sock.bind(('', UDP_PORT))
        except Exception:
            pass
        udp_sock.settimeout(1.0)
        self.udp_listen_sock = udp_sock

        while self.running and not self.connection:
            try:
                data, addr = udp_sock.recvfrom(1024)
                msg = json.loads(data.decode('utf-8', errors='ignore'))
                if msg.get("magic") == MAGIC_DISCOVERY.decode('utf-8'):
                    with self._servers_lock:
                        self.discovered_servers[addr[0]] = msg.get("name", "Salon P2P")
            except socket.timeout:
                continue
            except Exception:
                pass
        try:
            udp_sock.close()
        except Exception:
            pass

    def _accept_loop(self):
        while self.running and not self.connection and self.tcp_socket:
            try:
                conn, addr = self.tcp_socket.accept()
                conn.settimeout(None)
                self.connection = conn
                self.msg_queue.put({"type": "connected", "data": addr[0]})
                threading.Thread(target=self._receive_loop, daemon=True).start()
                break
            except socket.timeout:
                continue
            except Exception:
                break

    def _receive_loop(self):
        raw_buffer = bytearray()
        while self.running and self.connection:
            try:
                chunk = self.connection.recv(2048)
                if not chunk:
                    break
                raw_buffer.extend(chunk)
                while b"\n" in raw_buffer:
                    line, raw_buffer = raw_buffer.split(b"\n", 1)
                    line_str = line.decode('utf-8', errors='replace').strip()
                    if line_str:
                        msg = json.loads(line_str)
                        self.msg_queue.put(msg)
            except Exception as e:
                print(f"Receive error: {e}")
                break
        self.msg_queue.put({"type": "disconnected", "data": None})
        self.connection = None

    def close(self):
        self.running = False
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except Exception:
                pass
            self.tcp_socket = None
        if self.udp_broadcast_sock:
            try:
                self.udp_broadcast_sock.close()
            except Exception:
                pass
            self.udp_broadcast_sock = None
        if self.udp_listen_sock:
            try:
                self.udp_listen_sock.close()
            except Exception:
                pass
            self.udp_listen_sock = None
        if self._accept_thread and self._accept_thread.is_alive():
            try:
                self._accept_thread.join(timeout=0.6)
            except Exception:
                pass
            self._accept_thread = None
