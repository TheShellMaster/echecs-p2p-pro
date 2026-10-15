extends Control
## Écran d'accueil chaleureux et responsive. Les choix de jeu sont exposés par signaux
## afin que le menu reste indépendant de l'IA, des sauvegardes et du transport local.

signal ai_game_requested
signal nearby_game_requested
signal local_pass_and_play_requested
signal continue_game_requested

const INK := Color("#263b33")
const MUTED := Color("#687a70")
const GREEN := Color("#386b52")
const GREEN_HOVER := Color("#2f5c46")
const CREAM := Color("#f5f1e8")
const PAPER := Color("#fffdf8")
const BORDER := Color("#e5e0d5")
const GOLD := Color("#c69346")

var _continue_available := false
var _continue_summary := ""
var _page: VBoxContainer
var _actions: VBoxContainer
var _continue_button: Button
var _layout_is_compact := false
var _has_layout := false


func _ready() -> void:
	_build()
	get_viewport().size_changed.connect(_refresh_layout)
	_refresh_layout()


## À appeler lorsque le système de sauvegarde aura trouvé une partie reprenable.
func set_continue_available(available: bool, summary: String = "") -> void:
	_continue_available = available
	_continue_summary = summary.strip_edges()
	if is_node_ready():
		_update_continue_button()


func _build() -> void:
	var background := ColorRect.new()
	background.color = CREAM
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)

	var scroll := ScrollContainer.new()
	scroll.name = "PageScroll"
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	add_child(scroll)

	var margin := MarginContainer.new()
	margin.name = "PageMargin"
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_theme_constant_override("margin_left", 52)
	margin.add_theme_constant_override("margin_right", 52)
	margin.add_theme_constant_override("margin_top", 30)
	margin.add_theme_constant_override("margin_bottom", 30)
	scroll.add_child(margin)

	_page = VBoxContainer.new()
	_page.name = "Page"
	_page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_page.add_theme_constant_override("separation", 28)
	margin.add_child(_page)

	_page.add_child(_build_header())
	_page.add_child(_build_content())
	_page.add_child(_build_footer())


func _build_header() -> Control:
	var header := HBoxContainer.new()
	header.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_theme_constant_override("separation", 14)

	var mark := PanelContainer.new()
	mark.custom_minimum_size = Vector2(50, 50)
	mark.add_theme_stylebox_override(
		"panel", _panel_style(Color("#e7eddf"), Color("#dce5d5"), 16, 0)
	)
	var mark_label := Label.new()
	mark_label.text = "É"
	mark_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mark_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	mark_label.add_theme_font_size_override("font_size", 25)
	mark_label.add_theme_color_override("font_color", GREEN)
	mark.add_child(mark_label)
	header.add_child(mark)

	var brand := VBoxContainer.new()
	brand.add_theme_constant_override("separation", 1)
	var name := _label("ÉCHECS", 16, INK)
	name.add_theme_font_size_override("font_size", 16)
	var tagline := _label("L'art de jouer, tout simplement", 12, MUTED)
	brand.add_child(name)
	brand.add_child(tagline)
	header.add_child(brand)
	header.add_spacer(false)

	var offline := PanelContainer.new()
	offline.add_theme_stylebox_override(
		"panel", _panel_style(Color("#e9efe4"), Color("#dce5d5"), 14, 0)
	)
	var offline_margin := MarginContainer.new()
	offline_margin.add_theme_constant_override("margin_left", 15)
	offline_margin.add_theme_constant_override("margin_right", 15)
	offline_margin.add_theme_constant_override("margin_top", 9)
	offline_margin.add_theme_constant_override("margin_bottom", 9)
	var offline_label := _label("●  HORS LIGNE, SANS COMPTE", 11, GREEN)
	offline_margin.add_child(offline_label)
	offline.add_child(offline_margin)
	header.add_child(offline)
	return header


