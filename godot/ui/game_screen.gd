class_name ChessGameScreen
extends Control
## Écran de partie hors ligne. Le transport réseau reste à la charge du parent.

signal back_requested
signal nearby_requested

const ChessRules = preload("res://core/chess_game.gd")
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
const INK := Color("#263b33")
const MUTED := Color("#687a70")
const GREEN := Color("#386b52")
const CREAM := Color("#f5f1e8")
const PAPER := Color("#fffdf8")
const BORDER := Color("#e5e0d5")
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
var _board: BoardView
var _status: Label
var _turn: Label
var _history: Label
var _undo_button: Button


func _ready() -> void:
	game = ChessRules.new()
	_build()
	get_viewport().size_changed.connect(_refresh_layout)
	_refresh_layout()
	_refresh()


## Parent: appeler avant l'ajout à l'arbre si le mode n'est pas local.
func configure(mode: String) -> void:
	if mode in ["ai", "local", "nearby"]:
		play_mode = mode


func start_new_game(mode: String = "") -> void:
	if not mode.is_empty() and mode in ["ai", "local", "nearby"]:
		play_mode = mode
	game.new_game()
	_selected = -1
	_legal_for_selection.clear()
	_last_move = Vector2i(-1, -1)
	_refresh()


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
	var content := HBoxContainer.new()
	content.name = "GameContent"
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 24)
	_root.add_child(content)
	_board = BoardView.new()
	_board.piece_textures = PIECES
	_board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_board.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_board.square_pressed.connect(_on_square_pressed)
	content.add_child(_board)
	content.add_child(_build_side_panel())


func _build_header() -> Control:
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	var back := _button("‹  Menu", false)
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
	card.custom_minimum_size = Vector2(290, 0)
	card.size_flags_horizontal = Control.SIZE_FILL
	card.add_theme_stylebox_override("panel", _panel_style(PAPER, BORDER, 20))
	var inset := MarginContainer.new()
	inset.add_theme_constant_override("margin_left", 20)
	inset.add_theme_constant_override("margin_right", 20)
	inset.add_theme_constant_override("margin_top", 20)
	inset.add_theme_constant_override("margin_bottom", 20)
	card.add_child(inset)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 12)
	inset.add_child(stack)
	_turn = _label("BLANCS", 11, GREEN)
	stack.add_child(_turn)
	_status = _label("À vous de jouer.", 23, INK)
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(_status)
	stack.add_child(_label("Les coups légaux sont indiqués sur le plateau.", 12, MUTED))
	var separator := HSeparator.new()
	stack.add_child(separator)
	stack.add_child(_label("COUPS JOUÉS", 10, MUTED))
	_history = _label("La partie commence.", 14, INK)
	_history.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_history.custom_minimum_size.y = 80
	_history.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_child(_history)
	_undo_button = _button("↶  Annuler le dernier coup", false)
	_undo_button.pressed.connect(_undo)
	stack.add_child(_undo_button)
	var new_game := _button("Nouvelle partie", true)
	new_game.pressed.connect(func() -> void: start_new_game())
	stack.add_child(new_game)
	var nearby := _button("Joueur à proximité", false)
	nearby.pressed.connect(func() -> void: nearby_requested.emit())
	stack.add_child(nearby)
	var note := _label("Votre partie reste sur cet appareil.", 11, MUTED)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(note)
	return card


func _refresh_layout() -> void:
	var narrow := get_viewport_rect().size.x < 820.0
	if _has_layout and _compact == narrow:
		return
	_has_layout = true
	_compact = narrow
	if not is_instance_valid(_root):
		return
	var content := _root.get_node("GameContent") as HBoxContainer
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
	if _thinking or _is_finished():
		return
	if _selected >= 0:
		for move in _legal_for_selection:
			if move.to == square:
				var uci: String = game.move_to_uci(move)
				var moving_piece: String = game.board[_selected]
				if String(move.get("promotion", "")) != "":
					uci = uci.substr(0, 4) + "q"
				if game.play_uci(uci):
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
	_board.update()


