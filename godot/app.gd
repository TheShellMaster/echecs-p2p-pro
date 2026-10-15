extends Control
## Routeur du premier client Godot. Le cœur historique Pygame reste intact.

const HOME := preload("res://ui/home_screen.tscn")
const GAME := preload("res://ui/game_screen.tscn")

var _screen: Control
var _mode := "local"


func _ready() -> void:
	_show_home(false)


func _show_home(animated := true) -> void:
	var home := HOME.instantiate()
	home.ai_game_requested.connect(func() -> void: _show_game("ai"))
	home.local_pass_and_play_requested.connect(func() -> void: _show_game("local"))
	home.nearby_game_requested.connect(_show_nearby_notice)
	_replace_screen(home, animated)


func _show_game(mode: String) -> void:
	_mode = mode
	var game := GAME.instantiate()
	game.configure(mode)
	game.back_requested.connect(func() -> void: _show_home())
	game.nearby_requested.connect(_show_nearby_notice)
	_replace_screen(game, true)


func _show_nearby_notice() -> void:
	# Nearby transport is being integrated as a distinct offline feature. Do not
	# silently open a local board and imply that another device has connected.
	var page := Control.new()
	var bg := ColorRect.new()
	bg.color = Color("#f5f1e8")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	page.add_child(bg)
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	box.custom_minimum_size = Vector2(420, 170)
	box.add_theme_constant_override("separation", 16)
	page.add_child(box)
	var heading := Label.new()
	heading.text = "Jouer à proximité"
	heading.add_theme_font_size_override("font_size", 27)
	heading.add_theme_color_override("font_color", Color("#263b33"))
	box.add_child(heading)
	var copy := Label.new()
	copy.text = (
		"La partie locale est prête. La découverte entre appareils n’est pas encore raccordée "
		+ "dans ce nouveau client."
	)
	copy.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	copy.add_theme_color_override("font_color", Color("#687a70"))
	box.add_child(copy)
	var back := Button.new()
	back.text = "Retour"
	back.pressed.connect(func() -> void: _show_home())
	box.add_child(back)
	_replace_screen(page, true)


func _replace_screen(next: Control, animated: bool) -> void:
	if is_instance_valid(_screen):
		var old := _screen
		if animated:
			var fade := create_tween()
			fade.tween_property(old, "modulate:a", 0.0, 0.12)
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
			. tween_property(_screen, "modulate:a", 1.0, 0.22)
			. set_trans(Tween.TRANS_CUBIC)
			. set_ease(Tween.EASE_OUT)
		)
