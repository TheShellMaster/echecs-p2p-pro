class_name LanChessTransport
extends Node
## Découverte et partie directe sur le réseau local. Aucun service distant.

signal rooms_changed(rooms: Array)
signal state_changed(message: String)
signal session_started(local_is_white: bool, initial_fen: String)
signal remote_move_received(uci: String, ply: int)
signal session_ended(reason: String)

const UDP_PORT := 24681
const DEFAULT_TCP_PORT := 24682
const PROTOCOL := 1
const ADVERTISE_INTERVAL := 1.5
const ROOM_TTL := 5.0
const MAX_LINE_BYTES := 4096

var _udp := PacketPeerUDP.new()
var _server := TCPServer.new()
var _peer: StreamPeerTCP
var _rooms: Dictionary = {}
var _rx_buffer := ""
var _advertise_accumulator := 0.0
var _scan_accumulator := 0.0
var _session_active := false
var _local_is_host := false
var _local_is_white := true
var _expected_ply := 0
var _device_name := "Échecs"
var _room_id := ""
var _remote_id := ""
var _listening := false
var _discovering := false
var _hello_sent := false
var _connection_started_msec := 0


func _ready() -> void:
	_device_name = "Appareil %s · %04d" % [OS.get_name(), randi_range(1000, 9999)]
	set_process(true)


func _process(delta: float) -> void:
	if _listening:
		_advertise_accumulator += delta
		if _advertise_accumulator >= ADVERTISE_INTERVAL:
			_advertise_accumulator = 0.0
			_broadcast_room()
			_prune_rooms()
	if _discovering:
		_scan_accumulator += delta
		if _scan_accumulator >= 0.35:
			_scan_accumulator = 0.0
			_read_advertisements()
	if _peer != null:
		if not _session_active and Time.get_ticks_msec() - _connection_started_msec > 15000:
			_drop_peer("La connexion locale a expiré. Relancez la recherche.")
			return
		_poll_peer()
	if _server.is_connection_available() and _local_is_host and _peer == null:
		_accept_peer()


func start_discovery() -> bool:
	stop_discovery()
	if _udp.bind(UDP_PORT) != OK:
		state_changed.emit("Le réseau local ne peut pas être écouté sur ce port.")
		return false
	_udp.set_broadcast_enabled(true)
	_discovering = true
	_scan_accumulator = 0.0
	_rooms.clear()
	rooms_changed.emit([])
	state_changed.emit("Recherche des appareils sur le même réseau…")
	return true


func stop_discovery() -> void:
	_discovering = false
	if _udp.is_bound():
		_udp.close()


func start_host() -> bool:
	close_session()
	stop_discovery()
	var result := _server.listen(DEFAULT_TCP_PORT, "0.0.0.0")
	if result != OK:
		state_changed.emit("Impossible d’ouvrir le port local de partie (%d)." % DEFAULT_TCP_PORT)
		return false
	_local_is_host = true
	_room_id = _new_id()
	_listening = true
	_advertise_accumulator = ADVERTISE_INTERVAL
	_broadcast_room()
	state_changed.emit("Partie ouverte. En attente d’un joueur sur le même réseau…")
	return true


func join_room(room: Dictionary) -> bool:
	close_session()
	stop_discovery()
	if not _valid_room(room):
		state_changed.emit("Cette annonce de partie n’est pas valide ou a expiré.")
		return false
	_peer = StreamPeerTCP.new()
	_connection_started_msec = Time.get_ticks_msec()
	var result := _peer.connect_to_host(String(room.ip), int(room.port))
	if result != OK:
		_peer = null
		state_changed.emit(
			"Connexion directe impossible. Vérifiez que les appareils sont sur le même réseau."
		)
		return false
	_local_is_host = false
	_remote_id = String(room.id)
	_rx_buffer = ""
	state_changed.emit("Connexion directe à %s…" % String(room.name))
	return true


func send_move(uci: String, current_ply: int) -> bool:
	if not _session_active or _peer == null or current_ply != _expected_ply:
		return false
	if current_ply % 2 != (0 if _local_is_white else 1):
		return false
	if uci.length() != 4 and uci.length() != 5:
		return false
	if not _send_packet({"type": "move", "uci": uci.to_lower(), "ply": current_ply}):
		return false
	_expected_ply += 1
	return true


