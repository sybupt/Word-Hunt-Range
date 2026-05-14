extends Control
@onready var listen_and_pick_btn = $UI/MainContainer/Buttons/ListenAndPickBtn
@onready var scene_game_btn = $UI/MainContainer/Buttons/SceneGameBtn
@onready var back_btn = $UI/MainContainer/Buttons/BackBtn

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	if listen_and_pick_btn:
		listen_and_pick_btn.pressed.connect(_on_listen_and_pick_btn)
	if scene_game_btn:
		scene_game_btn.pressed.connect(_on_scene_game_btn)
		
	if back_btn:
		back_btn.pressed.connect(_on_back_btn)
	pass # Replace with function body.


func _on_listen_and_pick_btn() -> void:
	SceneTransition.change_scene("res://scenes/mods/listen_and_pick.tscn")
	
func _on_scene_game_btn() -> void:
	SceneTransition.change_scene("res://scenes/mods/scene_game_mode.tscn")
	
func _on_back_btn() -> void:
	SceneTransition.change_scene("res://scenes/menu/main_menu.tscn")
	pass
