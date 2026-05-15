extends Control

@onready var vocab_level_option = $UI/MainContainer/MenuButtons/VocabLevel/OptionButton
@onready var cursor_level_option = $UI/MainContainer/MenuButtons/Cursor/OptionButton
@onready var listen_and_pick_mode = $UI/MainContainer/MenuButtons/listen_and_pick_mode/OptionButton
@onready var back_btn = $UI/MainContainer/MenuButtons/BackBtn
@onready var scene_mode_has_voice = $UI/MainContainer/MenuButtons/scene_mode_has_voice/CheckButton

func _ready() -> void:
	init_vocab_level_option()
	init_cursor_option()
	init_listen_mode_option()
	init_scene_mode_has_voice()
	
	if back_btn:
		back_btn.pressed.connect(_on_back_btn)

	vocab_level_option.item_selected.connect(_on_vocab_selected)
	cursor_level_option.item_selected.connect(_on_cursor_selected)
	listen_and_pick_mode.item_selected.connect(_on_listen_mode_selected)

func _on_back_btn():
	SceneTransition.change_scene("res://scenes/menu/main_menu.tscn")

func init_scene_mode_has_voice():
	# 读取 GameManager 中的值，设置 CheckButton 状态
	scene_mode_has_voice.button_pressed = GameManager.current_scene_mode_have_voice
	scene_mode_has_voice.toggled.connect(_on_scene_mode_voice_toggled)

func _on_scene_mode_voice_toggled(button_pressed: bool):
	GameManager.current_scene_mode_have_voice = button_pressed
	print("场景模式语音开关：", button_pressed)
	
# ==============================
# 1. 词库难度下拉框
# ==============================
func init_vocab_level_option():
	vocab_level_option.clear()
	var idx := 0
	var target_idx := 0
	for level in GameManager.VocabLevel.values():
		var display_name = GameManager.vocab_display_name[level]
		vocab_level_option.add_item(display_name, level)
		if level == GameManager.current_vocab_level:
			target_idx = idx
		idx += 1
	vocab_level_option.select(target_idx)

# ==============================
# 2. 鼠标样式下拉框
# ==============================
func init_cursor_option():
	cursor_level_option.clear()
	var idx := 0
	var target_idx := 0
	for cursor in GameManager.CursorType.values():
		var display_name = GameManager.cursor_display_name[cursor]
		cursor_level_option.add_item(display_name, cursor)
		if cursor == GameManager.current_cursor_type:
			target_idx = idx
		idx += 1
	cursor_level_option.select(target_idx)

# ==============================
# 3. 游戏模式下拉框
# ==============================
func init_listen_mode_option():
	listen_and_pick_mode.clear()
	var idx := 0
	var target_idx := 0
	for mode in GameManager.ListenMode.values():
		var display_name = GameManager.listen_mode_display_name[mode]
		listen_and_pick_mode.add_item(display_name, mode)
		if mode == GameManager.current_listen_mode:
			target_idx = idx
		idx += 1
	listen_and_pick_mode.select(target_idx)

# ==============================
# 选中事件
# ==============================
func _on_vocab_selected(index: int) -> void:
	var selected_level: GameManager.VocabLevel = vocab_level_option.get_item_id(index)
	GameManager.set_vocab_level(selected_level)

func _on_cursor_selected(index: int) -> void:
	var selected_cursor: GameManager.CursorType = cursor_level_option.get_item_id(index)
	GameManager.set_cursor_type(selected_cursor)

func _on_listen_mode_selected(index: int) -> void:
	var selected_mode: GameManager.ListenMode = listen_and_pick_mode.get_item_id(index)
	GameManager.set_listen_mode(selected_mode)
