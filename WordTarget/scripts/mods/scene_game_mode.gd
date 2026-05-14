# GameController.gd
extends Control

# ──────────────────────────────────────────────
# 节点引用
# ──────────────────────────────────────────────
@onready var img: TextureRect = $Img
@onready var top: Panel = $Top
@onready var word_name: Label = $Top/Label
@onready var words: Node2D = $Words   # 注意：建议改为 Node2D，但这里保留原样

# ──────────────────────────────────────────────
# 常量配置
# ──────────────────────────────────────────────
const WORD_CARD_SCENE := preload("res://scenes/common/WordCard.tscn")
const SCENE_DATA_DIR := "res://data/scene_data/"

const DEFAULT_DISTRACTOR_COUNT := 4      # 最多尝试生成多少个干扰词
const CARD_ALPHA := 0.65
const MAX_CORRECT_OFFSET := 120.0        # 正确词微调半径
const MAX_DISTRACTOR_OFFSET := 120.0     # 干扰词微调半径（可以相同或稍大）
const PLACE_MAX_TRIES := 60              # 微调尝试次数
const FLASH_DURATION := 0.35

# ──────────────────────────────────────────────
# 运行时状态
# ──────────────────────────────────────────────
var scene_files: Array[String] = []
var scene_index: int = 0
var scene_data: Dictionary = {}
var annotation_keys: Array[String] = []

var current_english: String = ""
var current_chinese: String = ""
var all_english_pool: Array[String] = []    # 当前场景所有英文（用于选干扰词）

var placed_rects: Array[Rect2] = []         # 存储已放置卡片的全局矩形

# ──────────────────────────────────────────────
# 生命周期
# ──────────────────────────────────────────────
func _ready() -> void:
	_load_scene_list()
	await _load_scene(scene_index)

func _load_scene_list() -> void:
	scene_files.clear()
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

	var raw_keys: Array = scene_data["annotations"].keys()
	annotation_keys.clear()
	for k in raw_keys:
		annotation_keys.append(str(k))
	annotation_keys.shuffle()

	# 构建所有英文的列表（用于干扰词池）
	all_english_pool.clear()
	for key in annotation_keys:
		all_english_pool.append(key)

	await _load_word()

func _load_word() -> void:
	# 队列为空才切换场景
	if annotation_keys.is_empty():
		scene_index += 1
		await _load_scene(scene_index)
		return

	# 从队列头部取出第一个单词
	current_english = annotation_keys.pop_front()
	var ann: Dictionary = scene_data["annotations"][current_english] as Dictionary
	current_chinese = str(ann["chinese"])

	word_name.text = current_english
	word_name.modulate = Color.WHITE

	_clear_cards()
	await _spawn_cards(ann)

func _clear_cards() -> void:
	for child in words.get_children():
		child.queue_free()
	placed_rects.clear()

# ──────────────────────────────────────────────
# 核心：生成所有卡片（正确词先放，干扰词基于各自坐标）
# ──────────────────────────────────────────────
func _spawn_cards(ann: Dictionary) -> void:
	# 1. 准备正确词的数据
	var correct_english = current_english
	var correct_positions: Array = ann["pos"] as Array
	var correct_raw = correct_positions[randi() % correct_positions.size()] as Array
	var correct_anchor = _map_raw_to_global(Vector2(correct_raw[0], correct_raw[1]))

	# 2. 先放置正确词（必须成功）
	var correct_card = await _try_place_card(
		correct_english,
		correct_anchor,
		true,   # 正确词
		MAX_CORRECT_OFFSET
	)
	if correct_card == null:
		push_error("无法放置正确词卡，这不应该发生")
		return

	# 3. 准备干扰词列表（从 all_english_pool 中排除 correct_english）
	var candidate_distractors: Array[String] = []
	for en in all_english_pool:
		if en != correct_english:
			candidate_distractors.append(en)
	candidate_distractors.shuffle()

	var distractors_placed = 0
	var max_attempts = DEFAULT_DISTRACTOR_COUNT * 2   # 避免无限循环
	for en in candidate_distractors:
		if distractors_placed >= DEFAULT_DISTRACTOR_COUNT:
			break
		if max_attempts <= 0:
			break
		max_attempts -= 1

		# 获取该干扰词的随机一个坐标
		var distractor_ann: Dictionary = scene_data["annotations"][en] as Dictionary
		var dist_positions: Array = distractor_ann["pos"] as Array
		if dist_positions.is_empty():
			continue
		var dist_raw = dist_positions[randi() % dist_positions.size()] as Array
		var dist_anchor = _map_raw_to_global(Vector2(dist_raw[0], dist_raw[1]))

		# 尝试放置干扰词（如果位置被已有卡片遮挡，则跳过）
		var card = await _try_place_card(
			en,
			dist_anchor,
			false,   # 干扰词
			MAX_DISTRACTOR_OFFSET
		)
		if card != null:
			distractors_placed += 1

