extends Node

# ==============================
# 枚举定义
# ==============================
enum VocabLevel {
	CET4,
	CET6,
	COLLEGE_ENTRANCE,
	HIGH_SCHOOL_ENTRANCE,
	TEM4,
	TEM8
}

enum ListenMode {
	TIME,
	HEART
}

enum CursorType {
	CURSOR1,
	CURSOR2,
	DYNAMIC,
	NONE
}

# ==============================
# 显示名称
# ==============================
const listen_mode_display_name = {
	ListenMode.TIME: "时间模式",
	ListenMode.HEART: "心跳模式",
}

const vocab_display_name = {
	VocabLevel.CET4: "CET-4",
	VocabLevel.CET6: "CET-6",
	VocabLevel.COLLEGE_ENTRANCE: "大学入学词汇",
	VocabLevel.HIGH_SCHOOL_ENTRANCE: "初高词汇",
	VocabLevel.TEM4: "TEM-4",
	VocabLevel.TEM8: "TEM-8"
}

const cursor_display_name = {
	CursorType.CURSOR1: "准星 1",
	CursorType.CURSOR2: "准星 2",
	CursorType.DYNAMIC: "动态准星",
	CursorType.NONE: "系统默认",
}

# ==============================
# 数据路径
# ==============================
var vocab_file_map = {
	VocabLevel.CET4: "res://data/CET-4.json",
	VocabLevel.CET6: "res://data/CET-6.json",
	VocabLevel.COLLEGE_ENTRANCE: "res://data/College_Entrance_Examination.json",
	VocabLevel.HIGH_SCHOOL_ENTRANCE: "res://data/Senior_High_School_Entrance_Examination.json",
	VocabLevel.TEM4: "res://data/TEM-4.json",
	VocabLevel.TEM8: "res://data/TEM-8.json"
}

var cursor_file_map = {
	CursorType.CURSOR1: "res://assets/cursor/target.png",
	CursorType.CURSOR2: "res://assets/cursor/crosshair.png",
	CursorType.DYNAMIC: "res://assets/cursor/cursor_frames/",
	CursorType.NONE: ""
}

const STATIC_CURSOR_SIZE := 32
const DYNAMIC_CURSOR_SIZE := 32   # 可调整动态光标显示大小（像素）

# ==============================
# 当前状态
# ==============================
var current_vocab_level: VocabLevel = VocabLevel.CET4
var current_listen_mode: ListenMode = ListenMode.TIME
var current_cursor_type: CursorType = CursorType.CURSOR1

var current_scene_mode_have_voice = false
var current_has_fx = false
const VANISH_ANIMATION_TIME := 0.3
# ==============================
# 动态光标专用（CanvasLayer + Sprite2D）
# ==============================
var _cursor_layer: CanvasLayer
var _cursor_sprite: Sprite2D
var _dynamic_frames: Array[Texture2D] = []
var _frame_idx := 0
var _frame_timer := 0.0
var _tts_voice_id: String = ""
const DYNAMIC_FPS := 12.0

# ==============================
# 初始化
# ==============================
func _ready():
	_create_cursor_layer()
	call_deferred("_apply_cursor")
	set_process(true)
	_init_tts()
	
func _init_tts() -> void:
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

# ==============================
# 创建独立层（确保动态光标显示在所有 UI 之上）
# ==============================
func _create_cursor_layer():
	_cursor_layer = CanvasLayer.new()
	_cursor_layer.layer = 2048
	_cursor_layer.follow_viewport_enabled = true   # 关键：使 CanvasLayer 坐标对齐视口
	add_child(_cursor_layer)

	_cursor_sprite = Sprite2D.new()
	_cursor_sprite.centered = true
	_cursor_sprite.visible = false
	_cursor_layer.add_child(_cursor_sprite)

# ==============================
# 对外接口
# ==============================
func set_vocab_level(level: VocabLevel):
	current_vocab_level = level
	print("词库切换：", vocab_display_name[level])

func set_listen_mode(mode: ListenMode):
	current_listen_mode = mode
	print("模式切换：", listen_mode_display_name[mode])

