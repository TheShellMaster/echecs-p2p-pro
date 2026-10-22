class_name Board3D
extends SubViewportContainer
## Plateau 3D réaliste : pièces Aster (Blender), lumière PBR et ombres, coups en arc,
## captures renversées au ralenti, glisser-déposer, survol et caméra cinématique.
## Même contrat que l'ancien BoardView : square_pressed, set_board_state, animate_move.
## Indices de cases : a8 = 0 → h1 = 63 (voir core/README.md).

signal square_pressed(square: int)

const ChessRules = preload("res://core/chess_game.gd")
const PIECE_SCENE := preload("res://assets/3d/aster_chess_set.glb")
const SOUNDS := {
	"move": preload("res://assets/sounds/move.wav"),
	"capture": preload("res://assets/sounds/capture.wav"),
	"check": preload("res://assets/sounds/check.wav"),
	"gameover": preload("res://assets/sounds/gameover.wav"),
}
const PIECE_NAMES := {"k": "King", "q": "Queen", "r": "Rook", "b": "Bishop", "n": "Knight", "p": "Pawn"}
## Partie de l'Opéra (Morphy, 1858) jouée en boucle au ralenti derrière les menus.
const SHOWCASE_GAME := [
	"e2e4", "e7e5", "g1f3", "d7d6", "d2d4", "c8g4", "d4e5", "g4f3", "d1f3", "d6e5",
	"f1c4", "g8f6", "f3b3", "d8e7", "b1c3", "c7c6", "c1g5", "b7b5", "c3b5", "c6b5",
	"c4b5", "b8d7", "e1c1", "a8d8", "d1d7", "d8d7", "h1d1", "e7e6", "b5d7", "f6d7",
	"b3b8", "d7b8", "d1d8",
]

## Mode vitrine : caméra en orbite lente, partie de démonstration, pas d'entrée joueur.
var showcase := false
## Facteur de durée global des animations (1 = jeu, >1 = ralenti cinématique).
var slow_factor := 1.0

var _viewport: SubViewport
var _world: Node3D
var _camera: Camera3D
var _templates := {}
var _nodes := {}  # case -> Node3D (holder)
var _pieces: Array = []
var _selected := -1
var _targets: Array = []
var _last_move := Vector2i(-1, -1)
var _checked := -1
var _hover := -1
var _hint_from := -1
var _hint_to := -1
var _overlays: Array[MeshInstance3D] = []
var _markers: Array[MeshInstance3D] = []
var _check_light: OmniLight3D
var _pending_from := -1
var _pending_to := -1
var _sync_queued := false
var _press_square := -1
var _press_pos := Vector2.ZERO
var _dragging := false
var _drag_point := Vector3.ZERO
var _time := 0.0
var _time_scale := 1.0
var _tweens: Array[Tween] = []
var _cam_yaw := 0.0
var _cam_pitch := deg_to_rad(57.0)
var _cam_distance := 15.0
var _cam_target := Vector3.ZERO
var _intro := 0.0
var _game_over_square := -1
var _players := {}
var _demo: ChessGame
var _demo_index := 0
var _demo_timer := 1.6


func _ready() -> void:
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(260, 260)
	_viewport = SubViewport.new()
	_viewport.own_world_3d = true
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.gui_disable_input = true
	add_child(_viewport)
	_world = Node3D.new()
	_viewport.add_child(_world)
	_build_environment()
	_build_board()
	_load_templates()
	for key in SOUNDS:
		var player := AudioStreamPlayer.new()
		player.stream = SOUNDS[key]
		player.volume_db = -16.0 if showcase else -4.0
		add_child(player)
		_players[key] = player
	if showcase:
		_cam_pitch = deg_to_rad(32.0)
		_cam_distance = 11.0
		_cam_yaw = deg_to_rad(-30.0)
		_demo = ChessRules.new()
		set_board_state(_demo.board, -1, [], Vector2i(-1, -1), -1)
	else:
		_intro = 1.0  # plongée cinématique d'ouverture
	_update_camera(0.0)


func _exit_tree() -> void:
	if has_meta("template_root"):
		var root: Node = get_meta("template_root")
		if is_instance_valid(root):
			root.free()
		remove_meta("template_root")
	for tween in _tweens:
		if tween.is_valid():
			tween.kill()


# --- API publique (compatible avec l'ancien BoardView) -----------------------------