func local_is_white() -> bool:
	return _local_is_white


func is_session_active() -> bool:
	return _session_active


func close_session(reason: String = "Partie locale terminée.") -> void:
	if _session_active or _peer != null:
		session_ended.emit(reason)
	_session_active = false
	_expected_ply = 0
	_rx_buffer = ""
	if _peer != null:
		_peer.disconnect_from_host()
		_peer = null
	if _server.is_listening():
		_server.stop()
	_listening = false
	_local_is_host = false
	_room_id = ""
	_remote_id = ""
	_hello_sent = false


func _read_advertisements() -> void:
	while _udp.get_available_packet_count() > 0:
		var raw := _udp.get_packet().get_string_from_utf8()
		if raw.to_utf8_buffer().size() > MAX_LINE_BYTES:
			continue
		var parsed: Variant = JSON.parse_string(raw)
		if not parsed is Dictionary or not _valid_advertisement(parsed):
			continue
		if _listening and String(parsed.id) == _room_id:
			continue
		var sender_ip := _udp.get_packet_ip()
		if sender_ip.is_empty() or sender_ip == "127.0.0.1":
			continue
		var room: Dictionary = parsed.duplicate()
		room.ip = sender_ip
		room.seen_msec = Time.get_ticks_msec()
		var id := String(room.id)
		var changed: bool = (
			not _rooms.has(id) or _rooms[id].ip != sender_ip or _rooms[id].name != room.name
		)
		_rooms[id] = room
		if changed:
			_emit_rooms()


func _prune_rooms() -> void:
	var now := Time.get_ticks_msec()
	var removed := false
	for id in _rooms.keys():
		if now - int(_rooms[id].seen_msec) > int(ROOM_TTL * 1000.0):
			_rooms.erase(id)
			removed = true
	if removed:
		_emit_rooms()


func _emit_rooms() -> void:
	var result: Array = _rooms.values()
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.name < b.name)
	rooms_changed.emit(result)


func _broadcast_room() -> void:
	var announcer := PacketPeerUDP.new()
	if announcer.bind(0) != OK:
		return
	announcer.set_broadcast_enabled(true)
	announcer.set_dest_address("255.255.255.255", UDP_PORT)
	var packet := {
		"protocol": PROTOCOL,
		"type": "advertise",
		"id": _room_id,
		"name": _device_name,
		"port": DEFAULT_TCP_PORT
	}
	announcer.put_packet(JSON.stringify(packet).to_utf8_buffer())
	announcer.close()


func _accept_peer() -> void:
	_peer = _server.take_connection()
	_connection_started_msec = Time.get_ticks_msec()
	_rx_buffer = ""
	_remote_id = ""
	state_changed.emit("Un appareil demande à rejoindre la partie…")


func _poll_peer() -> void:
	_peer.poll()
	var status := _peer.get_status()
	if status == StreamPeerTCP.STATUS_ERROR or status == StreamPeerTCP.STATUS_NONE:
		_drop_peer("La connexion locale a été interrompue.")
		return
	if status != StreamPeerTCP.STATUS_CONNECTED:
		return
	var available := _peer.get_available_bytes()
	if available > 0:
		if available > MAX_LINE_BYTES:
			_drop_peer("Données réseau trop volumineuses, connexion refusée.")
			return
		var read_result: Array = _peer.get_data(available)
		if int(read_result[0]) != OK:
			_drop_peer("Impossible de lire les données reçues.")
			return
		_rx_buffer += (read_result[1] as PackedByteArray).get_string_from_utf8()
		if _rx_buffer.to_utf8_buffer().size() > MAX_LINE_BYTES:
			_drop_peer("Message réseau trop long, connexion refusée.")
			return
		_process_buffer()
	if _peer != null and not _session_active:
		if _local_is_host and _remote_id.is_empty():
			if not _hello_sent:
				_hello_sent = _send_packet({"type": "hello", "protocol": PROTOCOL, "id": _room_id})


func _process_buffer() -> void:
	while true:
		var newline := _rx_buffer.find("\n")
		if newline < 0:
			return
		var line := _rx_buffer.substr(0, newline).strip_edges()
		_rx_buffer = _rx_buffer.substr(newline + 1)
		var parsed: Variant = JSON.parse_string(line)
		if not parsed is Dictionary or not _handle_packet(parsed):
			_drop_peer("Le message reçu ne respecte pas le protocole de partie.")
			return


