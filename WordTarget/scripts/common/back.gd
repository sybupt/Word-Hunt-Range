extends Control
@onready var back_btn = $MenuButtons/BackBtn

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	if back_btn:
		back_btn.pressed.connect(_on_back_btn)

func _on_back_btn() -> void:
	SceneTransition.change_scene("res://scenes/menu/game_mod_menu.tscn")