func set_board_state(
	pieces: Array, picked: int, legal: Array, previous: Vector2i, checked_square: int
) -> void:
	var had_check := _checked
	_pieces = pieces.duplicate()
	_selected = picked
	_targets = legal
	_last_move = previous
	_checked = checked_square
	if _checked >= 0 and had_check != _checked:
		_play("check", 0.35)
	_refresh_markers()
	if not _sync_queued:
		_sync_queued = true
		_sync.call_deferred()


func animate_move(from_square: int, to_square: int, _piece: String) -> void:
	_pending_from = from_square
	_pending_to = to_square
	if not _sync_queued:
		_sync_queued = true
		_sync.call_deferred()


func update() -> void:
	_refresh_markers()


## Ralentit ou accélère le temps de la scène (bullet time des menus).
func set_time_scale(value: float, duration := 0.6) -> void:
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "_time_scale", clampf(value, 0.05, 2.0), duration)


## Fin de partie : le roi vaincu bascule au ralenti, la caméra tourne autour.

func set_hint(from_sq: int, to_sq: int) -> void:
	_hint_from = from_sq
	_hint_to = to_sq


func clear_hint() -> void:
	_hint_from = -1
	_hint_to = -1

func play_game_over(king_square: int) -> void:
	if king_square < 0 or _game_over_square == king_square:
		return
	_game_over_square = king_square
	_play("gameover", 0.6 * slow_factor)
	var holder: Node3D = _nodes.get(king_square)
	if holder == null:
		return
	var tween := _new_tween()
	tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_interval(0.5 * slow_factor)
	tween.tween_property(holder, "rotation:z", deg_to_rad(84.0), 2.4 * slow_factor)
	tween.parallel().tween_property(
		holder, "position", holder.position + Vector3(-0.42, 0.0, 0.0), 2.4 * slow_factor
	)
	var cam := _new_tween()
	cam.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	cam.tween_property(self, "_cam_target", _square_pos(king_square) * 0.6, 2.6 * slow_factor)
	cam.parallel().tween_property(self, "_cam_distance", _cam_distance * 0.72, 2.6 * slow_factor)


# --- Construction de la scène --------------------------------------------------------


func _build_environment() -> void:
	var env := Environment.new()
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.07, 0.08, 0.10)
	sky_mat.sky_horizon_color = Color(0.22, 0.19, 0.16)
	sky_mat.ground_bottom_color = Color(0.03, 0.03, 0.03)
	sky_mat.ground_horizon_color = Color(0.16, 0.13, 0.10)
	sky.sky_material = sky_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.05
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.08
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	_world.add_child(world_env)

	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1.0, 0.93, 0.82)
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	sun.shadow_blur = 1.6
	sun.directional_shadow_max_distance = 28.0
	sun.rotation = Vector3(deg_to_rad(-58.0), deg_to_rad(38.0), 0.0)
	_world.add_child(sun)
	var rim := OmniLight3D.new()
	rim.light_color = Color(0.55, 0.68, 1.0)
	rim.light_energy = 0.9
	rim.omni_range = 18.0
	rim.position = Vector3(-6.0, 5.0, -7.0)
	_world.add_child(rim)
	_check_light = OmniLight3D.new()
	_check_light.light_color = Color(1.0, 0.18, 0.1)
	_check_light.omni_range = 2.6
	_check_light.light_energy = 0.0
	_world.add_child(_check_light)
	_camera = Camera3D.new()
	_camera.fov = 36.0
	_world.add_child(_camera)


