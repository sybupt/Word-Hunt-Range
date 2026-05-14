extends CanvasLayer

@onready var color_rect := $ColorRect
@export var fade_duration := 0.5

var _is_transitioning := false

signal scene_changed

func _ready():
	layer = 128
	color_rect.modulate = Color.TRANSPARENT
	color_rect.anchor_right = 1.0
	color_rect.anchor_bottom = 1.0
	# 关键修正：设置 ColorRect 的鼠标过滤，并加上 Control. 前缀
	color_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE

func change_scene(scene, on_complete := Callable()):
	if _is_transitioning:
		push_warning("SceneTransition: 已有切换在进行中，已忽略本次请求")
		return
	
	_is_transitioning = true
	await _fade_out()
	await _load_and_change_scene(scene)
	await _fade_in()
	
	_is_transitioning = false
	scene_changed.emit()
	if on_complete.is_valid():
		on_complete.call()

func _fade_out():
	var tween = create_tween()
	color_rect.modulate = Color.TRANSPARENT
	tween.tween_property(color_rect, "modulate", Color.WHITE, fade_duration)
	await tween.finished
	# 淡出完成后阻止点击（也要加 Control. 前缀）
	color_rect.mouse_filter = Control.MOUSE_FILTER_STOP

func _fade_in():
	var tween = create_tween()
	color_rect.modulate = Color.WHITE
	tween.tween_property(color_rect, "modulate", Color.TRANSPARENT, fade_duration)
	await tween.finished
	color_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE

func _load_and_change_scene(scene):
	var scene_resource: PackedScene = null
	if scene is String:
		scene_resource = ResourceLoader.load(scene, "PackedScene")
		if scene_resource == null:
			printerr("SceneTransition: 无法加载场景 -> ", scene)
			_is_transitioning = false
			return
	elif scene is PackedScene:
		scene_resource = scene
	else:
		printerr("SceneTransition: 参数类型错误，需要 String 或 PackedScene")
		_is_transitioning = false
		return
	get_tree().change_scene_to_packed(scene_resource)
