extends Node2D

## Vertical slice visuel du nouveau client.
## Le cœur chess/network sera branché après validation de cette scène.

const LIGHT := Color("#e7d8b8")
const DARK := Color("#826b4d")
const INK := Color("#253228")
const GOLD := Color("#d4b16a")
const SURFACE := Color("#1b2721")

var board_origin := Vector2.ZERO
var cell := 74.0
var hovered := Vector2i(-1, -1)
var selected := Vector2i(-1, -1)
var pulse := 0.0

func _ready() -> void:
	get_viewport().size_changed.connect(_layout)
	_layout()
	queue_redraw()

func _process(delta: float) -> void:
	pulse += delta
	queue_redraw()

func _layout() -> void:
	var viewport := get_viewport_rect().size
	cell = clamp(min(viewport.y - 250.0, viewport.x * 0.47) / 8.0, 42.0, 88.0)
	board_origin = Vector2(max(36.0, viewport.x * 0.16 - cell * 4.0), 190.0)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		hovered = _square_at(event.position)
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		selected = _square_at(event.position)

func _square_at(position: Vector2) -> Vector2i:
	var local := position - board_origin
	if local.x < 0.0 or local.y < 0.0 or local.x >= cell * 8.0 or local.y >= cell * 8.0:
		return Vector2i(-1, -1)
	return Vector2i(int(local.x / cell), int(local.y / cell))

func _draw() -> void:
	var viewport := get_viewport_rect().size
	draw_rect(Rect2(Vector2.ZERO, viewport), Color("#101713"))
	draw_circle(Vector2(viewport.x * .18, viewport.y * .58), viewport.y * .48, Color(0.25, 0.43, 0.30, .2))
	draw_circle(Vector2(viewport.x * .84, viewport.y * .32), viewport.y * .30, Color(0.25, 0.43, 0.30, .14))
	draw_string(ThemeDB.fallback_font, Vector2(viewport.x * .5 - 160.0, 72.0), "LE CLUB  ·  ÉCHECS EN RÉSEAU LOCAL", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GOLD)
	draw_string(ThemeDB.fallback_font, Vector2(viewport.x * .5 - 280.0, 124.0), "La prochaine partie commence ici", HORIZONTAL_ALIGNMENT_LEFT, -1, 34, Color("#f1f0e9"))
	draw_string(ThemeDB.fallback_font, Vector2(viewport.x * .5 - 188.0, 153.0), "Une IA à votre mesure. Un ami à portée de réseau.", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("#b1bcb1"))

	var frame := Rect2(board_origin - Vector2(14.0, 14.0), Vector2(cell * 8.0 + 28.0, cell * 8.0 + 28.0))
	draw_style_box(_panel_style(Color("#26352c"), GOLD, 18.0), frame)
	for row in 8:
		for col in 8:
			var square := Rect2(board_origin + Vector2(col, row) * cell, Vector2(cell, cell))
			draw_rect(square, LIGHT if (row + col) % 2 == 0 else DARK)
			if Vector2i(col, row) == hovered:
				draw_rect(square, Color(0.83, 0.69, 0.41, .34))
			if Vector2i(col, row) == selected:
				draw_rect(square.grow(-4.0), Color(0.83, 0.69, 0.41, .75), false, 3.0)

	var card := Rect2(Vector2(viewport.x - min(420.0, viewport.x - 90.0) - 42.0, 190.0), Vector2(min(420.0, viewport.x - 90.0), 370.0))
	draw_style_box(_panel_style(SURFACE, Color("#34463a"), 20.0), card)
	draw_string(ThemeDB.fallback_font, card.position + Vector2(28.0, 36.0), "CHOISIR UNE PARTIE", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("#b1bcb1"))
	for i in 5:
		var button := Rect2(card.position + Vector2(24.0, 58.0 + i * 58.0), Vector2(card.size.x - 48.0, 46.0))
		draw_style_box(_panel_style(Color("#26362d") if i > 0 else Color("#77b58b"), Color("#56705d"), 10.0), button)
	var labels := ["Jouer contre l'IA", "Créer une partie réseau", "Rejoindre une partie", "Jouer à deux en local", "Quitter"]
	for i in labels.size():
		var position := card.position + Vector2(card.size.x * .5 - 90.0, 86.0 + i * 58.0)
		draw_string(ThemeDB.fallback_font, position, labels[i], HORIZONTAL_ALIGNMENT_CENTER, 180.0, 15, Color("#f1f0e9"))

func _panel_style(fill: Color, border: Color, radius: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(int(radius))
	return style
