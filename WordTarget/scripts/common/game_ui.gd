extends Control
class_name GameUI

# ========== 节点引用（与你场景中的路径一一对应） ==========
@onready var game_type_label = $TopBar/TopContent/HBox/GameTypeLabel
@onready var score_label = $TopBar/TopContent/HBox/ScoreLabel
@onready var health_container = $StatusPanel/HealthContainer
@onready var timer_container = $StatusPanel/TimerContainer
@onready var timer_label = $StatusPanel/TimerContainer/TimerLabel
@onready var game_over_panel = $GameOverPanel
@onready var restart_button = $GameOverPanel/VBox/MenuButtons/RestartButton
@onready var timer_node = $Timer

# ========== 导出变量（可在检查器中调整） ==========
@export var game_type_name: String = "WORD GAME"   # true=计时器模式, false=血量模式
@export var initial_health: int = 3
@export var initial_time: float = 10.0
@export var score_per_correct: int = 10

# ========== 内部状态 ==========
var current_score: int = 0
var current_health: int
var current_time: float
var is_game_active: bool = true
var _initializing: bool = true
# ========== 信号（供外部连接） ==========
signal game_over(reason: String)   # 参数: "health_depleted" 或 "time_up"
signal restart_pressed             # 点击重新开始按钮时发出（弹窗内）

@export var use_timer_mode: bool = true:
	set(value):
		if use_timer_mode == value:
			return
		use_timer_mode = value
		if use_timer_mode:
			_switch_to_timer_mode()
		else:
			_switch_to_health_mode()  

# ============================================================
# 生命周期
# ============================================================
func _ready():
	_setup_signals()
	game_type_label.text = game_type_name
	reset_game()
	_initializing = false
	

func _setup_signals():
	restart_button.pressed.connect(_on_restart_clicked)
	timer_node.timeout.connect(_on_timer_timeout)

# ============================================================
# 模式切换
# ============================================================
func _switch_to_health_mode():
	health_container.visible = true
	timer_container.visible = false
	timer_node.stop()
	current_health = initial_health
	_update_health_display()

func _switch_to_timer_mode():
	health_container.visible = false
	timer_container.visible = true
	current_time = initial_time
	_update_timer_display()
	timer_node.start(1.0)

# ============================================================
# 界面更新
# ============================================================
func _update_health_display():
	# 清空原有红心
	for child in health_container.get_children():
		child.queue_free()
	# 根据当前血量生成新的红心
	for i in range(current_health):
		var heart = Label.new()
		heart.text = "❤️"
		heart.add_theme_font_size_override("font_size", 28)
		health_container.add_child(heart)
	# 血量归零则结束游戏
	if current_health <= 0 and is_game_active:
		_end_game("health_depleted")

func _update_score_display():
	score_label.text = "Score: " + str(current_score)

func _update_timer_display():
	var seconds = max(0, int(ceil(current_time)))
	timer_label.text = str(seconds) + "s"
	if current_time <= 0 and is_game_active:
		_end_game("time_up")

# ============================================================
# 公共接口（供玩法场景调用）
# ============================================================
## 增加分数（自动更新显示）
func add_score(amount: int = score_per_correct):
	if not is_game_active:
		return
	current_score += amount
	_update_score_display()
	# 可选：播放加分动画（可在此处加tween，暂留空）

## 减少生命值（仅在血量模式下有效）
func decrease_health(amount: int = 1):
	if not is_game_active or use_timer_mode:
		return
	current_health = max(current_health - amount, 0)
	_update_health_display()

## 开始计时（计时器模式用，通常自动开始，但可用于暂停后恢复）
func start_timer():
	if use_timer_mode and is_game_active:
		timer_node.start(1.0)

## 暂停计时
func pause_timer():
	if use_timer_mode:
		timer_node.stop()

# 修正 reset_timer
func reset_timer():
	if not use_timer_mode:
		return
	timer_node.stop()
	current_time = initial_time
	_update_timer_display()
	if is_game_active:
		timer_node.start(1.0)

# 修正 reset_game
func reset_game():
	is_game_active = true
	game_over_panel.visible = false
	current_score = 0
	_update_score_display()
	if use_timer_mode:
		reset_timer()
	else:
		current_health = initial_health
		_update_health_display()
	restart_pressed.emit()

## 动态修改游戏类型名称
func set_game_type(name: String):
	game_type_name = name
	game_type_label.text = name

## 获取当前分数（供外部读取）
func get_current_score() -> int:
	return current_score

## 获取当前生命值（仅血量模式有效，计时器模式返回 -1）
func get_current_health() -> int:
	return current_health if not use_timer_mode else -1

## 获取剩余时间（仅计时器模式有效）
func get_current_time() -> float:
	return current_time if use_timer_mode else -1.0

# ============================================================
# 内部结束逻辑
# ============================================================
func _end_game(reason: String):
	if not is_game_active:
		return
	is_game_active = false
	if use_timer_mode:
		timer_node.stop()
	# 显示游戏结束弹窗
	game_over_panel.visible = true
	game_over.emit(reason)


func _on_restart_clicked():
	reset_game()

func _on_timer_timeout():
	if not is_game_active or not use_timer_mode:
		return
	current_time -= 1.0
	_update_timer_display()
	if current_time <= 0:
		_end_game("time_up")
	else:
		timer_node.start(1.0)   # 继续倒计时
