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
var _tts_voice_id: String = ""
var use_timer_mode = true

func _ready():
	use_timer_mode = (GameManager.current_listen_mode == GameManager.ListenMode.TIME)
	json_path = GameManager.vocab_file_map[GameManager.current_vocab_level]
	load_words()
	_setup_signals()
	_init_tts()
	_start_new_round()
	game_ui.use_timer_mode = use_timer_mode
		

func _get_boundary_rect() -> Rect2:
	 # 获取屏幕大小
	var screen_size = get_viewport().get_visible_rect().size
	
	# 获取 HintLabel 的下边界（全局坐标）
	# 假设 hint_label 是有效的节点引用，请确保它已在 _ready() 中赋值
	var hint_bottom = hint_label.get_global_rect().end.y
	
	# 上方与 HintLabel 的间距（像素）
	var top_margin = 20
	
	# 计算矩形区域：左右无留白，底部无留白
	var rect = Rect2(
		0,                      # left
		hint_bottom + top_margin,  # top
		screen_size.x,          # width
		screen_size.y - (hint_bottom + top_margin)  # height（底部自然贴边）
	)
	return rect

func _init_tts():
	var voices = DisplayServer.tts_get_voices_for_language("en")
	if voices.size() > 0:
		_tts_voice_id = voices[0]
	else:
		var all_voices = DisplayServer.tts_get_voices()
		if all_voices.size() > 0:
			_tts_voice_id = all_voices[0]
		else:
			printerr("No TTS voice available")
			_tts_voice_id = ""

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

	# 1. 随机选择目标单词
	var new_target = words_list[randi() % words_list.size()]
	while current_target.has("word") and new_target["word"] == current_target["word"] and words_list.size() > 1:
		new_target = words_list[randi() % words_list.size()]
	current_target = new_target

	# 2. 生成候选单词列表（包含正确答案 + 干扰）
	var candidates = _generate_candidates(current_target, options_count)

	# 3. 【新步骤】先临时实例化所有卡片，收集尺寸
	var temp_card_infos = []   # [{word, size}]
	if not word_card_scene:
		printerr("WordCard scene is missing! Check export variable.")
		return
	for entry in candidates:
		var temp_card = word_card_scene.instantiate() as WordCard
		temp_card.visible = false
		card_container.add_child(temp_card)          # 临时加入容器以便计算尺寸
		temp_card.set_text(entry["word"])
		await get_tree().process_frame               # 等待卡片尺寸计算完成
		var card_size = temp_card.get_card_size()
		temp_card_infos.append({
			"word": entry["word"],
			"size": card_size
		})
		temp_card.queue_free()                        # 立即删除临时卡片
		await get_tree().process_frame                # 等待删除完成，避免冲突

	# 4. 调用布局求解器，获得每个单词的位置（中心点）
	var play_area = _get_boundary_rect()
	var layout = LayoutSolver2D.layout_cards(play_area, temp_card_infos, current_target["word"])
	if layout.is_empty():
		printerr("布局失败，无法放置足够卡片")
		return

	# 5. 正式创建卡片，并应用到计算好的位置
	_clear_cards()
	for entry in candidates:
		var word = entry["word"]
		if not layout.has(word):
			continue   # 如果本次布局没给这个词分配位置，就跳过（保底逻辑已经保证了至少4词）
		var card = word_card_scene.instantiate() as WordCard
		card.visible = false
		card_container.add_child(card)
		card.set_text(word)
		await get_tree().process_frame   # 确保内部尺寸更新（其实 set_text 里已经有了，但再等一帧无妨）
		card.position = layout[word]     # 直接使用计算好的中心点
		card.set_mode(card_motion_mode)
		card.set_boundary(play_area)
		card.clicked.connect(_on_card_clicked.bind(card, word))
		card.visible = true
		current_cards.append(card)

	# 6. 更新 UI 提示，播放语音
	hint_label.text = current_target.get("meaning", "")
	_speak_word(current_target["word"])


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
	# 保底：放在区域中心（此时一定会重叠，但概率低）
	return Vector2(area.position.x + area.size.x/2, area.position.y + area.size.y/2)

func _speak_word(word: String):
	if _tts_voice_id != "":
		DisplayServer.tts_speak(word, _tts_voice_id)
	else:
		print("Cannot speak word: no TTS voice")

func _on_card_clicked(card: WordCard, word: String):
	if is_waiting_next_round:
		return
	if word == current_target["word"]:
		if game_ui:
			game_ui.add_score(game_ui.score_per_correct)
		is_waiting_next_round = true
		card.vanish()
		await get_tree().create_timer(GameManager.VANISH_ANIMATION_TIME).timeout
		_start_new_round()
	else:
		if game_ui and not game_ui.use_timer_mode:
			game_ui.decrease_health(1)
		print("错误，正确答案是: ", current_target["word"])

func _clear_cards():
	for card in current_cards:
		if is_instance_valid(card):
			card.queue_free()
	current_cards.clear()

func _on_game_over(reason: String):
	for card in current_cards:
		if is_instance_valid(card):
			card.input_pickable = false

func _on_restart_pressed():
	_clear_cards()
	_start_new_round()
