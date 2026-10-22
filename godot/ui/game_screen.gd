class_name ChessGameScreen
extends Control
## Écran de partie hors ligne. Le transport réseau reste à la charge du parent.

signal back_requested
signal nearby_requested

const ChessRules = preload("res://core/chess_game.gd")
const Board3DScript = preload("res://ui/board_3d.gd")
const ChessAIScript = preload("res://core/chess_ai.gd")
const PIECES := {
	"P": preload("res://assets/wP.png"),
	"N": preload("res://assets/wN.png"),
	"B": preload("res://assets/wB.png"),
	"R": preload("res://assets/wR.png"),
	"Q": preload("res://assets/wQ.png"),
	"K": preload("res://assets/wK.png"),
	"p": preload("res://assets/bP.png"),
	"n": preload("res://assets/bN.png"),
	"b": preload("res://assets/bB.png"),
	"r": preload("res://assets/bR.png"),
	"q": preload("res://assets/bQ.png"),
	"k": preload("res://assets/bK.png"),
}
const INK := Color("#f1e9d8")
const MUTED := Color("#a29a8a")
const GREEN := Color("#d1a24f")
const CREAM := Color("#0d0f0e")
const PAPER := Color(0.08, 0.075, 0.07, 0.86)
const BORDER := Color(1.0, 0.85, 0.55, 0.16)
const DARK_TEXT := Color("#1a1510")
const PIECE_VALUE := {"p": 100, "n": 320, "b": 335, "r": 500, "q": 900, "k": 20000}

var game: ChessGame
var play_mode := "local"  # "ai", "local" ou "nearby"
var _selected := -1
var _legal_for_selection: Array = []
var _last_move := Vector2i(-1, -1)
var _thinking := false
var _compact := false
var _has_layout := false
var _root: VBoxContainer
var _board
var _game_over_shown := false
var _status: Label
var _turn: Label
var _history: Label
var _undo_button: Button
var _new_game_button: Button
var _nearby_button: Button
var _note: Label
var _lan_transport: LanChessTransport
var _local_is_white := true
var _ai: RefCounted
var _ai_level := 2
var _engine_label: Label
var _level_option: OptionButton
var _hint_button: Button
var _coach_button: Button
var _coach_box: PanelContainer
var _coach_label: Label


func _ready() -> void:
	game = ChessRules.new()
	_ai = ChessAIScript.new()
	_build()
	get_viewport().size_changed.connect(_refresh_layout)
	_refresh_layout()
	_refresh()


## Parent: appeler avant l'ajout à l'arbre si le mode n'est pas local.
func configure(mode: String) -> void:
	if mode in ["ai", "local", "nearby"]:
		play_mode = mode
	if is_instance_valid(_level_option):
		_level_option.visible = play_mode == "ai"
	if is_instance_valid(_engine_label):
		_engine_label.visible = play_mode == "ai"
	if is_instance_valid(_hint_button):
		_hint_button.visible = play_mode != "nearby"
	if is_instance_valid(_coach_button):
		_coach_button.visible = play_mode != "nearby"


func start_new_game(mode: String = "") -> void:
	if not mode.is_empty() and mode in ["ai", "local", "nearby"]:
		play_mode = mode
	game.new_game()
	_selected = -1
	_legal_for_selection.clear()
	_last_move = Vector2i(-1, -1)
	_game_over_shown = false
	if is_instance_valid(_board):
		_board.clear_hint()
	if is_instance_valid(_coach_label):
		_coach_label.text = ""
	if is_instance_valid(_coach_box):
		_coach_box.visible = false
	_refresh()


func set_lan_transport(transport: LanChessTransport, local_is_white: bool) -> void:
	_lan_transport = transport
	_local_is_white = local_is_white
	if is_instance_valid(_lan_transport):
		_lan_transport.remote_move_received.connect(_on_remote_move)
		_lan_transport.session_ended.connect(_on_lan_session_ended)
		if is_instance_valid(_status) and _lan_transport.is_session_active():
			_status.text = "Partie locale connectée."


func _build() -> void:
	var background := ColorRect.new()
	background.color = CREAM
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)
	_root = VBoxContainer.new()
	_root.add_theme_constant_override("separation", 16)
	margin.add_child(_root)
	_root.add_child(_build_header())
	var content := BoxContainer.new()
	content.name = "GameContent"
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 24)
	_root.add_child(content)
	_board = Board3DScript.new()
	_board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_board.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_board.square_pressed.connect(_on_square_pressed)
	content.add_child(_board)
	content.add_child(_build_side_panel())