func _build_board() -> void:
	var table := MeshInstance3D.new()
	var table_mesh := PlaneMesh.new()
	table_mesh.size = Vector2(60, 60)
	table.mesh = table_mesh
	table.material_override = _pbr(Color(0.10, 0.07, 0.05), 0.75, 0.0)
	table.position.y = -0.34
	_world.add_child(table)

	var frame := MeshInstance3D.new()
	var frame_mesh := BoxMesh.new()
	frame_mesh.size = Vector3(9.3, 0.32, 9.3)
	frame.mesh = frame_mesh
	frame.material_override = _pbr(Color(0.20, 0.11, 0.06), 0.28, 0.0)
	frame.position.y = -0.18
	_world.add_child(frame)
	var inlay := MeshInstance3D.new()
	var inlay_mesh := BoxMesh.new()
	inlay_mesh.size = Vector3(8.18, 0.3, 8.18)
	inlay.mesh = inlay_mesh
	inlay.material_override = _pbr(Color(0.62, 0.43, 0.20), 0.25, 0.85)
	inlay.position.y = -0.165
	_world.add_child(inlay)

	var square_mesh := BoxMesh.new()
	square_mesh.size = Vector3(1.0, 0.12, 1.0)
	var overlay_mesh := PlaneMesh.new()
	overlay_mesh.size = Vector2(0.98, 0.98)
	var rng := RandomNumberGenerator.new()
	rng.seed = 64
	for square in 64:
		var row := int(square / 8)
		var file := square % 8
		var light := (row + file) % 2 == 0
		var base := Color(0.72, 0.62, 0.45) if light else Color(0.30, 0.19, 0.11)
		var tile := MeshInstance3D.new()
		tile.mesh = square_mesh
		tile.material_override = _pbr(
			base.darkened(rng.randf_range(0.0, 0.07)), rng.randf_range(0.32, 0.42), 0.0
		)
		tile.position = _square_pos(square) + Vector3(0, -0.06, 0)
		_world.add_child(tile)
		var overlay := MeshInstance3D.new()
		overlay.mesh = overlay_mesh
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color = Color(1, 1, 1, 0)
		overlay.material_override = mat
		overlay.position = _square_pos(square) + Vector3(0, 0.004, 0)
		overlay.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_world.add_child(overlay)
		_overlays.append(overlay)


func _load_templates() -> void:
	var root := PIECE_SCENE.instantiate()
	for letter in PIECE_NAMES:
		for white in [true, false]:
			var node_name := "Aster_%s_%s" % ["White" if white else "Black", PIECE_NAMES[letter]]
			var node := root.find_child(node_name, true, false) as Node3D
			if node != null:
				_templates[letter.to_upper() if white else letter] = node
	# Les gabarits restent hors de l'arbre; ils sont dupliqués à la demande.
	set_meta("template_root", root)


