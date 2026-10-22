extends Control
## Routeur du premier client Godot. Le cœur historique Pygame reste intact.

const HOME := preload("res://ui/home_screen.tscn")
const GAME := preload("res://ui/game_screen.tscn")
const NEARBY := preload("res://ui/nearby_screen.gd")
const LanTransport := preload("res://net/lan_chess_transport.gd")

var _screen: Control
var _mode := "local"
var _lan: LanChessTransport


func _ready() -> void:
	_lan = LanTransport.new()
	_lan.name = "LanChessTransport"
	add_child(_lan)
	_lan.session_started.connect(_on_lan_session_started)
	_show_home(false)


func _show_home(animated := true) -> void:
	var home := HOME.instantiate()
	home.ai_game_requested.connect(func() -> void: _show_game("ai"))
	home.local_pass_and_play_requested.connect(func() -> void: _show_game("local"))
	home.nearby_game_requested.connect(_show_nearby_screen)
	_replace_screen(home, animated)


func _show_game(mode: String) -> void:
	_mode = mode
	var game := GAME.instantiate()
	game.configure(mode)
	game.back_requested.connect(_leave_game)
	game.nearby_requested.connect(_show_nearby_screen)
	_replace_screen(game, true)
	if mode == "nearby":
		game.set_lan_transport(_lan, _lan.local_is_white())


func _show_nearby_screen() -> void:
	_lan.close_session()
	var page := NEARBY.new()
	page.back_requested.connect(
		func() -> void:
			_lan.close_session()
			_lan.stop_discovery()
			_show_home()
	)
	page.room_join_requested.connect(func(room: Dictionary) -> void: _lan.join_room(room))
	_replace_screen(page, true)
	page.set_transport(_lan)


func _on_lan_session_started(_local_is_white: bool, _initial_fen: String) -> void:
	_show_game("nearby")


func _leave_game() -> void:
	if _mode == "nearby":
		_lan.close_session()
		_lan.stop_discovery()
	_show_home()


func _replace_screen(next: Control, animated: bool) -> void:
	if is_instance_valid(_screen):
		var old := _screen
		if animated:
			var fade := create_tween()
			fade.tween_property(old, "modulate:a", 0.0, 0.3)
			await fade.finished
			if not is_instance_valid(old):
				return
		remove_child(old)
		old.queue_free()
	_screen = next
	_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_screen.modulate.a = 0.0 if animated else 1.0
	add_child(_screen)
	if animated:
		var fade_in := create_tween()
		(
			fade_in
			. tween_property(_screen, "modulate:a", 1.0, 0.8)
			. set_trans(Tween.TRANS_CUBIC)
			. set_ease(Tween.EASE_OUT)
		)
