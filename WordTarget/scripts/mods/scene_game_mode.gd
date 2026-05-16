extends Control

# 题目结构体
class QuestionItem:
	var word: String
	var is_listen_mode: bool  # true: 听英文选英文, false: 看英文选中文
	
	func _init(p_word: String, p_is_listen_mode: bool):
		word = p_word
		is_listen_mode = p_is_listen_mode

# 节点引用
@onready var img: TextureRect = $Img
@onready var top: Panel = $Top
@onready var word_name: Label = $Top/Label
@onready var words: Node2D = $Words
@onready var win_panel = $Panel
@onready var restart_btn = $Panel/MainContainer/Buttons/RestartBtn
@onready var back_btn = $Panel/MainContainer/Buttons/BackBtn

# 常量
const WORD_CARD_SCENE := preload("res://scenes/common/WordCard.tscn")
const SCENE_DATA_DIR := "res://data/scene_data/"
const DEFAULT_DISTRACTOR_COUNT := 4
const CARD_ALPHA := 0.65
const FLASH_DURATION := 0.35

# 运行时
var scene_files: Array[String] = []
var scene_index: int = 0
var scene_data: Dictionary = {}
var question_queue: Array[QuestionItem] = []
var all_english_pool: Array[String] = []

var current_question: QuestionItem = null
var current_english: String = ""
var placed_rects: Array[Rect2] = []   # 存储已放置卡片的矩形（用于碰撞检测）

func _ready() -> void:
	restart_btn.pressed.connect(_on_restart_btn)
	back_btn.pressed.connect(_on_back_btn)
	_load_scene_list()
	await _load_scene(scene_index)

func _on_restart_btn():
	win_panel.visible = false
	scene_index = 0
	_load_scene_list()
	await _load_scene(scene_index)

func _on_back_btn():
	SceneTransition.change_scene("res://scenes/menu/game_mod_menu.tscn")

func _load_scene_list() -> void:
	scene_files.clear()
	win_panel.visible = false
	var dir := DirAccess.open(SCENE_DATA_DIR)
	if dir == null:
		push_error("无法打开 scene_data 目录：" + SCENE_DATA_DIR)
		return
	dir.list_dir_begin()
	var fname := dir.get_next()
	while fname != "":
		if not dir.current_is_dir() and fname.ends_with(".json"):
			scene_files.append(SCENE_DATA_DIR + fname)
		fname = dir.get_next()
	dir.list_dir_end()
	scene_files.shuffle()

func _load_scene(index: int) -> void:
	if index >= scene_files.size():
		_on_game_over()
		return

	var path: String = scene_files[index]
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("无法读取 JSON：" + path)
		return
	var text: String = file.get_as_text()
	file.close()
	var result = JSON.parse_string(text)
	if result == null or not (result is Dictionary):
		push_error("JSON 解析失败：" + path)
		return

	scene_data = result as Dictionary

	var image_path: String = scene_data["image_path"]
	var tex: Texture2D = load(image_path) as Texture2D
	if tex == null:
		push_error("图片加载失败：" + image_path)
		return
	img.texture = tex
	await get_tree().process_frame

	# 构建题目队列：每个单词两个模式
	var raw_keys: Array = scene_data["annotations"].keys()
	question_queue.clear()
	all_english_pool.clear()
	for k in raw_keys:
		var word = str(k)
		all_english_pool.append(word)
		
		question_queue.append(QuestionItem.new(word, false))  # 模式一
		if GameManager.current_scene_mode_have_voice:
			question_queue.append(QuestionItem.new(word, true))   # 模式二
	question_queue.shuffle()

	await _load_next_question()

func _load_next_question() -> void:
	if question_queue.is_empty():
		scene_index += 1
		await _load_scene(scene_index)
		return

	current_question = question_queue.pop_front()
	current_english = current_question.word
	var ann: Dictionary = scene_data["annotations"][current_english]

	_clear_cards()
	
	if current_question.is_listen_mode:
		# 模式二：听音选英文
		word_name.text = "听音选词"
		word_name.modulate = Color.WHITE
		SoundManager.speak_word(current_english)
		await _spawn_audio_cards(ann)
	else:
		# 模式一：看英文选中文
		word_name.text = current_english
		word_name.modulate = Color.WHITE
		SoundManager.speak_word(current_english)
		await _spawn_match_cards(ann)

func _clear_cards() -> void:
	for child in words.get_children():
		child.queue_free()
	placed_rects.clear()

# ==================== 模式一：看英文选中文（卡片显示中文，基于锚点放置） ====================
func _spawn_match_cards(ann: Dictionary) -> void:
	# 正确词卡片
	var correct_anchor = _get_anchor_from_ann(ann)
	var correct_card = await _create_card_at_anchor(current_english, correct_anchor)
	if correct_card == null:
		push_error("无法放置正确词卡")
		return

	# 干扰词
	var distractors = _get_distractors(current_english, DEFAULT_DISTRACTOR_COUNT)
	for en in distractors:
		var dist_anchor = _get_anchor_from_word(en)
		if dist_anchor != Vector2.INF:
			await _create_card_at_anchor(en, dist_anchor)