func _pbr(color: Color, roughness: float, metallic: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = roughness
	mat.metallic = metallic
	return mat


func _make_piece(letter: String) -> Node3D:
	var holder := Node3D.new()
	var lift := Node3D.new()
	lift.name = "Lift"
	holder.add_child(lift)
	_set_piece_mesh(holder, letter)
	_world.add_child(holder)
	return holder


func _set_piece_mesh(holder: Node3D, letter: String) -> void:
	var lift := holder.get_node("Lift") as Node3D
	for child in lift.get_children():
		child.queue_free()
	var template: Node3D = _templates.get(letter)
	if template != null:
		var mesh := template.duplicate() as Node3D
		mesh.transform = Transform3D.IDENTITY
		if letter == letter.to_lower():
			mesh.rotation.y = PI
		lift.add_child(mesh)
	holder.set_meta("piece", letter)
	holder.set_meta("lift", 0.0)


# --- Synchronisation et animations ---------------------------------------------------


func _sync() -> void:
	_sync_queued = false
	if _pieces.size() != 64:
		return
	var old := _nodes
	var fresh := {}
	var used := {}
	var mover: Node3D = null
	var captured_any := false
	if _pending_from >= 0 and old.has(_pending_from) and _pieces[_pending_to] != "":
		mover = old[_pending_from]
		fresh[_pending_to] = mover
		used[mover] = true
	for square in 64:
		if fresh.has(square) or _pieces[square] == "" or not old.has(square):
			continue
		var holder: Node3D = old[square]
		if not used.has(holder) and holder.get_meta("piece") == _pieces[square]:
			fresh[square] = holder
			used[holder] = true
	for square in 64:
		if fresh.has(square) or _pieces[square] == "":
			continue
		var best: Node3D = null
		var best_distance := INF
		for old_square in old:
			var candidate: Node3D = old[old_square]
			if used.has(candidate) or candidate.get_meta("piece") != _pieces[square]:
				continue
			var distance := candidate.position.distance_to(_square_pos(square))
			if distance < best_distance:
				best_distance = distance
				best = candidate
		if best != null:
			fresh[square] = best
			used[best] = true
	for old_square in old:
		var leftover: Node3D = old[old_square]
		if not used.has(leftover):
			captured_any = true
			_animate_capture(leftover, mover)
	for square in 64:
		if _pieces[square] != "" and not fresh.has(square):
			var spawned := _make_piece(_pieces[square])
			spawned.position = _square_pos(square) + Vector3(0, 1.2, 0)
			spawned.scale = Vector3.ONE * 0.01
			fresh[square] = spawned
			var tween := _new_tween().set_parallel(true)
			tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			tween.tween_property(spawned, "position", _square_pos(square), 0.45 * slow_factor)
			tween.tween_property(spawned, "scale", Vector3.ONE, 0.45 * slow_factor)
	_nodes = fresh
	var moved := false
	for square in fresh:
		var holder: Node3D = fresh[square]
		if holder.get_meta("piece") != _pieces[square]:
			_promote_after_landing(holder, _pieces[square], holder == mover)
		if holder.position.distance_to(_square_pos(square)) > 0.02:
			moved = true
			_animate_travel(holder, _square_pos(square), holder == mover, captured_any)
	if moved or captured_any:
		_play("capture" if captured_any else "move", _travel_time(1.0, captured_any) * 0.92)
	_pending_from = -1
	_pending_to = -1


func _travel_time(distance: float, capture: bool) -> float:
	var base := 0.34 + 0.06 * minf(distance, 6.0)
	if capture:
		base *= 1.45  # ralenti sur l'impact
	return base * slow_factor


func _animate_travel(holder: Node3D, target: Vector3, main: bool, capture: bool) -> void:
	_kill_tween(holder)
	var start := holder.position
	start.y = 0.0
	var distance := start.distance_to(target)
	var knight := String(holder.get_meta("piece")).to_lower() == "n"
	var height := 0.25 + distance * 0.12
	if knight:
		height = 1.1
	if _dragging or not main:
		height *= 0.4
	var duration := _travel_time(distance, capture and main)
	var tween := _new_tween()
	holder.set_meta("tween", tween)
	tween.tween_method(
		func(t: float) -> void:
			var eased := t * t * (3.0 - 2.0 * t)
			var pos := start.lerp(target, eased)
			pos.y = sin(t * PI) * height
			holder.position = pos,
		0.0,
		1.0,
		duration
	)
	var lift := holder.get_node("Lift") as Node3D
	tween.tween_property(lift, "scale", Vector3(1.1, 0.86, 1.1), 0.06 * slow_factor)
	tween.tween_property(lift, "scale", Vector3.ONE, 0.32 * slow_factor).set_trans(
		Tween.TRANS_ELASTIC
	).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_callback(_spawn_dust.bind(target, capture))


func _animate_capture(victim: Node3D, attacker: Node3D) -> void:
	_kill_tween(victim)
	var away := Vector3(0.6, 0, 0.4)
	if attacker != null:
		away = victim.position - attacker.position
		away.y = 0.0
		away = away.normalized() if away.length() > 0.01 else Vector3.RIGHT
	var impact_delay := _travel_time(1.0, true) * 0.85
	var axis := Vector3.UP.cross(away).normalized()
	if axis.length() < 0.1:
		axis = Vector3.RIGHT
	var start_basis := victim.basis
	var start_pos := victim.position
	var tween := _new_tween()
	tween.tween_interval(impact_delay)
	tween.tween_method(
		func(t: float) -> void:
			var eased := 1.0 - pow(1.0 - t, 2.0)
			victim.basis = start_basis.rotated(axis, eased * deg_to_rad(95.0))
			victim.position = start_pos + away * eased * 0.9 + Vector3(0, sin(t * PI) * 0.35, 0),
		0.0,
		1.0,
		0.9 * slow_factor
	)
	tween.tween_property(victim, "scale", Vector3.ONE * 0.01, 0.45 * slow_factor).set_trans(
		Tween.TRANS_BACK
	).set_ease(Tween.EASE_IN)
	tween.tween_callback(victim.queue_free)
	# Petite poussée de caméra au moment de l'impact.
	var punch := _new_tween()
	punch.tween_interval(impact_delay)
	punch.tween_property(_camera, "fov", 33.0, 0.12 * slow_factor)
	punch.tween_property(_camera, "fov", 36.0, 0.6 * slow_factor).set_trans(Tween.TRANS_SINE)


func _promote_after_landing(holder: Node3D, letter: String, main: bool) -> void:
	var tween := _new_tween()
	tween.tween_interval(_travel_time(1.0, false) if main else 0.0)
	tween.tween_callback(_set_piece_mesh.bind(holder, letter))
	tween.tween_callback(_spawn_dust.bind(holder.position, true))


func _spawn_dust(at: Vector3, strong: bool) -> void:
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.30
	torus.outer_radius = 0.36
	ring.mesh = torus
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(1.0, 0.85, 0.55, 0.75) if strong else Color(1, 1, 1, 0.4)
	ring.material_override = mat
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ring.position = Vector3(at.x, 0.02, at.z)
	ring.scale = Vector3(0.6, 0.15, 0.6)
	_world.add_child(ring)
	var tween := _new_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	var grow := 2.2 if strong else 1.5
	tween.tween_property(ring, "scale", Vector3(grow, 0.15, grow), 0.55 * slow_factor)
	tween.tween_property(mat, "albedo_color:a", 0.0, 0.55 * slow_factor)
	tween.chain().tween_callback(ring.queue_free)


func _new_tween() -> Tween:
	var tween := create_tween()
	tween.set_speed_scale(_time_scale)
	_tweens.append(tween)
	return tween


func _kill_tween(holder: Node3D) -> void:
	if holder.has_meta("tween"):
		var previous: Tween = holder.get_meta("tween")
		if previous != null and previous.is_valid():
			previous.kill()
		holder.remove_meta("tween")


func _play(key: String, delay: float) -> void:
	var player: AudioStreamPlayer = _players.get(key)
	if player == null:
		return
	if delay <= 0.0:
		player.play()
		return
	get_tree().create_timer(delay / maxf(_time_scale, 0.05)).timeout.connect(player.play)


# --- Marqueurs, survol, caméra --------------------------------------------------------


func _refresh_markers() -> void:
	if _overlays.size() != 64:
		return
	for marker in _markers:
		marker.queue_free()
	_markers.clear()
	for move in _targets:
		var target: int = move.to
		var occupied = _pieces.size() == 64 and _pieces[target] != ""
		var marker := MeshInstance3D.new()
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color = Color(1.0, 0.78, 0.35, 0.85)
		if occupied:
			var torus := TorusMesh.new()
			torus.inner_radius = 0.40
			torus.outer_radius = 0.47
			marker.mesh = torus
		else:
			var dot := CylinderMesh.new()
			dot.top_radius = 0.13
			dot.bottom_radius = 0.13
			dot.height = 0.02
			marker.mesh = dot
		marker.material_override = mat
		marker.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		marker.position = _square_pos(target) + Vector3(0, 0.02, 0)
		marker.scale = Vector3.ONE * 0.01
		_world.add_child(marker)
		_markers.append(marker)
		var tween := _new_tween()
		tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(marker, "scale", Vector3(1, 0.3 if occupied else 1.0, 1), 0.22)


func _process(delta: float) -> void:
	var scaled := delta * _time_scale
	_time += scaled
	for tween in _tweens.duplicate():
		if not tween.is_valid():
			_tweens.erase(tween)
		else:
			tween.set_speed_scale(_time_scale)
	_update_overlays()
	_update_lifts(scaled)
	if showcase:
		_run_demo(scaled)
	_update_camera(scaled)


func _update_overlays() -> void:
	if _overlays.size() != 64:
		return
	var pulse := 0.5 + 0.5 * sin(_time * 5.0)
	for square in 64:
		var color := Color(1, 1, 1, 0)
		if square == _last_move.x or square == _last_move.y:
			color = Color(0.95, 0.72, 0.30, 0.30)
		if square == _hover and not showcase:
			color = Color(1, 0.95, 0.8, 0.16 + color.a)
		if square == _selected:
			color = Color(1.0, 0.78, 0.32, 0.50)
		if square == _checked:
			color = Color(0.95, 0.12, 0.08, 0.30 + 0.30 * pulse)
		if square == _hint_from or square == _hint_to:
			color = Color(0.15, 0.85, 0.98, 0.45 + 0.35 * pulse)
		var mat := _overlays[square].material_override as StandardMaterial3D
		mat.albedo_color = mat.albedo_color.lerp(color, 0.25)
	if _checked >= 0:
		_check_light.position = _square_pos(_checked) + Vector3(0, 1.0, 0)
		_check_light.light_energy = 1.2 + 1.8 * pulse
	else:
		_check_light.light_energy = move_toward(_check_light.light_energy, 0.0, 0.2)


func _update_lifts(delta: float) -> void:
	for square in _nodes:
		var holder: Node3D = _nodes[square]
		var lift := holder.get_node("Lift") as Node3D
		var target := 0.0
		if square == _selected:
			target = 0.32 + sin(_time * 3.2) * 0.04
		elif square == _hover and not showcase:
			target = 0.07
		if _dragging and square == _press_square:
			target = 0.55
			holder.position = holder.position.lerp(Vector3(_drag_point.x, 0, _drag_point.z), 0.45)
		lift.position.y = lerpf(lift.position.y, target, clampf(delta * 14.0, 0.0, 1.0))


func _update_camera(delta: float) -> void:
	if _camera == null:
		return
	var yaw := _cam_yaw
	var pitch := _cam_pitch
	var distance := _cam_distance
	if showcase:
		_cam_yaw += delta * 0.09
		pitch += sin(_time * 0.21) * 0.05
	else:
		yaw += sin(_time * 0.35) * 0.012
		pitch += sin(_time * 0.27) * 0.006
		if _intro > 0.0:
			_intro = maxf(0.0, _intro - delta / 1.8)
			var k := _intro * _intro * (3.0 - 2.0 * _intro)
			yaw += k * deg_to_rad(-70.0)
			pitch += k * deg_to_rad(18.0)
			distance += k * 7.0
	var offset := Vector3(
		sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)
	) * distance
	_camera.position = _cam_target + offset
	_camera.look_at(_cam_target, Vector3.UP)


