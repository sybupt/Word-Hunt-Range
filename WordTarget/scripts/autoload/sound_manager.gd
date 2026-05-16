extends Node

# ====================
# 音效路径
# ====================
const gun_shot_sfx_path = "res://assets/SFX/universfield-gunshot-352466.mp3"
const gun_shot_miss_sfx_path = "res://assets/SFX/game-closing-sound.mp3"
const game_over_sfx_path = "res://assets/SFX/alphix-game-over-417465.mp3"

# ====================
# 开关 & 音量
# ====================
static var is_fx_enabled := true
@export var sfx_volume: float = 0.7

# ====================
# TTS
# ====================
var _tts_voice_id: String = ""
var _tts_retry_count := 0
const MAX_TTS_RETRY = 5  # 网页最多重试5次

# ====================
# 播放器
# ====================
var audio_player: AudioStreamPlayer

func _ready():
	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)
	audio_player.bus = "Master"

	# 网页端 TTS 需要延迟初始化！
	await get_tree().create_timer(0.2).timeout
	_init_tts()

# 网页专用：延迟重试初始化 TTS
func _init_tts():
	var voices = DisplayServer.tts_get_voices_for_language("en")
	if voices.size() > 0:
		_tts_voice_id = voices[0]
		print("TTS 初始化成功：使用英语语音")
		return
	else:
		var all_voices = DisplayServer.tts_get_voices()
		if all_voices.size() > 0:
			_tts_voice_id = all_voices[0]
			print("TTS 初始化成功：使用系统默认语音")
			return

	# 网页端失败 → 延迟重试
	_tts_voice_id = ""
	_tts_retry_count += 1
	if _tts_retry_count < MAX_TTS_RETRY:
		print("TTS 未就绪，" + str(_tts_retry_count) + " 秒后重试...")
		await get_tree().create_timer(1.0).timeout
		_init_tts()
	else:
		print("TTS 最终不可用（Web 环境限制）")

# 播放单词（自动重试 + 安全）
func speak_word(word: String):
	# 网页端核心：如果没准备好，再试一次初始化
	if _tts_voice_id == "":
		_init_tts()
		await get_tree().create_timer(0.5).timeout

	if _tts_voice_id != "":
		DisplayServer.tts_speak(word, _tts_voice_id)
	else:
		print("TTS 不可用，无法播放：", word)

# 开枪音效：单独减弱 0.5 倍
func play_correct():
	if is_fx_enabled:
		_play(gun_shot_sfx_path, sfx_volume * 0.5)

func play_wrong():
	if is_fx_enabled:
		_play(gun_shot_miss_sfx_path, sfx_volume)

func play_game_over():
	if is_fx_enabled:
		_play(game_over_sfx_path, sfx_volume)

# 内部播放
func _play(path: String, volume: float):
	var audio = load(path)
	if not audio:
		return
	audio_player.stream = audio
	audio_player.volume_db = linear_to_db(volume)
	audio_player.play()