func _build_header() -> Control:
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	var back := _button("‹  Menu", false)
	back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	back.custom_minimum_size.x = 120
	back.pressed.connect(func() -> void: back_requested.emit())
	header.add_child(back)
	var brand := VBoxContainer.new()
	brand.add_theme_constant_override("separation", 0)
	var title := _label("ÉCHECS", 15, INK)
	brand.add_child(title)
	brand.add_child(_label("UNE PARTIE, À VOTRE RYTHME", 10, MUTED))
	header.add_child(brand)
	header.add_spacer(false)
	var offline := _label("●  HORS LIGNE", 11, GREEN)
	header.add_child(offline)
	return header


func _build_side_panel() -> Control:
	var card := PanelContainer.new()
	card.name = "GamePanel"
	card.custom_minimum_size = Vector2(320, 0)
	card.size_flags_horizontal = Control.SIZE_FILL
	card.add_theme_stylebox_override("panel", _panel_style(PAPER, BORDER, 20))
	var inset := MarginContainer.new()
	inset.add_theme_constant_override("margin_left", 18)
	inset.add_theme_constant_override("margin_right", 18)
	inset.add_theme_constant_override("margin_top", 18)
	inset.add_theme_constant_override("margin_bottom", 18)
	card.add_child(inset)
	
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	inset.add_child(scroll)
	
	var stack := VBoxContainer.new()
	stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stack.add_theme_constant_override("separation", 10)
	scroll.add_child(stack)
	
	_turn = _label("BLANCS", 11, GREEN)
	stack.add_child(_turn)
	_status = _label("À vous de jouer.", 21, INK)
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(_status)
	
	# Moteur et sélection du niveau d'IA
	_engine_label = _label("●  " + _ai.get_engine_name(), 10, GREEN)
	_engine_label.visible = play_mode == "ai"
	stack.add_child(_engine_label)
	
	_level_option = OptionButton.new()
	_level_option.custom_minimum_size = Vector2(0, 36)
	_level_option.add_item("Niveau 1 · Débutant (800)")
	_level_option.add_item("Niveau 2 · Intermédiaire (1400)")
	_level_option.add_item("Niveau 3 · Avancé (1900)")
	_level_option.add_item("Niveau 4 · Grand Maître (2500)")
	_level_option.selected = _ai_level - 1
	_level_option.item_selected.connect(func(idx: int) -> void: _ai_level = idx + 1)
	_level_option.add_theme_color_override("font_color", INK)
	_level_option.add_theme_stylebox_override("normal", _panel_style(Color(1, 1, 1, 0.05), BORDER, 8))
	_level_option.visible = play_mode == "ai"
	stack.add_child(_level_option)
	
	# Outils d'apprentissage : Indice et Coach
	var train_row := HBoxContainer.new()
	train_row.add_theme_constant_override("separation", 8)
	_hint_button = _button("✦  Indice", false)
	_hint_button.pressed.connect(_on_hint_pressed)
	_hint_button.visible = play_mode != "nearby"
	_coach_button = _button("◈  Coach", false)
	_coach_button.pressed.connect(_on_coach_pressed)
	_coach_button.visible = play_mode != "nearby"
	train_row.add_child(_hint_button)
	train_row.add_child(_coach_button)
	stack.add_child(train_row)
	
	_coach_box = PanelContainer.new()
	_coach_box.add_theme_stylebox_override("panel", _panel_style(Color(0.12, 0.16, 0.15, 0.8), Color(0.2, 0.85, 0.95, 0.35), 10))
	_coach_box.visible = false
	var coach_inset := MarginContainer.new()
	coach_inset.add_theme_constant_override("margin_left", 12)
	coach_inset.add_theme_constant_override("margin_right", 12)
	coach_inset.add_theme_constant_override("margin_top", 10)
	coach_inset.add_theme_constant_override("margin_bottom", 10)
	_coach_box.add_child(coach_inset)
	_coach_label = _label("", 12, INK)
	_coach_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	coach_inset.add_child(_coach_label)
	stack.add_child(_coach_box)
	
	var separator := HSeparator.new()
	stack.add_child(separator)
	
	stack.add_child(_label("COUPS JOUÉS", 10, MUTED))
	_history = _label("La partie commence.", 13, INK)
	_history.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_history.custom_minimum_size.y = 60
	stack.add_child(_history)
	
	_undo_button = _button("↶  Annuler le dernier coup", false)
	_undo_button.pressed.connect(_undo)
	stack.add_child(_undo_button)
	
	_new_game_button = _button("Nouvelle partie", true)
	_new_game_button.pressed.connect(func() -> void: start_new_game())
	stack.add_child(_new_game_button)
	
	_nearby_button = _button("Joueur à proximité", false)
	_nearby_button.pressed.connect(func() -> void: nearby_requested.emit())
	stack.add_child(_nearby_button)
	
	_note = _label("Votre partie reste sur cet appareil.", 10, MUTED)
	_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(_note)
	return card