func _build_content() -> Control:
	var content := HBoxContainer.new()
	content.name = "HomeContent"
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 24)

	var hero := _build_hero()
	hero.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hero.size_flags_stretch_ratio = 1.1
	content.add_child(hero)

	var panel := PanelContainer.new()
	panel.name = "PlayOptions"
	panel.custom_minimum_size = Vector2(370, 0)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.size_flags_stretch_ratio = 0.9
	panel.add_theme_stylebox_override("panel", _panel_style(PAPER, BORDER, 22, 1))
	content.add_child(panel)

	var inner := MarginContainer.new()
	inner.add_theme_constant_override("margin_left", 25)
	inner.add_theme_constant_override("margin_right", 25)
	inner.add_theme_constant_override("margin_top", 24)
	inner.add_theme_constant_override("margin_bottom", 24)
	panel.add_child(inner)
	_actions = VBoxContainer.new()
	_actions.add_theme_constant_override("separation", 12)
	inner.add_child(_actions)

	_actions.add_child(_label("CHOISIR UNE PARTIE", 11, MUTED))
	var heading := _label("À vous de jouer.", 25, INK)
	heading.add_theme_constant_override("line_spacing", 0)
	_actions.add_child(heading)
	_actions.add_child(_label("Une partie solo ou un joueur près de vous.", 13, MUTED))
	var spacer := Control.new()
	spacer.custom_minimum_size.y = 7
	_actions.add_child(spacer)

	var ai_button := _make_action_button(
		"Jouer contre l’IA", "Choisissez votre niveau et lancez la partie", true
	)
	ai_button.pressed.connect(func() -> void: ai_game_requested.emit())
	_actions.add_child(ai_button)

	var nearby_button := _make_action_button(
		"Jouer à proximité", "Trouvez un appareil sur le réseau local", false
	)
	nearby_button.pressed.connect(func() -> void: nearby_game_requested.emit())
	_actions.add_child(nearby_button)

	var local_button := _make_action_button(
		"À deux sur cet appareil", "Passez l’appareil après chaque coup", false
	)
	local_button.pressed.connect(func() -> void: local_pass_and_play_requested.emit())
	_actions.add_child(local_button)

	_continue_button = _make_action_button("Continuer la partie", "", false)
	_continue_button.pressed.connect(func() -> void: continue_game_requested.emit())
	_actions.add_child(_continue_button)
	_update_continue_button()

	return content


func _build_hero() -> Control:
	var hero := PanelContainer.new()
	hero.name = "Welcome"
	hero.custom_minimum_size = Vector2(0, 450)
	hero.add_theme_stylebox_override(
		"panel", _panel_style(Color("#e9eee3"), Color("#dce5d7"), 24, 1)
	)

	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 16)
	hero.add_child(layout)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 31)
	margin.add_theme_constant_override("margin_right", 31)
	margin.add_theme_constant_override("margin_top", 30)
	margin.add_theme_constant_override("margin_bottom", 27)
	layout.add_child(margin)
	var stack := VBoxContainer.new()
	stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_theme_constant_override("separation", 13)
	margin.add_child(stack)

	var eyebrow := _label("LA TABLE EST À VOUS", 11, GREEN)
	eyebrow.add_theme_font_size_override("font_size", 11)
	stack.add_child(eyebrow)
	var headline := _label("Une belle partie\ncommence ici.", 37, INK)
	headline.name = "Headline"
	headline.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	headline.add_theme_font_size_override("font_size", 37)
	stack.add_child(headline)
	var intro := _label(
		"Du premier coup jusqu’au mat, prenez le temps de jouer à votre façon.", 15, MUTED
	)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	intro.custom_minimum_size.y = 44
	stack.add_child(intro)

	var board := MiniBoard.new()
	board.custom_minimum_size = Vector2(270, 220)
	board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_child(board)

	var note := _label("Vos parties restent sur vos appareils.", 12, MUTED)
	stack.add_child(note)
	return hero


func _build_footer() -> Control:
	var footer := HBoxContainer.new()
	footer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_theme_constant_override("separation", 8)
	var dot := _label("●", 11, GOLD)
	footer.add_child(dot)
	var copy := _label("Sans connexion Internet · Vos parties restent privées", 12, MUTED)
	footer.add_child(copy)
	return footer


func _make_action_button(title: String, subtitle: String, primary: bool) -> Button:
	var button := Button.new()
	button.custom_minimum_size = Vector2(0, 68 if subtitle.is_empty() else 76)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.text = title + ("\n" + subtitle if not subtitle.is_empty() else "")
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.add_theme_font_size_override("font_size", 15)
	button.add_theme_color_override("font_color", PAPER if primary else INK)
	button.add_theme_color_override("font_hover_color", PAPER if primary else INK)
	button.add_theme_color_override("font_pressed_color", PAPER if primary else INK)
	button.add_theme_stylebox_override(
		"normal",
		_button_style(
			GREEN if primary else Color("#fffdf8"), Color("#b9d0bd") if primary else BORDER
		)
	)
	button.add_theme_stylebox_override(
		"hover",
		_button_style(
			GREEN_HOVER if primary else Color("#f1f3ec"), GREEN if primary else Color("#bdcbbc")
		)
	)
	button.add_theme_stylebox_override(
		"pressed", _button_style(Color("#294f3d") if primary else Color("#e9eee5"), GREEN)
	)
	button.add_theme_stylebox_override(
		"focus", _button_style(GREEN if primary else Color("#f1f3ec"), GOLD)
	)
	button.add_theme_constant_override("h_separation", 10)
	button.tooltip_text = subtitle
	return button


