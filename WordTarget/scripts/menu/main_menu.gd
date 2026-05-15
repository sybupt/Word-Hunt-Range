extends Control

@onready var login_button := $UI/MainContainer/MenuButtons/LoginGameBtn # 根据你的实际路径，注意按钮原名叫 HostGameBtn
@onready var register_button := $UI/MainContainer/MenuButtons/RegisterGameBtn
@onready var quit_button := $UI/MainContainer/MenuButtons/QuitBtn
@onready var setting_button := $UI/MainContainer/MenuButtons/SettingsBtn

func _ready():
	# 连接登录按钮的信号
	if login_button:
		login_button.pressed.connect(_on_login_pressed)
	# 连接注册按钮（暂时可以只打印信息）
	if register_button:
		register_button.pressed.connect(_on_register_pressed)
		
	if quit_button:
		quit_button.pressed.connect(_on_quit_button)
		
	if setting_button:
		setting_button.pressed.connect(_on_setting_button)

func _on_login_pressed():
	# 使用之前写好的转场单例跳转到听音选词场景
	# 注意：路径必须准确，假设场景放在 scenes/modes/ListenAndPick.tscn
	SceneTransition.change_scene("res://scenes/menu/game_mod_menu.tscn")

func _on_register_pressed():
	print("注册功能待实现")
	# 以后可以跳转到注册界面或弹出窗口
	
func _on_quit_button():
	get_tree().quit()
	
func _on_setting_button():
	SceneTransition.change_scene("res://scenes/menu/setting.tscn")