func _run_demo(delta: float) -> void:
	_demo_timer -= delta
	if _demo_timer > 0.0:
		return
	if _demo_index >= SHOWCASE_GAME.size():
		_demo.new_game()
		_demo_index = 0
		_game_over_square = -1
		_cam_target = Vector3.ZERO
		_cam_distance = 11.0
		set_board_state(_demo.board, -1, [], Vector2i(-1, -1), -1)
		_demo_timer = 2.5
		return
	var uci: String = SHOWCASE_GAME[_demo_index]
	_demo_index += 1
	var from_square := _demo.square_from_name(uci.substr(0, 2))
	var to_square := _demo.square_from_name(uci.substr(2, 2))
	if not _demo.play_uci(uci):
		_demo_index = SHOWCASE_GAME.size()
		return
	animate_move(from_square, to_square, _demo.board[to_square])
	var king := _demo.board.find("K" if _demo.white_to_move else "k")
	set_board_state(
		_demo.board, -1, [], Vector2i(from_square, to_square),
		king if _demo.is_in_check() else -1
	)
	_demo_timer = 2.4 * slow_factor * 0.6
	if _demo.game_status() == "checkmate":
		play_game_over.call_deferred(king)
		_demo_timer = 7.0


# --- Entrées : clic, survol, glisser-déposer ----------------------------------------


