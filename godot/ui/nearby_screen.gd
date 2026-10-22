class_name NearbyScreen
extends Control

signal back_requested
signal room_join_requested(room: Dictionary)

const INK := Color("#263b33")
const MUTED := Color("#687a70")
const GREEN := Color("#386b52")
const CREAM := Color("#f5f1e8")
const PAPER := Color("#fffdf8")
const BORDER := Color("#e5e0d5")

var _transport: LanChessTransport
var _room_list: VBoxContainer
var _status: Label
var _host_button: Button
var _refresh_button: Button
var _waiting := false


func _ready() -> void:
	_build()
	get_viewport().size_changed.connect(_layout)
	_layout()


func set_transport(transport: LanChessTransport) -> void:
	_transport = transport
	if is_instance_valid(_transport):
		_transport.rooms_changed.connect(_show_rooms)
		_transport.state_changed.connect(_show_status)
		_transport.start_discovery()


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
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_bottom", 20)
	add_child(margin)
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 18)
	margin.add_child(page)
	var header := HBoxContainer.new()
	var back := _button("‹  Menu", false)
	back.pressed.connect(func() -> void: back_requested.emit())
	header.add_child(back)
	var heading := Label.new()
	heading.text = "Jouer à proximité"
	heading.add_theme_font_size_override("font_size", 26)
	heading.add_theme_color_override("font_color", INK)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	header.add_child(heading)
	page.add_child(header)
	var info := Label.new()
	info.text = "Appareils visibles sur votre réseau local. Aucun compte ni serveur distant."
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_color_override("font_color", MUTED)
	page.add_child(info)
	var card := PanelContainer.new()
	card.size_flags_vertical = Control.SIZE_EXPAND_FILL
	card.add_theme_stylebox_override("panel", _panel_style(PAPER, BORDER, 18))
	page.add_child(card)
	var inner := MarginContainer.new()
	inner.add_theme_constant_override("margin_left", 22)
	inner.add_theme_constant_override("margin_right", 22)
	inner.add_theme_constant_override("margin_top", 18)
	inner.add_theme_constant_override("margin_bottom", 18)
	card.add_child(inner)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 12)
	inner.add_child(stack)
	stack.add_child(_label("PARTIES DÉTECTÉES", 11, MUTED))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	stack.add_child(scroll)
	_room_list = VBoxContainer.new()
	_room_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_room_list.add_theme_constant_override("separation", 8)
	scroll.add_child(_room_list)
	_status = _label("Recherche sur le réseau local…", 13, MUTED)
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(_status)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 10)
	_host_button = _button("Créer une partie", true)
	_host_button.pressed.connect(_host)
	actions.add_child(_host_button)
	_refresh_button = _button("Rechercher", false)
	_refresh_button.pressed.connect(_refresh)
	actions.add_child(_refresh_button)
	page.add_child(actions)


func _layout() -> void:
	# Keep the content comfortably narrow on desktop and usable on phone-sized windows.
	pass


func _host() -> void:
	if not is_instance_valid(_transport):
		_show_status("Le service réseau local n’est pas disponible.")
		return
	_transport.stop_discovery()
	if _transport.start_host():
		_host_button.disabled = true
		_host_button.text = "En attente d’un joueur…"
		_refresh_button.disabled = true


func _refresh() -> void:
	if is_instance_valid(_transport):
		_transport.start_discovery()


func _show_rooms(rooms: Array) -> void:
	for child in _room_list.get_children():
		child.queue_free()
	if rooms.is_empty():
		var empty := _label(
			(
				"Aucune partie visible pour l’instant. "
				+ "L’autre appareil doit ouvrir une partie sur le même réseau Wi‑Fi."
			),
			14,
			MUTED
		)
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_room_list.add_child(empty)
		return
	for room_value in rooms:
		if not room_value is Dictionary:
			continue
		var room: Dictionary = room_value
		var join := _button("♟  %s     Rejoindre" % String(room.get("name", "Appareil")), false)
		join.pressed.connect(func() -> void: room_join_requested.emit(room))
		_room_list.add_child(join)


func _show_status(message: String) -> void:
	if is_instance_valid(_status):
		_status.text = message


func _button(text: String, primary: bool) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 48)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.add_theme_font_size_override("font_size", 14)
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