func _on_hint_pressed() -> void:
	if _thinking or _is_finished():
		return
	var hint: Dictionary = _ai.get_hint(game)
	if hint.is_empty():
		return
	if is_instance_valid(_board):
		_board.set_hint(hint.from, hint.to)
	_coach_box.visible = true
	_coach_label.text = "✦ Indice : %s" % hint.explanation


func _on_coach_pressed() -> void:
	if _thinking or _is_finished():
		return
	var eval: Dictionary = _ai.get_coach_evaluation(game, _local_is_white)
	_coach_box.visible = true
	_coach_label.text = "🎓 %s
%s" % [eval.balance, "\n".join(eval.advice)]


func _refresh_layout() -> void:
	var narrow := get_viewport_rect().size.x < 820.0
	if _has_layout and _compact == narrow:
		return
	_has_layout = true
	_compact = narrow
	if not is_instance_valid(_root):
		return
	var content := _root.get_node("GameContent") as BoxContainer
	content.vertical = narrow
	content.add_theme_constant_override("separation", 12 if narrow else 24)
	var panel := content.get_node("GamePanel") as PanelContainer
	panel.custom_minimum_size = Vector2(0 if narrow else 290, 250 if narrow else 0)
	var board_side := minf(
		get_viewport_rect().size.x - (48 if narrow else 380),
		get_viewport_rect().size.y * (0.54 if narrow else 0.78)
	)
	_board.custom_minimum_size = Vector2(maxf(240, board_side), maxf(240, board_side))


func _on_square_pressed(square: int) -> void:
	if is_instance_valid(_board):
		_board.clear_hint()
	if _thinking or _is_finished():
		return
	if play_mode == "nearby":
		if not is_instance_valid(_lan_transport) or not _lan_transport.is_session_active():
			return
		if game.white_to_move != _local_is_white:
			return
	if _selected >= 0:
		for move in _legal_for_selection:
			if move.to == square:
				var uci: String = game.move_to_uci(move)
				var moving_piece: String = game.board[_selected]
				if String(move.get("promotion", "")) != "":
					uci = uci.substr(0, 4) + "q"
				var ply := game.get_uci_history().size()
				if game.play_uci(uci):
					if play_mode == "nearby" and not _lan_transport.send_move(uci, ply):
						game.undo()
						_selected = -1
						_legal_for_selection.clear()
						_refresh()
						return
					_last_move = Vector2i(_selected, square)
					if uci.length() == 5:
						moving_piece = "Q" if moving_piece == "P" else "q"
					_board.animate_move(_selected, square, moving_piece)
				_selected = -1
				_legal_for_selection.clear()
				_refresh()
				if play_mode == "ai" and not _is_finished() and not game.white_to_move:
					_play_ai_turn()
				return
	var piece: String = game.board[square]
	if (
		piece != ""
		and (piece == piece.to_upper()) == game.white_to_move
		and (play_mode != "ai" or game.white_to_move)
	):
		_selected = square
		_legal_for_selection = game.legal_moves(square)
	else:
		_selected = -1
		_legal_for_selection.clear()
	_board.set_board_state(game.board, _selected, _legal_for_selection, _last_move, (
		game.board.find("K" if game.white_to_move else "k") if game.is_in_check() else -1
	))


func _undo() -> void:
	if _thinking or play_mode == "nearby":
		return
	if game.undo():
		if play_mode == "ai" and not game.white_to_move:
			game.undo()
		var history := game.get_uci_history()
		_last_move = Vector2i(-1, -1)
		if not history.is_empty():
			var last: String = history[-1]
			_last_move = Vector2i(
				game.square_from_name(last.substr(0, 2)), game.square_from_name(last.substr(2, 2))
			)
		_selected = -1
		_refresh()


