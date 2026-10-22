class_name UCIEngine
extends RefCounted
## Pilote de moteur UCI (Stockfish local) hors ligne avec détection automatique du binaire.

var _pipe: Dictionary = {}
var _is_ready := false
var _engine_path := ""

func _init() -> void:
	_engine_path = _find_engine()
	if not _engine_path.is_empty():
		_start_engine()

func is_available() -> bool:
	return _is_ready and _pipe.has("stdio")

func _find_engine() -> String:
	var candidates: Array[String] = []
	var exec_dir := OS.get_executable_path().get_base_dir()
	candidates.append(exec_dir.path_join("stockfish_bin"))
	candidates.append(exec_dir.path_join("stockfish.exe"))
	candidates.append(exec_dir.path_join("stockfish"))
	
	var res_parent := ProjectSettings.globalize_path("res://../").simplify_path()
	candidates.append(res_parent.path_join("stockfish_bin"))
	candidates.append(res_parent.path_join("stockfish.exe"))
	candidates.append(res_parent.path_join("stockfish"))
	
	var res_dir := ProjectSettings.globalize_path("res://").simplify_path()
	candidates.append(res_dir.path_join("stockfish_bin"))
	candidates.append(res_dir.path_join("stockfish.exe"))
	
	candidates.append("/usr/games/stockfish")
	candidates.append("/usr/local/bin/stockfish")
	candidates.append("/usr/bin/stockfish")
	
	for path in candidates:
		if FileAccess.file_exists(path):
			return path
	return ""

func _start_engine() -> bool:
	if _engine_path.is_empty():
		return false
	_pipe = OS.execute_with_pipe(_engine_path, PackedStringArray())
	if not _pipe.has("stdio"):
		return false
	var io: FileAccess = _pipe.stdio
	io.store_string("uci\n")
	io.flush()
	
	var start_time := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start_time < 2000:
		if io.get_length() > 0 or io.get_position() < io.get_length():
			var line := io.get_line().strip_edges()
			if line == "uciok":
				_is_ready = true
				io.store_string("isready\n")
				io.flush()
				return true
		OS.delay_msec(10)
	# Si uciok n'a pas répondu à temps, on accepte si le pipe est valide
	_is_ready = true
	return true

func set_skill_level(level: int) -> void:
	if not is_available():
		return
	var io: FileAccess = _pipe.stdio
	# Niveaux Stockfish de 0 à 20
	var skill := clampi(level, 0, 20)
	io.store_string("setoption name Skill Level value %d\n" % skill)
	io.flush()

func get_best_move(moves_uci: PackedStringArray, movetime_ms := 300) -> String:
	if not is_available():
		return ""
	var io: FileAccess = _pipe.stdio
	if moves_uci.is_empty():
		io.store_string("position startpos\n")
	else:
		io.store_string("position startpos moves %s\n" % " ".join(moves_uci))
	io.store_string("go movetime %d\n" % movetime_ms)
	io.flush()
	
	var start_time := Time.get_ticks_msec()
	var timeout_ms := movetime_ms + 2500
	while Time.get_ticks_msec() - start_time < timeout_ms:
		var line := io.get_line().strip_edges()
		if line.begins_with("bestmove"):
			var parts := line.split(" ")
			if parts.size() >= 2:
				return parts[1]
		OS.delay_msec(10)
	return ""

func close() -> void:
	if _pipe.has("stdio"):
		var io: FileAccess = _pipe.stdio
		io.store_string("quit\n")
		io.flush()
	_is_ready = false
	_pipe.clear()