func _undo() -> void:
	if _thinking:
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
	_undo_button.disabled = game.get_uci_history().is_empty() or _thinking
	var checked_king := (
		game.board.find("K" if game.white_to_move else "k") if game.is_in_check() else -1
	)
	_board.set_board_state(game.board, _selected, _legal_for_selection, _last_move, checked_king)
	_board.update()


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
	await get_tree().process_frame
	var best_uci := _choose_ai_move(game, 2)
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
		var center_bonus := 7 - (abs(3 - file) + abs(3 - row))
		var positional := center_bonus * (3 if piece.to_lower() != "k" else 1)
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
	button.add_theme_color_override("font_color", PAPER if primary else INK)
	button.add_theme_color_override("font_hover_color", PAPER if primary else INK)
	button.add_theme_stylebox_override(
		"normal", _button_style(GREEN if primary else PAPER, GREEN if primary else BORDER)
	)
	button.add_theme_stylebox_override(
		"hover", _button_style(Color("#2f5c46") if primary else Color("#f1f3ec"), GREEN)
	)
	button.add_theme_stylebox_override(
		"pressed", _button_style(Color("#294f3d") if primary else Color("#e9eee5"), GREEN)
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


class BoardView:
	extends Control
	signal square_pressed(square: int)
	const LIGHT := Color("#eee9dc")
	const DARK := Color("#aebe9f")
	const SELECTED := Color("#e5bd66")
	const LAST_MOVE := Color(0.78, 0.67, 0.36, 0.30)
	var piece_textures: Dictionary = {}
	var pieces: Array[String] = []
	var selected := -1
	var targets: Array = []
	var last_move := Vector2i(-1, -1)
	var checked := false
	var _board_rect := Rect2()
	var _anim_from := -1
	var _anim_to := -1
	var _anim_piece := ""
	var _anim_progress := 1.0

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		custom_minimum_size = Vector2(260, 260)
		set_process(true)

	func animate_move(from_square: int, to_square: int, piece: String) -> void:
		_anim_from = from_square
		_anim_to = to_square
		_anim_piece = piece
		_anim_progress = 0.0
		queue_redraw()

	func _process(delta: float) -> void:
		if _anim_progress < 1.0:
			_anim_progress = minf(1.0, _anim_progress + delta / 0.18)
			queue_redraw()

	func set_board_state(
		pieces: Array[String], picked: int, legal: Array, previous: Vector2i, checked_square: int
	) -> void:
		self.pieces = pieces
		selected = picked
		targets = legal
		last_move = previous
		checked = checked_square

	func _gui_input(event: InputEvent) -> void:
		var point := Vector2(-1, -1)
		if (
			event is InputEventMouseButton
			and event.button_index == MOUSE_BUTTON_LEFT
			and event.pressed
		):
			point = event.position
		elif event is InputEventScreenTouch and event.pressed:
			point = event.position
		if point.x < 0.0 or not _board_rect.has_point(point):
			return
		var cell := _board_rect.size.x / 8.0
		var file := clampi(int((point.x - _board_rect.position.x) / cell), 0, 7)
		var row := clampi(int((point.y - _board_rect.position.y) / cell), 0, 7)
		square_pressed.emit(row * 8 + file)
		accept_event()

	func _draw() -> void:
		var side := minf(size.x, size.y) - 20.0
		if side <= 0.0:
			return
		_board_rect = Rect2((size - Vector2(side, side)) * 0.5, Vector2(side, side))
		draw_rect(_board_rect.grow(7.0).grow_individual(0, 0, 0, 2), Color("#d9d2c3"), true, 14.0)
		draw_rect(_board_rect.grow(4.0), PAPER, true, 12.0)
		var cell := side / 8.0
		for row in 8:
			for file in 8:
				var square := row * 8 + file
				var rect := Rect2(
					_board_rect.position + Vector2(file, row) * cell, Vector2(cell, cell)
				)
				draw_rect(rect, LIGHT if (row + file) % 2 == 0 else DARK)
				if square == last_move.x or square == last_move.y:
					draw_rect(rect, LAST_MOVE)
				if square == selected:
					draw_rect(rect, SELECTED)
				if (
					pieces.size() == 64
					and pieces[square] != ""
					and not (_anim_progress < 1.0 and square == _anim_to)
				):
					var texture: Texture2D = piece_textures[pieces[square]]
					var inset := cell * 0.09
					draw_texture_rect(
						texture,
						Rect2(
							rect.position + Vector2(inset, inset),
							rect.size - Vector2(inset * 2.0, inset * 2.0)
						),
						false
					)
		if (
			_anim_progress < 1.0
			and _anim_from >= 0
			and _anim_to >= 0
			and piece_textures.has(_anim_piece)
		):
			var from_center := (
				_board_rect.position
				+ Vector2((_anim_from % 8) + 0.5, int(_anim_from / 8) + 0.5) * cell
			)
			var to_center := (
				_board_rect.position + Vector2((_anim_to % 8) + 0.5, int(_anim_to / 8) + 0.5) * cell
			)
			var eased := 1.0 - pow(1.0 - _anim_progress, 3.0)
			var piece_side := cell * 0.82
			draw_texture_rect(
				piece_textures[_anim_piece],
				Rect2(
					from_center.lerp(to_center, eased) - Vector2.ONE * piece_side * 0.5,
					Vector2.ONE * piece_side
				),
				false
			)
		for move in targets:
			var target: int = move.to
			var center := (
				_board_rect.position + Vector2((target % 8) + 0.5, int(target / 8) + 0.5) * cell
			)
			var occupied := pieces.size() == 64 and pieces[target] != ""
			if occupied:
				draw_arc(
					center,
					cell * 0.45,
					0.0,
					TAU,
					36,
					Color(0.14, 0.28, 0.20, 0.68),
					maxf(2.0, cell * 0.055),
					true
				)
			else:
				draw_circle(center, maxf(4.0, cell * 0.12), Color(0.14, 0.28, 0.20, 0.38))
		if checked >= 0 and pieces.size() == 64:
			var row := int(checked / 8)
			var file := checked % 8
			var rect := Rect2(_board_rect.position + Vector2(file, row) * cell, Vector2(cell, cell))
			draw_rect(rect, Color(0.78, 0.22, 0.17, 0.32))
