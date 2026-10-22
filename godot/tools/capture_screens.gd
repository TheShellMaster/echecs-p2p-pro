extends SceneTree
## Outil de captures d'écran : menu, partie, sélection, coup en arc, réponse de l'IA.
## Usage depuis la racine : godot --path godot --script res://tools/capture_screens.gd
## Les images sont écrites dans docs/images/captures/ (nécessite un affichage, pas --headless).
var OUT := ProjectSettings.globalize_path("res://").path_join("../docs/images/captures/").simplify_path() + "/"
func _initialize() -> void:
	_run.call_deferred()
func _wait(sec: float) -> void:
	await create_timer(sec).timeout
func _shot(name: String) -> void:
	await process_frame
	root.get_texture().get_image().save_png(OUT + name + ".png")
	print("shot ", name)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var app = load("res://app.tscn").instantiate()
	root.add_child(app)
	await _wait(1.0); await _shot("1_menu_entree")
	await _wait(5.0); await _shot("2_menu")
	var home = app._screen
	home.ai_game_requested.emit()
	await _wait(3.0); await _shot("3_partie")
	var game = app._screen
	game._on_square_pressed(52)  # e2
	await _wait(0.6); await _shot("4_selection")
	game._on_square_pressed(36)  # e4
	await _wait(0.2); await _shot("5_arc")
	await _wait(3.0); await _shot("6_apres_ia")
	quit()
