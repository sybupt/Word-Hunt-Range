extends RigidBody2D
class_name WordCard

enum Mode { STATIC, BOUNCE, FALL }

@onready var panel: Panel = $Panel
@onready var label: Label = $Panel/Label
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@export var firework_scene: PackedScene = preload("res://scenes/fx/firework.tscn")
var word_text: String = "apple"
var current_mode: Mode = Mode.STATIC
signal clicked(card_text: String)

var _normal_style: StyleBoxFlat
var _hover_style: StyleBoxFlat

# 边界限制（由玩法场景传入）
var boundary_rect: Rect2 = Rect2(-10000, -10000, 20000, 20000)

func _ready():
	# 禁止旋转
	lock_rotation = true
	input_pickable = true
	
	# 让 Panel 和 Label 忽略鼠标（事件传递到 RigidBody2D）
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	# 强制重置 Panel 偏移（防止场景文件干扰）
	panel.offset_left = 0
	panel.offset_top = 0
	panel.offset_right = 0
	panel.offset_bottom = 0
	
	mouse_entered.connect(_on_mouse_entered)
	mouse_exited.connect(_on_mouse_exited)
	
	# 临时碰撞体（避免空形状）
	var temp_shape = RectangleShape2D.new()
	temp_shape.size = Vector2(100, 60)
	collision_shape.shape = temp_shape
	
	_create_styles()
	_apply_normal_style()
	_set_text()
	set_mode(Mode.STATIC)

func _set_text():
	label.text = word_text
	await get_tree().process_frame
	_update_size_and_collision()

func set_text(new_text: String):
	word_text = new_text
	label.text = new_text
	await get_tree().process_frame
	await get_tree().process_frame
	_update_size_and_collision()

func set_mode(mode: Mode):
	current_mode = mode
	match mode:
		Mode.STATIC:
			freeze = true
			linear_velocity = Vector2.ZERO
			angular_velocity = 0
		Mode.BOUNCE:
			freeze = false
			linear_damp = 0
			angular_damp = 0
			linear_velocity = Vector2(randf_range(-200, 200), randf_range(-200, 200))
			angular_velocity = 0
			_apply_bounce_material(0.9)
		Mode.FALL:
			freeze = false
			linear_velocity = Vector2(0, 200)
			angular_velocity = 0
			_apply_bounce_material(0.2)

func _update_size_and_collision():
	var label_min_size = label.get_combined_minimum_size()
	var padding = Vector2(40, 30)
	var new_size = Vector2(
		max(label_min_size.x + padding.x, 100),
		max(label_min_size.y + padding.y, 60)
	)
	panel.size = new_size
	panel.position = -new_size / 2   # 因为 Panel 锚点还是左上角，需要手动偏移中心
	var rect_shape = RectangleShape2D.new()
	rect_shape.size = new_size
	collision_shape.shape = rect_shape
	collision_shape.position = Vector2.ZERO

func _create_styles():
	_normal_style = StyleBoxFlat.new()
	_normal_style.bg_color = Color(1, 1, 1)
	_normal_style.border_width_left = 2
	_normal_style.border_width_top = 2
	_normal_style.border_width_right = 2
	_normal_style.border_width_bottom = 2
	_normal_style.border_color = Color(0.8, 0.8, 0.8)
	_normal_style.corner_radius_top_left = 12
	_normal_style.corner_radius_top_right = 12
	_normal_style.corner_radius_bottom_left = 12
	_normal_style.corner_radius_bottom_right = 12
	_normal_style.shadow_size = 6
	_normal_style.shadow_offset = Vector2(0, 3)
	_normal_style.shadow_color = Color(0, 0, 0, 0.2)

	_hover_style = StyleBoxFlat.new()
	_hover_style.bg_color = Color(1, 1, 1)
	_hover_style.border_width_left = 2
	_hover_style.border_width_top = 2
	_hover_style.border_width_right = 2
	_hover_style.border_width_bottom = 2
	_hover_style.border_color = Color(0.4, 0.7, 1.0)
	_hover_style.corner_radius_top_left = 12
	_hover_style.corner_radius_top_right = 12
	_hover_style.corner_radius_bottom_left = 12
	_hover_style.corner_radius_bottom_right = 12
	_hover_style.shadow_size = 10
	_hover_style.shadow_offset = Vector2(0, 4)
	_hover_style.shadow_color = Color(0.4, 0.6, 1.0, 0.3)

	# 文本样式：不换行，居中对齐
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.autowrap_mode = TextServer.AUTOWRAP_OFF
	label.add_theme_font_size_override("font_size", 24)
	label.add_theme_color_override("font_color", Color(0.1, 0.1, 0.1))