func _update_continue_button() -> void:
	if not is_instance_valid(_continue_button):
		return
	_continue_button.visible = _continue_available
	_continue_button.disabled = not _continue_available
	_continue_button.text = (
		"Continuer la partie"
		+ ("\n" + _continue_summary if not _continue_summary.is_empty() else "")
	)
	_continue_button.custom_minimum_size.y = 76 if not _continue_summary.is_empty() else 68


func _refresh_layout() -> void:
	if not is_instance_valid(_page):
		return
	var compact := get_viewport_rect().size.x < 940.0
	if _has_layout and compact == _layout_is_compact:
		return
	_has_layout = true
	_layout_is_compact = compact
	var margin := get_node_or_null("PageScroll/PageMargin") as MarginContainer
	if margin != null:
		var side_margin := 20 if compact else 52
		margin.add_theme_constant_override("margin_left", side_margin)
		margin.add_theme_constant_override("margin_right", side_margin)
	var content := _page.get_node_or_null("HomeContent") as HBoxContainer
	if content != null:
		content.vertical = compact
		content.add_theme_constant_override("separation", 16 if compact else 24)
		var play_options := content.get_node_or_null("PlayOptions") as PanelContainer
		if play_options != null:
			play_options.custom_minimum_size.x = 0 if compact else 370
		var hero := content.get_node_or_null("Welcome") as PanelContainer
		if hero != null:
			hero.custom_minimum_size.y = 335 if compact else 450
			var headline := hero.find_child("Headline", true, false) as Label
			if headline != null and compact:
				headline.add_theme_font_size_override("font_size", 31)
			elif headline != null:
				headline.add_theme_font_size_override("font_size", 37)


func _label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	return label


func _panel_style(fill: Color, border: Color, radius: int, border_width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(radius)
	return style


func _button_style(fill: Color, border: Color) -> StyleBoxFlat:
	var style := _panel_style(fill, border, 14, 1)
	style.content_margin_left = 17
	style.content_margin_right = 17
	style.content_margin_top = 11
	style.content_margin_bottom = 11
	return style


class MiniBoard:
	extends Control
	const LIGHT_SQUARE := Color("#f0ecdf")
	const DARK_SQUARE := Color("#9bae91")
	const PATTERN := [
		"r.bqkbnr",
		"pppp.ppp",
		"..n.....",
		"....p...",
		"....P...",
		".....N..",
		"PPPP.PPP",
		"RNBQKB.R"
	]
	var piece_textures: Dictionary = {}

	func _ready() -> void:
		for symbol in "KQRBNP":
			piece_textures["w" + symbol] = load("res://assets/w%s.png" % symbol)
			piece_textures["b" + symbol] = load("res://assets/b%s.png" % symbol)
		queue_redraw()

	func _draw() -> void:
		var side := minf(size.x, size.y) - 12.0
		if side <= 0.0:
			return
		var cell := side / 8.0
		var origin := Vector2((size.x - side) * 0.5, (size.y - side) * 0.5)
		draw_rect(
			Rect2(origin - Vector2(7, 7), Vector2(side + 14, side + 14)),
			Color("#d7e1d1"),
			true,
			12.0
		)
		for row in 8:
			for column in 8:
				var rect := Rect2(origin + Vector2(column, row) * cell, Vector2(cell, cell))
				draw_rect(rect, LIGHT_SQUARE if (row + column) % 2 == 0 else DARK_SQUARE)
				var piece: String = PATTERN[row][column]
				if piece != ".":
					var color_prefix := "w" if piece == piece.to_upper() else "b"
					var texture: Texture2D = piece_textures.get(color_prefix + piece.to_upper())
					if texture != null:
						var inset := cell * 0.08
						var piece_rect := Rect2(
							rect.position + Vector2(inset, inset),
							Vector2(cell - inset * 2.0, cell - inset * 2.0)
						)
						draw_texture_rect(texture, piece_rect, false)