func _handle_packet(packet: Dictionary) -> bool:
	if not packet.has("type") or typeof(packet.type) != TYPE_STRING:
		return false
	match packet.type:
		"hello":
			return _handle_hello(packet)
		"join":
			return _handle_join(packet)
		"start":
			return _handle_start(packet)
		"move":
			return _handle_move(packet)
		_:
			return false


func _handle_hello(packet: Dictionary) -> bool:
	if _local_is_host or _session_active or packet.get("protocol") != PROTOCOL:
		return false
	var host_id: String = packet.get("id", "")
	if host_id != _remote_id:
		return false
	_remote_id = host_id
	return _send_packet({"type": "join", "protocol": PROTOCOL, "id": _new_id()})


func _handle_join(packet: Dictionary) -> bool:
	if not _local_is_host or _session_active or packet.get("protocol") != PROTOCOL:
		return false
	if typeof(packet.get("id")) != TYPE_STRING or String(packet.id).length() > 64:
		return false
	_remote_id = String(packet.id)
	_session_active = true
	_local_is_white = true
	_expected_ply = 0
	_listening = false
	if not _send_packet({"type": "start", "fen": ChessGame.START_FEN, "white": false}):
		return false
	session_started.emit(true, ChessGame.START_FEN)
	state_changed.emit("Joueur connecté. Vous jouez les Blancs.")
	return true


func _handle_start(packet: Dictionary) -> bool:
	if _local_is_host or _session_active or typeof(packet.get("fen")) != TYPE_STRING:
		return false
	var fen := String(packet.fen)
	var rules := ChessGame.new(fen)
	if fen != ChessGame.START_FEN or rules.to_fen() != fen or packet.get("white") != false:
		return false
	_session_active = true
	_local_is_white = false
	_expected_ply = 0
	_listening = false
	session_started.emit(false, fen)
	state_changed.emit("Connecté. Vous jouez les Noirs.")
	return true


func _handle_move(packet: Dictionary) -> bool:
	if not _session_active or typeof(packet.get("uci")) != TYPE_STRING:
		return false
	var ply: Variant = packet.get("ply")
	var uci := String(packet.uci).to_lower()
	if typeof(ply) != TYPE_INT or int(ply) != _expected_ply:
		return false
	if uci.length() != 4 and uci.length() != 5:
		return false
	if _expected_ply % 2 == (0 if _local_is_white else 1):
		return false
	_expected_ply += 1
	remote_move_received.emit(uci, int(ply))
	return true


func _send_packet(packet: Dictionary) -> bool:
	if _peer == null or _peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		return false
	var bytes := (JSON.stringify(packet) + "\n").to_utf8_buffer()
	return _peer.put_data(bytes) == OK


func _drop_peer(reason: String) -> void:
	if _peer != null:
		_peer.disconnect_from_host()
		_peer = null
	var was_active := _session_active
	_session_active = false
	_expected_ply = 0
	_remote_id = ""
	_rx_buffer = ""
	if was_active:
		session_ended.emit(reason)
	state_changed.emit(reason)


func _valid_advertisement(packet: Dictionary) -> bool:
	return (
		packet.get("protocol") == PROTOCOL
		and packet.get("type") == "advertise"
		and typeof(packet.get("id")) == TYPE_STRING
		and String(packet.id).length() >= 8
		and String(packet.id).length() <= 64
		and typeof(packet.get("name")) == TYPE_STRING
		and not String(packet.name).strip_edges().is_empty()
		and String(packet.name).length() <= 80
		and typeof(packet.get("port")) == TYPE_INT
		and int(packet.port) > 0
		and int(packet.port) <= 65535
	)


func _valid_room(room: Dictionary) -> bool:
	return (
		typeof(room.get("ip")) == TYPE_STRING
		and typeof(room.get("port")) == TYPE_INT
		and int(room.port) > 0
		and int(room.port) <= 65535
		and typeof(room.get("id")) == TYPE_STRING
	)


func _new_id() -> String:
	return "%s-%s" % [str(Time.get_ticks_usec()), str(randi())]