func _apply_normal_style():
	panel.add_theme_stylebox_override("panel", _normal_style)

func _apply_hover_style():
	panel.add_theme_stylebox_override("panel", _hover_style)

func _apply_bounce_material(bounce: float):
	if physics_material_override:
		physics_material_override.bounce = bounce
	else:
		var mat = PhysicsMaterial.new()
		mat.bounce = bounce
		physics_material_override = mat

func _input_event(_viewport: Node, event: InputEvent, _shape_idx: int):
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		_animate_click()
		clicked.emit()

func _on_mouse_entered():
	_apply_hover_style()

func _on_mouse_exited():
	_apply_normal_style()

func _animate_click():
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_BACK)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(panel, "scale", Vector2(0.95, 0.95), 0.08)
	tween.tween_property(panel, "scale", Vector2(1.0, 1.0), 0.12)

func get_card_size() -> Vector2:
	return panel.size

func set_boundary(rect: Rect2):
	boundary_rect = rect

func _integrate_forces(state: PhysicsDirectBodyState2D):
	if current_mode == Mode.STATIC:
		return
	var pos = state.transform.origin
	var size = get_card_size()
	var min_x = boundary_rect.position.x + size.x/2
	var max_x = boundary_rect.position.x + boundary_rect.size.x - size.x/2
	var min_y = boundary_rect.position.y + size.y/2
	var max_y = boundary_rect.position.y + boundary_rect.size.y - size.y/2
	
	if pos.x < min_x:
		pos.x = min_x
		state.linear_velocity.x = -state.linear_velocity.x * 0.8
	if pos.x > max_x:
		pos.x = max_x
		state.linear_velocity.x = -state.linear_velocity.x * 0.8
	if pos.y < min_y:
		pos.y = min_y
		state.linear_velocity.y = -state.linear_velocity.y * 0.8
	if pos.y > max_y:
		pos.y = max_y
		state.linear_velocity.y = -state.linear_velocity.y * 0.8
	
	state.transform.origin = pos

func vanish():
	if not is_inside_tree():
		queue_free()
		return

	input_pickable = false
	freeze = true
	linear_velocity = Vector2.ZERO
	angular_velocity = 0

	# ⭐ 粒子先爆
	if GameManager.current_has_fx:
		_spawn_fireworks()

	# ⭐ 震屏
	if get_tree().current_scene.has_method("shake_camera"):
		get_tree().current_scene.shake_camera(5.0, 0.12)

	# ⭐ 创建“左右碎片”
	var left_piece = panel.duplicate()
	var right_piece = panel.duplicate()

	add_child(left_piece)
	add_child(right_piece)

	left_piece.position = panel.position
	right_piece.position = panel.position

	# 原卡片隐藏
	panel.visible = false

	# ⭐ Tween
	var tween = create_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_OUT)

	# 左右撕开
	tween.tween_property(left_piece, "position:x", left_piece.position.x - 120, 0.25)
	tween.tween_property(right_piece, "position:x", right_piece.position.x + 120, 0.25)

	# 微旋转（不是乱转）
	tween.tween_property(left_piece, "rotation", -0.3, 0.25)
	tween.tween_property(right_piece, "rotation", 0.3, 0.25)

	# 下落一点（增加重量感）
	tween.tween_property(left_piece, "position:y", left_piece.position.y + 60, 0.25)
	tween.tween_property(right_piece, "position:y", right_piece.position.y + 60, 0.25)

	# 淡出
	tween.tween_property(left_piece, "modulate:a", 0.0, 0.25)
	tween.tween_property(right_piece, "modulate:a", 0.0, 0.25)

	await tween.finished
	queue_free()

func _spawn_fireworks():
	if not firework_scene:
		return
	var fx = firework_scene.instantiate()
	get_tree().current_scene.add_child(fx)
	fx.global_position = global_position
	fx.emitting = true
	
	# 自动清理（防止内存残留）
	var timer = Timer.new()
	timer.one_shot = true
	timer.wait_time = fx.lifetime + 0.2
	fx.add_child(timer)
	timer.start()
	timer.timeout.connect(func():
		if is_instance_valid(fx):
			fx.queue_free()
	)