func _refresh() -> void:
	if not is_instance_valid(_board):
		return
	var status: String = game.game_status()
	_new_game_button.disabled = play_mode == "nearby"
	_nearby_button.visible = play_mode != "nearby"
	_note.text = (
		"Partie directe sur le réseau local."
		if play_mode == "nearby"
		else "Votre partie reste sur cet appareil."
	)
	var terminal := (
		status
		in [
			"checkmate",
			"stalemate",
			"draw_seventy_five_move",
			"draw_fivefold_repetition",
			"draw_insufficient_material"
		]
	)
	_turn.text = "BLANCS À JOUER" if game.white_to_move else "NOIRS À JOUER"
	if _thinking:
		_status.text = "L’adversaire réfléchit…"
	elif status == "checkmate":
		_status.text = "Échec et mat."
	elif status == "stalemate":
		_status.text = "Partie nulle."
	elif status.begins_with("draw_"):
		_status.text = "Partie nulle."
	elif status == "check":
		_status.text = "Échec ! À vous de répondre."
	elif play_mode == "nearby" and game.white_to_move != _local_is_white:
		_status.text = "À l’adversaire de jouer…"
	else:
		_status.text = "À vous de jouer." if not terminal else "Partie terminée."
	var sans := game.get_san_history()
	var lines := PackedStringArray()
	for index in range(0, sans.size(), 2):
		var move_number := str(int(index / 2) + 1) + "."
		var line := move_number + "  " + sans[index]
		if index + 1 < sans.size():
			line += "     " + sans[index + 1]
		lines.append(line)
	_history.text = "\n".join(lines) if not lines.is_empty() else "La partie commence."
	_undo_button.disabled = (
		game.get_uci_history().is_empty() or _thinking or play_mode == "nearby"
	)
	var checked_king := (
		game.board.find("K" if game.white_to_move else "k") if game.is_in_check() else -1
	)
	_board.set_board_state(game.board, _selected, _legal_for_selection, _last_move, checked_king)
	if status == "checkmate" and not _game_over_shown:
		_game_over_shown = true
		_board.play_game_over(game.board.find("K" if game.white_to_move else "k"))


func _on_remote_move(uci: String, ply: int) -> void:
	if play_mode != "nearby" or ply != game.get_uci_history().size():
		if is_instance_valid(_lan_transport):
			_lan_transport.close_session("Séquence de coups invalide. Partie locale arrêtée.")
		return
	var from_square := game.square_from_name(uci.substr(0, 2))
	var to_square := game.square_from_name(uci.substr(2, 2))
	if from_square < 0 or to_square < 0 or not game.play_uci(uci):
		if is_instance_valid(_lan_transport):
			_lan_transport.close_session("Coup reçu illégal. Partie locale arrêtée.")
		return
	_board.animate_move(from_square, to_square, game.board[to_square])
	_last_move = Vector2i(from_square, to_square)
	_selected = -1
	_legal_for_selection.clear()
	_refresh()


func _on_lan_session_ended(reason: String) -> void:
	if play_mode == "nearby" and is_instance_valid(_status):
		_status.text = reason


func _is_finished() -> bool:
	return (
		game.game_status()
		in [
			"checkmate",
			"stalemate",
			"draw_seventy_five_move",
			"draw_fivefold_repetition",
			"draw_insufficient_material"
		]
	)


func _play_ai_turn() -> void:
	_thinking = true
	_refresh()
	# Laisse la pièce du joueur atterrir avant la réponse de l'IA.
	await get_tree().create_timer(0.6).timeout
	if not is_inside_tree():
		return
	var best_uci: String = _ai.get_best_move(game, _ai_level)
	var moving_piece := ""
	var from_square := -1
	var to_square := -1
	if not best_uci.is_empty() and game.play_uci(best_uci):
		from_square = game.square_from_name(best_uci.substr(0, 2))
		to_square = game.square_from_name(best_uci.substr(2, 2))
		moving_piece = game.board[to_square]
		_last_move = Vector2i(from_square, to_square)
	_thinking = false
	_refresh()
	if from_square >= 0 and to_square >= 0:
		_board.animate_move(from_square, to_square, moving_piece)