func set_cursor_type(type: CursorType):
	if current_cursor_type == type:
		return
	current_cursor_type = type
	_apply_cursor()

# ==============================
# 核心：应用光标
# ==============================
func _apply_cursor():
	_cursor_sprite.visible = false
	_dynamic_frames.clear()
	_frame_idx = 0
	_frame_timer = 0.0

	match current_cursor_type:
		CursorType.NONE:
			DisplayServer.cursor_set_custom_image(null)
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			print("光标：系统默认")

		CursorType.DYNAMIC:
			Input.mouse_mode = Input.MOUSE_MODE_HIDDEN
			_load_dynamic_frames()
			if not _dynamic_frames.is_empty():
				_cursor_sprite.texture = _dynamic_frames[0]
				_cursor_sprite.visible = true
				print("动态光标已启动，帧数：", _dynamic_frames.size())
			else:
				print("动态光标加载失败，回退至无光标")
				DisplayServer.cursor_set_custom_image(null)
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

		_:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			var path = cursor_file_map.get(current_cursor_type, "")
			if not path.is_empty():
				_set_static_cursor(path)
			else:
				DisplayServer.cursor_set_custom_image(null)

# ==============================
# 静态光标
# ==============================
func _set_static_cursor(path: String):
	if not ResourceLoader.exists(path):
		print("静态光标文件不存在：", path)
		return

	var img: Image = null
	var tex = load(path) as Texture2D
	if tex:
		img = tex.get_image()
	else:
		img = Image.new()
		var abs_path = ProjectSettings.globalize_path(path)
		if img.load(abs_path) != OK:
			print("无法加载图片：", path)
			return

	img.resize(STATIC_CURSOR_SIZE, STATIC_CURSOR_SIZE, Image.INTERPOLATE_LANCZOS)
	var hotspot = Vector2(STATIC_CURSOR_SIZE / 2.0, STATIC_CURSOR_SIZE / 2.0)
	DisplayServer.cursor_set_custom_image(img, DisplayServer.CURSOR_ARROW, hotspot)
	print("静态光标设置成功：", path, " 尺寸 ", STATIC_CURSOR_SIZE)

# ==============================
# 动态光标：加载并缩放帧
# ==============================
func _load_dynamic_frames():
	var base_path = cursor_file_map[CursorType.DYNAMIC]
	var dir = DirAccess.open(base_path)
	if dir == null:
		print("无法打开动态光标目录：", base_path)
		return

	var files: Array[String] = []
	dir.list_dir_begin()
	var fname = dir.get_next()
	while fname != "":
		if not fname.begins_with(".") and fname.to_lower().ends_with(".png"):
			files.append(fname)
		fname = dir.get_next()
	dir.list_dir_end()
	files.sort()

	_dynamic_frames.clear()
	for file in files:
		var full_path = base_path + "/" + file
		var tex = load(full_path) as Texture2D
		if tex == null:
			print("无法加载帧：", full_path)
			continue

		var img = tex.get_image()
		if img == null:
			continue
		img.resize(DYNAMIC_CURSOR_SIZE, DYNAMIC_CURSOR_SIZE, Image.INTERPOLATE_LANCZOS)
		var scaled_tex = ImageTexture.create_from_image(img)
		_dynamic_frames.append(scaled_tex)

	print("动态光标加载帧数：", _dynamic_frames.size())

# ==============================
# 每帧更新：位置 + 动画（优化跟手性）
# ==============================
func _process(delta: float):
	if current_cursor_type != CursorType.DYNAMIC:
		return
	if not _cursor_sprite.visible:
		return
	if _dynamic_frames.is_empty():
		return

	# 直接使用视口鼠标坐标，设置 position（CanvasLayer 已跟随视口）
	_cursor_sprite.position = get_viewport().get_mouse_position()

	# 帧动画
	_frame_timer += delta
	if _frame_timer >= 1.0 / DYNAMIC_FPS:
		_frame_timer = 0.0
		_frame_idx = (_frame_idx + 1) % _dynamic_frames.size()
		_cursor_sprite.texture = _dynamic_frames[_frame_idx]