# 尝试放置一张卡片（基于锚点微调）
# 返回放置成功的 WordCard，如果无法找到合法位置则返回 null
func _try_place_card(english: String, anchor_global: Vector2, is_correct: bool, max_offset: float) -> WordCard:
	var top_global_rect = top.get_global_rect()
	var screen_rect = get_viewport_rect()

	var card = WORD_CARD_SCENE.instantiate() as WordCard
	card.visible = false
	words.add_child(card)
	# 卡片上显示中文
	var chinese = scene_data["annotations"][english]["chinese"]
	card.set_text(chinese)
	card.set_mode(WordCard.Mode.STATIC)
	card.set_meta("english", english)   # 存储英文标识

	await get_tree().process_frame
	await get_tree().process_frame
	var card_size = card.get_card_size()

	# 寻找合法位置（在锚点附近微调）
	var final_global = anchor_global
	# 检查最终位置是否真的合法（可能被之前放置的卡片挤占）
	var half = card_size / 2.0
	var final_rect = Rect2(final_global - half, card_size)
	if not _is_position_valid(final_rect, screen_rect, top_global_rect):
		# 无法找到合法位置，销毁卡片并返回 null
		card.queue_free()
		return null
	card.visible = true
	card.global_position = final_global
	placed_rects.append(final_rect)
	card.modulate = Color(1, 1, 1, CARD_ALPHA)

	# 连接信号，传递英文标识
	card.clicked.connect(_on_card_clicked.bind(card, english))
	return card

# 坐标映射（保持不变）
func _map_raw_to_global(raw: Vector2) -> Vector2:
	var tex_size = img.texture.get_size()
	var img_global_rect = img.get_global_rect()
	var img_scale = min(img_global_rect.size.x / tex_size.x, img_global_rect.size.y / tex_size.y)
	var displayed_size = tex_size * img_scale
	var offset = (img_global_rect.size - displayed_size) / 2.0
	var displayed_origin = img_global_rect.position + offset
	return displayed_origin + raw * img_scale

# 合法性检查（保持不变）
func _is_position_valid(rect: Rect2, screen_rect: Rect2, top_rect: Rect2) -> bool:
	var expanded = rect.grow(4.0)
	for placed in placed_rects:
		if placed.intersects(expanded):
			return false
	return true

func _clamp_to_screen(pos: Vector2, card_size: Vector2, screen_rect: Rect2, top_rect: Rect2) -> Vector2:
	var half = card_size / 2.0
	var clamped = Vector2(
		clamp(pos.x, screen_rect.position.x + half.x, screen_rect.end.x - half.x),
		clamp(pos.y, screen_rect.position.y + half.y, screen_rect.end.y - half.y)
	)
	if top_rect.intersects(Rect2(clamped - half, card_size)):
		clamped.y = top_rect.end.y + half.y + 10.0
	return clamped

# ──────────────────────────────────────────────
# 卡片点击处理（通过英文标识判断）
# ──────────────────────────────────────────────
func _on_card_clicked(card_text: String, card: WordCard, card_english: String) -> void:
	if card_english == current_english:
		# 正确：进入下一个单词
		await _load_word()
	else:
		# 错误：只移除该卡片
		card.queue_free()
		_flash_label_red()
		# 先把【答错的这个单词】加入队尾
		if not annotation_keys.has(card_english):
			annotation_keys.append(card_english)

		# 再把【当前正确单词】加入队尾
		if not annotation_keys.has(current_english):
			annotation_keys.append(current_english)

func _flash_label_red() -> void:
	var tween = create_tween()
	tween.tween_property(word_name, "modulate", Color.RED, FLASH_DURATION * 0.3)
	tween.tween_property(word_name, "modulate", Color.WHITE, FLASH_DURATION * 0.7)

func _on_game_over() -> void:
	var dialog = AcceptDialog.new()
	dialog.title = "游戏结束"
	dialog.dialog_text = "🎉 恭喜！你已完成所有场景！"
	add_child(dialog)
	dialog.popup_centered()