## Minimax alpha-bêta déterministe, évalué du point de vue des Blancs.
## Profondeur 2: pensée courte pour ne pas immobiliser l'interface.
func _choose_ai_move(position: ChessGame, depth: int) -> String:
	var moves := position.legal_moves()
	if moves.is_empty():
		return ""
	moves.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			return _move_order_score(position, a) > _move_order_score(position, b)
	)
	var maximizing := position.white_to_move
	var best_score := -INF if maximizing else INF
	var best_uci := ""
	var alpha := -INF
	var beta := INF
	for move in moves:
		var child := ChessRules.new(position.to_fen())
		var uci: String = position.move_to_uci(move)
		if not child.play_uci(uci):
			continue
		var score := _minimax(child, depth - 1, alpha, beta)
		if (maximizing and score > best_score) or (not maximizing and score < best_score):
			best_score = score
			best_uci = uci
		if maximizing:
			alpha = maxf(alpha, best_score)
		else:
			beta = minf(beta, best_score)
	return best_uci


func _minimax(position: ChessGame, depth: int, alpha_in: float, beta_in: float) -> float:
	if depth <= 0:
		return _evaluate(position)
	var moves := position.legal_moves()
	if moves.is_empty():
		if position.is_in_check(position.white_to_move):
			return 100000.0 if not position.white_to_move else -100000.0
		return 0.0
	moves.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			return _move_order_score(position, a) > _move_order_score(position, b)
	)
	var maximizing := position.white_to_move
	var alpha := alpha_in
	var beta := beta_in
	var best := -INF if maximizing else INF
	for move in moves:
		var child := ChessRules.new(position.to_fen())
		if not child.play_uci(position.move_to_uci(move)):
			continue
		var score := _minimax(child, depth - 1, alpha, beta)
		best = maxf(best, score) if maximizing else minf(best, score)
		if maximizing:
			alpha = maxf(alpha, best)
		else:
			beta = minf(beta, best)
		if beta <= alpha:
			break
	return best


func _evaluate(position: ChessGame) -> float:
	var score := 0.0
	for square in 64:
		var piece: String = position.board[square]
		if piece.is_empty():
			continue
		var white := piece == piece.to_upper()
		var value: int = PIECE_VALUE[piece.to_lower()]
		var row := int(square / 8)
		var file := square % 8
		var center_bonus: int = 7 - (absi(3 - file) + absi(3 - row))
		var positional: int = center_bonus * (3 if piece.to_lower() != "k" else 1)
		score += value + positional if white else -(value + positional)
	return score


func _move_order_score(position: ChessGame, move: Dictionary) -> int:
	var target: String = position.board[move.to]
	var score := 0
	if not target.is_empty():
		score += (
			int(PIECE_VALUE[target.to_lower()]) * 10
			- int(PIECE_VALUE[position.board[move.from].to_lower()])
		)
	if not String(move.get("promotion", "")).is_empty():
		score += 8000
	return score


func _button(text: String, primary: bool) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 46)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.add_theme_font_size_override("font_size", 13)
	for key in ["font_color", "font_hover_color", "font_pressed_color"]:
		button.add_theme_color_override(key, DARK_TEXT if primary else INK)
	button.add_theme_color_override("font_disabled_color", MUTED.darkened(0.3))
	button.add_theme_stylebox_override(
		"normal", _button_style(GREEN if primary else Color(1, 1, 1, 0.04), GREEN if primary else BORDER)
	)
	button.add_theme_stylebox_override(
		"hover", _button_style(GREEN.lightened(0.15) if primary else Color(1, 0.9, 0.7, 0.10), GREEN)
	)
	button.add_theme_stylebox_override(
		"pressed", _button_style(GREEN.darkened(0.15) if primary else Color(1, 0.9, 0.7, 0.16), GREEN)
	)
	button.add_theme_stylebox_override("disabled", _button_style(Color(1, 1, 1, 0.02), BORDER))
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.mouse_entered.connect(
		func() -> void:
			button.pivot_offset = button.size * 0.5
			create_tween().tween_property(button, "scale", Vector2.ONE * 1.025, 0.25).set_trans(Tween.TRANS_BACK)
	)
	button.mouse_exited.connect(
		func() -> void: create_tween().tween_property(button, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_SINE)
	)
	return button


func _label(text: String, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	return label


func _panel_style(fill: Color, border: Color, radius: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(radius)
	return style


func _button_style(fill: Color, border: Color) -> StyleBoxFlat:
	var style := _panel_style(fill, border, 12)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	return style

