extends Control
class_name ListenAndPick

@onready var card_container = $GameArea/CardContainer
@onready var game_area = $GameArea
@onready var game_ui = $GameUI
@onready var hint_label = $HintLabel

@export var word_card_scene: PackedScene = preload("res://scenes/common/WordCard.tscn")
@export var json_path: String = "res://data/TEM-4.json"
@export var options_count: int = 9
@export var card_motion_mode: WordCard.Mode = WordCard.Mode.STATIC

var words_list: Array = []
var current_target: Dictionary = {}
var current_cards: Array[WordCard] = []
var is_waiting_next_round: bool = false
var use_timer_mode = true

func _ready():
	use_timer_mode = (GameManager.current_listen_mode == GameManager.ListenMode.TIME)
	json_path = GameManager.vocab_file_map[GameManager.current_vocab_level]
	load_words()
	_setup_signals()
	_start_new_round()
	game_ui.use_timer_mode = use_timer_mode

func _get_boundary_rect() -> Rect2:
	var screen_size = get_viewport().get_visible_rect().size
	var hint_bottom = hint_label.get_global_rect().end.y
	var top_margin = 20
	var rect = Rect2(
		0,
		hint_bottom + top_margin,
		screen_size.x,
		screen_size.y - (hint_bottom + top_margin)
	)
	return rect

func _setup_signals():
	if game_ui:
		game_ui.game_over.connect(_on_game_over)
		game_ui.restart_pressed.connect(_on_restart_pressed)
	else:
		printerr("GameUI instance missing")

func load_words():
	if not FileAccess.file_exists(json_path):
		printerr("JSON not found: ", json_path)
		return
	var file = FileAccess.open(json_path, FileAccess.READ)
	var json_string = file.get_as_text()
	var json = JSON.new()
	var err = json.parse(json_string)
	if err != OK:
		printerr("JSON parse error: ", json.get_error_message())
		return
	var data = json.data
	words_list.clear()
	for key in data:
		var entry = data[key]
		if entry.has("english"):
			words_list.append({
				"word": entry["english"],
				"meaning": entry.get("chinese_trans", ""),
				"spell": entry.get("spell", "")
			})
	if words_list.is_empty():
		printerr("No words loaded")

func _start_new_round():
	if words_list.is_empty():
		return
	is_waiting_next_round = false
	if game_ui and game_ui.use_timer_mode:
		game_ui.reset_timer()

	var new_target = words_list[randi() % words_list.size()]
	while current_target.has("word") and new_target["word"] == current_target["word"] and words_list.size() > 1:
		new_target = words_list[randi() % words_list.size()]
	current_target = new_target

	var candidates = _generate_candidates(current_target, options_count)

	var temp_card_infos = []
	if not word_card_scene:
		printerr("WordCard scene is missing! Check export variable.")
		return
	for entry in candidates:
		var temp_card = word_card_scene.instantiate() as WordCard
		temp_card.visible = false
		card_container.add_child(temp_card)
		temp_card.set_text(entry["word"])
		await get_tree().process_frame
		var card_size = temp_card.get_card_size()
		temp_card_infos.append({
			"word": entry["word"],
			"size": card_size
		})
		temp_card.queue_free()
		await get_tree().process_frame

	var play_area = _get_boundary_rect()
	var layout = LayoutSolver2D.layout_cards(play_area, temp_card_infos, current_target["word"])
	if layout.is_empty():
		printerr("布局失败，无法放置足够卡片")
		return

	_clear_cards()
	for entry in candidates:
		var word = entry["word"]
		if not layout.has(word):
			continue
		var card = word_card_scene.instantiate() as WordCard
		card.visible = false
		card_container.add_child(card)
		card.set_text(word)
		await get_tree().process_frame
		card.position = layout[word]
		card.set_mode(card_motion_mode)
		card.set_boundary(play_area)
		card.clicked.connect(_on_card_clicked.bind(card, word))
		card.visible = true
		current_cards.append(card)

	hint_label.text = current_target.get("meaning", "")
	
	# ====================
	# 播放单词（交给 SoundManager）
	# ====================
	SoundManager.speak_word(current_target["word"])

func _generate_candidates(target: Dictionary, total: int) -> Array:
	var candidates = [target]
	var others = words_list.duplicate()
	others.erase(target)
	others.shuffle()
	for i in range(total - 1):
		if i < others.size():
			candidates.append(others[i])
	candidates.shuffle()
	return candidates

func _get_non_overlap_position(card: WordCard, existing_rects: Array[Rect2], area: Rect2) -> Vector2:
	var size = card.get_card_size()
	var attempts = 0
	while attempts < 50:
		var pos = Vector2(
			randf_range(area.position.x + size.x/2, area.end.x - size.x/2),
			randf_range(area.position.y + size.y/2, area.end.y - size.y/2)
		)
		var rect = Rect2(pos - size/2, size)
		var overlap = false
		for r in existing_rects:
			if r.intersects(rect):
				overlap = true
				break
		if not overlap:
			return pos
		attempts += 1
	return Vector2(area.position.x + area.size.x/2, area.position.y + area.size.y/2)

func _on_card_clicked(card: WordCard, word: String):
	if is_waiting_next_round:
		return
	if word == current_target["word"]:
		# 正确音效
		SoundManager.play_correct()

		if game_ui:
			game_ui.add_score(game_ui.score_per_correct)
		is_waiting_next_round = true
		card.vanish()
		await get_tree().create_timer(GameManager.VANISH_ANIMATION_TIME).timeout
		_start_new_round()
	else:
		# 错误音效
		SoundManager.play_wrong()

		if game_ui and not game_ui.use_timer_mode:
			game_ui.decrease_health(1)
		print("错误，正确答案是: ", current_target["word"])

func _clear_cards():
	for card in current_cards:
		if is_instance_valid(card):
			card.queue_free()
	current_cards.clear()

func _on_game_over(_reason: String):
	# 游戏结束音效
	SoundManager.play_game_over()

	for card in current_cards:
		if is_instance_valid(card):
			card.input_pickable = false

func _on_restart_pressed():
	_clear_cards()
	_start_new_round()