func _gui_input(event: InputEvent) -> void:
	if showcase:
		return
	if event is InputEventMouseMotion:
		var hit := _pick(event.position)
		_hover = _square_at(hit)
		if (event.button_mask & MOUSE_BUTTON_MASK_LEFT) and _press_square >= 0:
			if not _dragging and event.position.distance_to(_press_pos) > 8.0:
				_dragging = _press_square == _selected and _nodes.has(_press_square)
			if _dragging:
				_drag_point = hit
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var square := _square_at(_pick(event.position))
		if event.pressed:
			_press_square = square
			_press_pos = event.position
			_dragging = false
			if square >= 0:
				square_pressed.emit(square)
		else:
			var was_dragging := _dragging
			if was_dragging and square >= 0 and square != _press_square:
				square_pressed.emit(square)
			_dragging = false
			_press_square = -1
			if was_dragging and not _sync_queued:
				_sync_queued = true
				_sync.call_deferred()
		accept_event()


func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_EXIT:
		_hover = -1


func _pick(point: Vector2) -> Vector3:
	if _camera == null:
		return Vector3(INF, 0, INF)
	var view_point := point
	if size.x > 0.0 and size.y > 0.0:
		view_point = point * Vector2(_viewport.size) / size
	var origin := _camera.project_ray_origin(view_point)
	var normal := _camera.project_ray_normal(view_point)
	if absf(normal.y) < 0.0001:
		return Vector3(INF, 0, INF)
	var t := -origin.y / normal.y
	return origin + normal * t


func _square_at(hit: Vector3) -> int:
	var file := int(floor(hit.x + 4.0))
	var row := int(floor(hit.z + 4.0))
	if file < 0 or file > 7 or row < 0 or row > 7:
		return -1
	return row * 8 + file


func _square_pos(square: int) -> Vector3:
	return Vector3((square % 8) - 3.5, 0.0, int(square / 8) - 3.5)