# ==================== 模式二：听音选英文（卡片显示英文，同样基于锚点放置） ====================
func _spawn_audio_cards(ann: Dictionary) -> void:
	# 正确词卡片（显示英文）
	var correct_anchor = _get_anchor_from_ann(ann)
	var correct_card = await _create_english_card_at_anchor(current_english, correct_anchor)
	if correct_card == null:
		push_error("无法放置正确词卡（英文）")
		return

	# 干扰词（英文）
	var distractors = _get_distractors(current_english, DEFAULT_DISTRACTOR_COUNT)
	for en in distractors:
		var dist_anchor = _get_anchor_from_word(en)
		if dist_anchor != Vector2.INF:
			await _create_english_card_at_anchor(en, dist_anchor)

# 获取单词的随机一个锚点（全局坐标）
func _get_anchor_from_word(word: String) -> Vector2:
	if not scene_data["annotations"].has(word):
		return Vector2.INF
	var ann = scene_data["annotations"][word] as Dictionary
	return _get_anchor_from_ann(ann)

func _get_anchor_from_ann(ann: Dictionary) -> Vector2:
	var positions: Array = ann["pos"] as Array
	if positions.is_empty():
		return Vector2.ZERO
	var raw = positions[randi() % positions.size()] as Array
	return _map_raw_to_global(Vector2(raw[0], raw[1]))

# 坐标映射（原图坐标 -> 屏幕坐标）
func _map_raw_to_global(raw: Vector2) -> Vector2:
	var tex_size = img.texture.get_size()
	var img_global_rect = img.get_global_rect()
	var img_scale = min(img_global_rect.size.x / tex_size.x, img_global_rect.size.y / tex_size.y)
	var displayed_size = tex_size * img_scale
	var offset = (img_global_rect.size - displayed_size) / 2.0
	var displayed_origin = img_global_rect.position + offset
	return displayed_origin + raw * img_scale

# 创建卡片（模式一：显示中文）
func _create_card_at_anchor(english: String, anchor_global: Vector2) -> WordCard:
	var chinese = scene_data["annotations"][english]["chinese"]
	var card = WORD_CARD_SCENE.instantiate() as WordCard
	card.visible = false
	words.add_child(card)
	card.set_text(chinese)
	card.set_mode(WordCard.Mode.STATIC)
	card.set_meta("english", english)

	await get_tree().process_frame
	await get_tree().process_frame
	var card_size = card.get_card_size()
	var half = card_size / 2.0
	var final_rect = Rect2(anchor_global - half, card_size)
	if not _is_position_valid(final_rect):
		card.queue_free()
		return null
	card.global_position = anchor_global
	card.visible = true
	placed_rects.append(final_rect)
	card.modulate = Color(1,1,1,CARD_ALPHA)
	
	card.clicked.connect(_on_card_clicked.bind(card, english))
	return card

# 创建卡片（模式二：显示英文）
func _create_english_card_at_anchor(english: String, anchor_global: Vector2) -> WordCard:
	var card = WORD_CARD_SCENE.instantiate() as WordCard
	card.visible = false
	words.add_child(card)
	card.set_text(english)   # 显示英文
	card.set_mode(WordCard.Mode.STATIC)
	card.set_meta("english", english)

	await get_tree().process_frame
	await get_tree().process_frame
	var card_size = card.get_card_size()
	var half = card_size / 2.0
	var final_rect = Rect2(anchor_global - half, card_size)
	if not _is_position_valid(final_rect):
		card.queue_free()
		return null
	card.global_position = anchor_global
	card.visible = true
	placed_rects.append(final_rect)
	card.modulate = Color(1,1,1,CARD_ALPHA)
	
	card.clicked.connect(_on_card_clicked.bind(card, english))
	return card

func _is_position_valid(rect: Rect2) -> bool:
	var expanded = rect.grow(4.0)
	for placed in placed_rects:
		if placed.intersects(expanded):
			return false
	return true

# 生成干扰词列表（排除当前单词，不重复）
func _get_distractors(exclude_word: String, count: int) -> Array[String]:
	var pool = all_english_pool.duplicate()
	pool.erase(exclude_word)
	pool.shuffle()
	var result: Array[String] = []
	for i in range(min(count, pool.size())):
		result.append(pool[i])
	return result

func _on_card_clicked(card: WordCard, card_english: String) -> void:
	if card_english == current_english:
		# ========== 正确 ==========
		SoundManager.play_correct()
		
		card.vanish()
		await get_tree().create_timer(GameManager.VANISH_ANIMATION_TIME).timeout
		await _load_next_question()
	else:
		# ========== 错误 ==========
		SoundManager.play_wrong()
		
		_flash_label_red()
		SoundManager.speak_word(current_english)
		question_queue.append(QuestionItem.new(card_english, current_question.is_listen_mode))
		question_queue.append(current_question)

func _flash_label_red() -> void:
	var tween = create_tween()
	tween.tween_property(word_name, "modulate", Color.RED, FLASH_DURATION * 0.3)
	tween.tween_property(word_name, "modulate", Color.WHITE, FLASH_DURATION * 0.7)

func _on_game_over() -> void:
	# ========== 游戏结束 ==========
	SoundManager.play_game_over()
	
	win_panel.visible = true
