import pygame
import pygame_menu
import random
import threading
import time
import sys
import os
import json
import queue
import platform
import subprocess
import re
from pygame_menu import themes
from scene_game import scene_game_loop, get_scene_list

# -------------------------- 全局配置与状态管理 --------------------------
pygame.init()

BASE_WIDTH, BASE_HEIGHT = 1280, 720
current_width, current_height = BASE_WIDTH, BASE_HEIGHT
screen = pygame.display.set_mode((current_width, current_height))
pygame.display.set_caption("Word Hunt - 单词射击游戏")
clock = pygame.time.Clock()
is_fullscreen = False

# 颜色
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (255, 70, 70)
BLUE = (70, 130, 230)
GRAY = (240, 240, 245)
DARK_GRAY = (90, 90, 90)
GREEN = (50, 210, 80)
BG_COLOR = (240, 248, 255)
GRADIENT_TOP = (230, 240, 255)
GRADIENT_BOTTOM = (170, 200, 240)
CARD_COLOR = (255, 255, 255, 220)
CARD_HOVER = (255, 245, 200, 240)
CARD_SHADOW = (0, 0, 0, 40)

current_library = "CET-4"
sensitivity = 20
game_time = 60
game_mode = "en2cn"

game_paused = False
game_running = False
show_settings_in_game = False

# -------------------------- 系统原生语音 --------------------------
class NativeVoiceSystem:
    def __init__(self):
        self._word_queue = queue.Queue()
        self._running = True
        self._system = platform.system()
        self._init_voice()
        self._voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
        self._voice_thread.start()
        print(f"[语音系统] 已启动 ({self._system} 原生模式)")
        self.speak("欢迎使用单词射击游戏")

    def _init_voice(self):
        if self._system == "Windows":
            try:
                import win32com.client
                self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
                print("[语音系统] Windows SAPI 初始化成功")
            except ImportError:
                print("[语音系统] 未安装 pywin32，使用 PowerShell 备用方案")
                self._speaker = None
        else:
            self._speaker = None

    def _voice_loop(self):
        while self._running:
            try:
                word = self._word_queue.get(timeout=1.0)
                if word is None:
                    break
                print(f"[语音系统] 播报: {word}")
                self._speak_word(word)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[语音系统] 异常: {e}")

    def _speak_word(self, word):
        if self._system == "Windows":
            self._speak_windows(word)
        elif self._system == "Darwin":
            self._speak_macos(word)
        else:
            self._speak_linux(word)

    def _speak_windows(self, word):
        safe_word = word.replace("'", "''")
        try:
            if hasattr(self, '_speaker') and self._speaker:
                self._speaker.Speak(word, 0)
            else:
                ps_script = (
                    f"Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{safe_word}')"
                )
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        except Exception as e:
            print(f"[语音系统] Windows 播报失败: {e}")

    def _speak_macos(self, word):
        try:
            subprocess.run(['say', word])
        except Exception as e:
            print(f"[语音系统] macOS 播报失败: {e}")

    def _speak_linux(self, word):
        try:
            subprocess.run(['espeak', word], stderr=subprocess.DEVNULL)
        except:
            try:
                subprocess.run(['festival', '--tts'], input=word.encode(), stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[语音系统] Linux 播报失败: {e}")

    def speak(self, word):
        self._word_queue.put(word)

    def shutdown(self):
        self._running = False
        self._word_queue.put(None)

try:
    voice_system = NativeVoiceSystem()
except Exception as e:
    print(f"[警告] 语音系统初始化失败: {e}")
    class DummyVoice:
        def speak(self, w): print(f"[哑元] {w}")
        def shutdown(self): pass
    voice_system = DummyVoice()

# -------------------------- 字体与绘图工具 --------------------------
def get_font(size, bold=False):
    font_names = [
        "Microsoft YaHei", "SimHei", "Arial",
        "PingFang SC", "Heiti TC", "WenQuanYi Micro Hei",
        "Noto Sans CJK SC", "freesans", "sans-serif"
    ]
    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            test = font.render("测试", True, BLACK)
            if test.get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)

font_small = get_font(22)
font_medium = get_font(32)
font_large = get_font(46)
font_xlarge = get_font(64, bold=True)
font_hint = get_font(18)
font_mini = get_font(18)

def draw_gradient_background(surface, top_color, bottom_color):
    w, h = surface.get_size()
    for y in range(h):
        ratio = y / h
        r = top_color[0] + (bottom_color[0] - top_color[0]) * ratio
        g = top_color[1] + (bottom_color[1] - top_color[1]) * ratio
        b = top_color[2] + (bottom_color[2] - top_color[2]) * ratio
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (w, y))

def draw_rounded_rect(surface, color, rect, radius=0.2, shadow=False):
    rect = pygame.Rect(rect)
    r = min(radius * min(rect.width, rect.height), min(rect.width, rect.height)//2)
    if shadow:
        shadow_surf = pygame.Surface((rect.width+8, rect.height+8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, CARD_SHADOW, (4, 4, rect.width, rect.height), border_radius=int(r))
        surface.blit(shadow_surf, (rect.x-4, rect.y-4))
    if r < 1:
        pygame.draw.rect(surface, color, rect)
        return
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, color, surf.get_rect(), border_radius=int(r))
    surface.blit(surf, rect)

def draw_ui_panel(surface, text, value, x, y, width=180, height=60):
    panel_rect = (x, y, width, height)
    draw_rounded_rect(surface, WHITE, panel_rect, 0.3, shadow=True)
    pygame.draw.rect(surface, (200, 210, 230), panel_rect, 2, border_radius=18)
    label_surf = font_small.render(text, True, DARK_GRAY)
    value_surf = font_medium.render(str(value), True, BLUE)
    surface.blit(label_surf, (x + 15, y + 8))
    surface.blit(value_surf, (x + 15, y + 28))

# -------------------------- 窗口管理 --------------------------
def set_window_size(width, height):
    global current_width, current_height, screen, is_fullscreen
    current_width, current_height = width, height
    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((current_width, current_height))

def toggle_fullscreen():
    global is_fullscreen, screen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((current_width, current_height))

# -------------------------- 词库加载 --------------------------
def load_word_libraries():
    word_libraries = {}
    resource_dir = os.path.join(os.path.dirname(__file__), "resource")
    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
        generate_default_libraries(resource_dir)

    for filename in os.listdir(resource_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(resource_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                lib_name = filename.replace(".json", "")
                entries = []
                if isinstance(data, dict):
                    if "name" in data and isinstance(data["name"], str):
                        lib_name = data["name"]
                    for key, val in data.items():
                        if key == "name":
                            continue
                        if isinstance(val, dict) and "english" in val:
                            entries.append({
                                "english": val.get("english", ""),
                                "chinese_trans": val.get("chinese_trans", ""),
                                "spell": val.get("spell", "")
                            })
                        elif isinstance(val, list):
                            for w in val:
                                if isinstance(w, str):
                                    entries.append({"english": w, "chinese_trans": "", "spell": ""})
                                elif isinstance(w, dict):
                                    entries.append(w)
                if entries:
                    word_libraries[lib_name] = entries
            except Exception as e:
                print(f"加载词库失败 {filename}: {e}")
    if not word_libraries:
        word_libraries = {
            "小学": [{"english": "apple", "chinese_trans": "苹果", "spell": "[ˈæpl]"}],
        }
    return word_libraries

def generate_default_libraries(resource_dir):
    default = {
        "4级词汇": {
            "name": "4级词汇",
            "1": {"english": "abandon", "chinese_trans": "v. 遗弃；离开；放弃；终止；陷入 n. 放任，狂热", "spell": "[əˈbændən]"},
            "2": {"english": "absence", "chinese_trans": "缺席，不在场，缺乏", "spell": "[ˈæbsəns]"},
            "3": {"english": "absorb", "chinese_trans": "吸收，使专心", "spell": "[əbˈsɔːb]"},
        },
        "小学英语": {
            "name": "小学英语",
            "1": {"english": "apple", "chinese_trans": "苹果", "spell": "[ˈæpl]"},
            "2": {"english": "banana", "chinese_trans": "香蕉", "spell": "[bəˈnɑːnə]"},
        }
    }
    for fname, data in default.items():
        file_path = os.path.join(resource_dir, f"{fname}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

word_libraries = load_word_libraries()

# -------------------------- 长翻译裁剪 --------------------------
def shorten_chinese_text(text, max_width, font):
    if font.render(text, True, BLACK).get_width() <= max_width:
        return text
    pos_pattern = r'(?:n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|art\.|int\.|aux\.|num\.|det\.|abbr\.)\s*'
    matches = list(re.finditer(pos_pattern, text))
    if matches:
        last_match = matches[-1]
        short = text[last_match.start():].strip()
        if font.render(short, True, BLACK).get_width() <= max_width:
            return short
    short = text
    while len(short) > 0:
        short = short[:-1]
        if font.render(short + "…", True, BLACK).get_width() <= max_width:
            return short + "…"
    return "…"

# -------------------------- 游戏核心逻辑（经典模式） --------------------------
def game_loop():
    global game_paused, game_running, show_settings_in_game

    if game_mode == "scene":
        scene_name = globals().get("selected_scene_name", "bathroom")
        settings = {"game_time": game_time, "sensitivity": sensitivity, "scene_name": scene_name}
        score = scene_game_loop(screen, clock, voice_system, settings)
        show_game_over(score)
        return

    score = 0
    start_ticks = pygame.time.get_ticks()
    options = []
    target_entry = None
    show_feedback = False
    feedback_color = None
    feedback_timer = 0
    last_sw, last_sh = pygame.display.get_surface().get_size()

    def generate_options():
        nonlocal target_entry, options, show_feedback, feedback_color
        show_feedback = False
        options.clear()
        sw, sh = pygame.display.get_surface().get_size()
        lib = word_libraries[current_library]
        if len(lib) < 5:
            selected = random.choices(lib, k=5)
        else:
            selected = random.sample(lib, 5)
        target_entry = random.choice(selected)

        # 根据模式准备文本，并确保 target_text 经过相同处理
        if game_mode == "en2cn":
            raw_texts = [entry["chinese_trans"] for entry in selected]
            # 目标中文也进行截断，以保证与卡片文字完全一致
            target_raw = target_entry["chinese_trans"]
            target_text = shorten_chinese_text(target_raw, 280, font_medium)
            cards_text = [shorten_chinese_text(t, 280, font_medium) for t in raw_texts]
        elif game_mode == "cn2en":
            raw_texts = [entry["english"] for entry in selected]
            target_text = target_entry["english"]
            cards_text = raw_texts[:]
        elif game_mode == "listen2en":
            raw_texts = [entry["english"] for entry in selected]
            target_text = target_entry["english"]
            cards_text = raw_texts[:]
        else:
            raw_texts = [entry["english"] for entry in selected]
            target_text = target_entry["english"]
            cards_text = raw_texts[:]

        word_to_speak = target_entry.get("english", "")
        if word_to_speak:
            voice_system.speak(word_to_speak)

        random.shuffle(cards_text)

        area_x = 60
        area_y = 180
        area_w = sw - 120
        area_h = sh - 220
        card_height = 70
        max_card_width = 350

        placed_rects = []
        for text in cards_text:
            text_surf = font_medium.render(text, True, BLACK)
            desired_w = min(text_surf.get_width() + 40, max_card_width)
            card_width = max(120, desired_w)
            max_x = max(area_x, area_x + area_w - card_width)
            for _ in range(100):
                x = random.randint(area_x, max_x)
                y = random.randint(area_y, area_y + area_h - card_height)
                new_rect = pygame.Rect(x, y, card_width, card_height)
                if not any(new_rect.inflate(10,10).colliderect(r.inflate(10,10)) for r in placed_rects):
                    placed_rects.append(new_rect)
                    options.append({
                        "text": text,
                        "rect": new_rect,
                        "is_target": text == target_text,
                        "width": card_width
                    })
                    break
            else:
                x = random.randint(area_x, max_x)
                y = random.randint(area_y, area_y + area_h - card_height)
                rect = pygame.Rect(x, y, card_width, card_height)
                placed_rects.append(rect)
                options.append({
                    "text": text,
                    "rect": rect,
                    "is_target": text == target_text,
                    "width": card_width
                })
        print(f"[游戏] 目标: {target_entry['english']} | 显示文本: {target_text}")

    generate_options()
    game_running = True
    game_paused = False
    show_settings_in_game = False

    while game_running:
        sw, sh = pygame.display.get_surface().get_size()
        dt = clock.tick(30)
        if (sw, sh) != (last_sw, last_sh):
            last_sw, last_sh = sw, sh
            generate_options()
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                voice_system.shutdown()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and not game_paused:
                if show_feedback:
                    continue
                for opt in options:
                    if opt["rect"].collidepoint(mouse_pos):
                        if opt["is_target"]:
                            score += 10
                            feedback_color = GREEN
                        else:
                            feedback_color = RED
                        show_feedback = True
                        feedback_timer = 30
                        break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_settings_in_game:
                        show_settings_in_game = False
                    else:
                        game_paused = not game_paused
        if show_feedback:
            feedback_timer -= 1
            if feedback_timer <= 0:
                show_feedback = False
                generate_options()
        if not game_paused:
            draw_gradient_background(screen, GRADIENT_TOP, GRADIENT_BOTTOM)
            elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
            remaining_time = game_time - elapsed
            if remaining_time <= 0:
                game_running = False
                show_game_over(score)
                break
            draw_ui_panel(screen, "得分", score, 20, 20)
            draw_ui_panel(screen, "剩余时间", f"{remaining_time}s", 220, 20)
            mode_text = {"en2cn": "英译中", "cn2en": "中译英", "listen2en": "听音选词"}
            mode_surf = font_small.render(f"模式: {mode_text.get(game_mode, '')}", True, DARK_GRAY)
            screen.blit(mode_surf, (sw - mode_surf.get_width() - 20, 35))
            hint_surf = font_hint.render("按 ESC 暂停", True, DARK_GRAY)
            screen.blit(hint_surf, (sw - hint_surf.get_width() - 20, 55))
            if game_mode == "en2cn":
                prompt = target_entry["english"]
            elif game_mode == "cn2en":
                prompt = target_entry["chinese_trans"]
            else:
                prompt = "🔊 请听发音并选择"
            prompt_surf = font_xlarge.render(prompt, True, BLACK)
            prompt_rect = prompt_surf.get_rect(center=(sw//2, 110))
            bg_rect = prompt_rect.inflate(40, 20)
            draw_rounded_rect(screen, (255, 255, 255, 220), bg_rect, 0.3, shadow=True)
            screen.blit(prompt_surf, prompt_rect)
            for opt in options:
                rect = opt["rect"]
                is_hover = rect.collidepoint(mouse_pos) and not show_feedback
                if show_feedback and opt["is_target"]:
                    card_color = (100, 255, 100, 180) if feedback_color == GREEN else (255, 100, 100, 180)
                elif is_hover:
                    card_color = CARD_HOVER
                else:
                    card_color = CARD_COLOR
                draw_rounded_rect(screen, card_color, rect, 0.25, shadow=True)
                text_surf = font_medium.render(opt["text"], True, BLACK)
                if text_surf.get_width() > rect.width - 20:
                    text_surf = font_small.render(opt["text"], True, BLACK)
                    if text_surf.get_width() > rect.width - 20:
                        text_surf = font_mini.render(opt["text"], True, BLACK)
                text_rect = text_surf.get_rect(center=rect.center)
                screen.blit(text_surf, text_rect)
        else:
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((30, 30, 40, 160))
            screen.blit(overlay, (0, 0))
            if show_settings_in_game:
                draw_in_game_settings(sw, sh)
            else:
                draw_pause_menu(sw, sh)
        pygame.display.flip()

# -------------------------- 暂停菜单与设置 --------------------------
def draw_pause_menu(sw, sh):
    global game_paused, show_settings_in_game, game_running
    menu_w, menu_h = 400, 450
    menu_x = (sw - menu_w) // 2
    menu_y = (sh - menu_h) // 2
    draw_rounded_rect(screen, (45, 52, 60, 240), (menu_x, menu_y, menu_w, menu_h), 0.05)
    title_surf = font_large.render("游戏暂停", True, WHITE)
    screen.blit(title_surf, (menu_x + (menu_w - title_surf.get_width())//2, menu_y + 30))
    buttons = [
        ("继续游戏", lambda: globals().update({'game_paused': False})),
        ("设置", lambda: globals().update({'show_settings_in_game': True})),
        ("结束本局", lambda: (globals().update({'game_running': False, 'game_paused': False}))),
        ("返回主菜单", lambda: (globals().update({'game_running': False, 'game_paused': False}), main_menu()))
    ]
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]
    btn_y = menu_y + 120
    for text, cb in buttons:
        btn_rect = pygame.Rect(menu_x + 50, btn_y, menu_w - 100, 60)
        is_hover = btn_rect.collidepoint(mouse_pos)
        color = (70, 130, 180) if is_hover else (60, 80, 100)
        draw_rounded_rect(screen, color, btn_rect, 0.2)
        t_surf = font_medium.render(text, True, WHITE)
        screen.blit(t_surf, (menu_x + (menu_w - t_surf.get_width())//2, btn_y + 12))
        if is_hover and mouse_click:
            time.sleep(0.15)
            cb()
        btn_y += 80

def draw_in_game_settings(sw, sh):
    global show_settings_in_game, sensitivity
    menu_w, menu_h = 500, 520
    menu_x = (sw - menu_w) // 2
    menu_y = (sh - menu_h) // 2
    draw_rounded_rect(screen, (45, 52, 60, 240), (menu_x, menu_y, menu_w, menu_h), 0.05)
    title_surf = font_large.render("设置", True, WHITE)
    screen.blit(title_surf, (menu_x + (menu_w - title_surf.get_width())//2, menu_y + 25))
    label_surf = font_small.render(f"鼠标灵敏度: {sensitivity}", True, WHITE)
    screen.blit(label_surf, (menu_x + 50, menu_y + 100))
    slider_track = pygame.Rect(menu_x + 50, menu_y + 140, menu_w - 100, 20)
    draw_rounded_rect(screen, (80, 80, 80), slider_track, 0.5)
    slider_x = menu_x + 50 + (sensitivity - 10) * (menu_w - 100) / 40
    pygame.draw.circle(screen, (100, 150, 255), (int(slider_x), menu_y + 150), 15)
    sizes = [(800,600), (1024,768), (1280,720)]
    btn_y = menu_y + 200
    label_surf = font_small.render("窗口大小:", True, WHITE)
    screen.blit(label_surf, (menu_x + 50, btn_y))
    btn_y += 40
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]
    for i, (w, h) in enumerate(sizes):
        btn_rect = pygame.Rect(menu_x + 50 + i*140, btn_y, 130, 45)
        is_hover = btn_rect.collidepoint(mouse_pos)
        is_current = (w, h) == (current_width, current_height)
        color = (100, 150, 200) if is_current else (70, 130, 180) if is_hover else (60, 80, 100)
        draw_rounded_rect(screen, color, btn_rect, 0.2)
        t_surf = font_small.render(f"{w}x{h}", True, WHITE)
        screen.blit(t_surf, (menu_x + 50 + i*140 + (130 - t_surf.get_width())//2, btn_y + 10))
        if is_hover and mouse_click:
            time.sleep(0.15)
            set_window_size(w, h)
    btn_y += 70
    fs_text = "退出全屏" if is_fullscreen else "切换全屏"
    fs_rect = pygame.Rect(menu_x + 50, btn_y, menu_w - 100, 50)
    fs_hover = fs_rect.collidepoint(mouse_pos)
    fs_color = (70, 130, 180) if fs_hover else (60, 80, 100)
    draw_rounded_rect(screen, fs_color, fs_rect, 0.2)
    fs_surf = font_medium.render(fs_text, True, WHITE)
    screen.blit(fs_surf, (menu_x + (menu_w - fs_surf.get_width())//2, btn_y + 8))
    if fs_hover and mouse_click:
        time.sleep(0.15)
        toggle_fullscreen()
    btn_y += 80
    back_rect = pygame.Rect(menu_x + 50, btn_y, menu_w - 100, 50)
    back_hover = back_rect.collidepoint(mouse_pos)
    back_color = (180, 70, 70) if back_hover else (140, 50, 50)
    draw_rounded_rect(screen, back_color, back_rect, 0.2)
    back_surf = font_medium.render("返回", True, WHITE)
    screen.blit(back_surf, (menu_x + (menu_w - back_surf.get_width())//2, btn_y + 8))
    if back_hover and mouse_click:
        time.sleep(0.15)
        globals()['show_settings_in_game'] = False
    if mouse_click and slider_track.inflate(0,20).collidepoint(mouse_pos):
        new_sens = int(10 + (mouse_pos[0] - (menu_x + 50)) * 40 / (menu_w - 100))
        globals()['sensitivity'] = max(10, min(50, new_sens))

def show_game_over(score):
    sw, sh = pygame.display.get_surface().get_size()
    theme = themes.THEME_BLUE.copy()
    theme.widget_font = get_font(30)
    theme.title_font = get_font(50, bold=True)
    menu = pygame_menu.Menu(title="游戏结束", width=sw, height=sh, theme=theme)
    menu.add.label(f"最终得分: {score}", font_size=60, margin=(0, 30))
    menu.add.vertical_margin(50)
    menu.add.button("再来一局", game_loop)
    menu.add.button("返回主菜单", main_menu)
    menu.mainloop(screen)

# -------------------------- 二级菜单（经典/设置/场景） --------------------------
def run_classic_menu():
    # 如果 game_mode 不是经典模式之一，重置为 en2cn
    if game_mode not in ("en2cn", "cn2en", "listen2en"):
        globals()['game_mode'] = "en2cn"

    theme = themes.THEME_SOLARIZED.copy()
    theme.widget_font = get_font(30)
    theme.title_font = get_font(50, bold=True)

    menu = pygame_menu.Menu(
        title="经典模式",
        width=current_width,
        height=current_height,
        theme=theme
    )
    lib_names = [(name, name) for name in word_libraries.keys()]
    menu.add.selector("词库选择: ", lib_names,
                     onchange=lambda s, v: globals().update({'current_library': v}))

    mode_choices = [("英译中", "en2cn"), ("中译英", "cn2en"), ("听音选词", "listen2en")]
    # 计算当前 game_mode 对应的索引
    default_index = 0
    for i, (_, val) in enumerate(mode_choices):
        if val == game_mode:
            default_index = i
            break

    menu.add.selector("游戏模式: ", mode_choices,
                     default=default_index,  # 正确传入整数索引
                     onchange=lambda s, v: globals().update({'game_mode': v}))

    menu.add.range_slider("游戏时长(秒): ", default=game_time, range_values=(30, 180), increment=10,
                          onchange=lambda v: globals().update({'game_time': int(v)}))
    menu.add.range_slider("鼠标灵敏度: ", default=sensitivity, range_values=(10, 50), increment=1,
                          onchange=lambda v: globals().update({'sensitivity': int(v)}))
    menu.add.vertical_margin(30)
    menu.add.button("开始游戏", game_loop, font_size=36, background_color=(50, 210, 80))
    menu.add.button("返回主菜单", main_menu)
    menu.mainloop(screen)

def run_settings_menu():
    theme = themes.THEME_SOLARIZED.copy()
    theme.widget_font = get_font(30)
    theme.title_font = get_font(50, bold=True)

    menu = pygame_menu.Menu(
        title="设置",
        width=current_width,
        height=current_height,
        theme=theme
    )
    menu.add.range_slider("鼠标灵敏度: ", default=sensitivity, range_values=(10, 50), increment=1,
                          onchange=lambda v: globals().update({'sensitivity': int(v)}))
    menu.add.selector("窗口大小: ", [("800x600", (800,600)), ("1024x768", (1024,768)), ("1280x720", (1280,720))],
                     onchange=lambda s, v: set_window_size(*v))
    menu.add.button("切换全屏", toggle_fullscreen)
    menu.add.vertical_margin(30)
    menu.add.button("返回主菜单", main_menu)
    menu.mainloop(screen)

# -------------------------- 场景选择菜单（带滚动） --------------------------
def run_scene_menu():
    scenes = get_scene_list()
    if not scenes:
        theme = themes.THEME_SOLARIZED.copy()
        theme.widget_font = get_font(30)
        theme.title_font = get_font(50, bold=True)
        menu = pygame_menu.Menu(
            title="场景选词",
            width=current_width,
            height=current_height,
            theme=theme
        )
        menu.add.label("未找到任何场景文件", max_char=30, font_size=30)
        menu.add.button("返回主菜单", main_menu)
        menu.mainloop(screen)
        return

    selected_scene = None
    scroll_y = 0
    max_scroll = 0
    card_w, card_h = 250, 180
    cols = 4
    margin_x = 60
    margin_top = 120      # 卡片区域起始 Y
    card_gap_y = 40
    header_height = 80    # 标题和返回按钮占用的高度，用于裁剪

    cards = []
    sw, sh = screen.get_size()
    row = 0
    col = 0
    for scene_name in scenes:
        x = margin_x + col * (card_w + 20)
        y = margin_top + row * (card_h + card_gap_y)
        thumb = None
        json_path = os.path.join("resource", "scene", f"{scene_name}.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                img_filename = os.path.basename(data["image_path"])
                img_path = os.path.join("resource", "scene_img", img_filename)
                if os.path.exists(img_path):
                    thumb = pygame.image.load(img_path).convert()
                    thumb = pygame.transform.scale(thumb, (card_w, card_h))
        except:
            pass
        cards.append({
            "name": scene_name,
            "rect": pygame.Rect(x, y, card_w, card_h + 30),
            "thumb": thumb
        })
        col += 1
        if col >= cols:
            col = 0
            row += 1

    if cards:
        last_card = cards[-1]
        max_y = last_card["rect"].y + last_card["rect"].height + 20
        visible_h = sh - header_height - 20   # 底部留 20px
        max_scroll = max(0, max_y - visible_h)

    running = True
    title_font = get_font(40, bold=True)
    name_font = get_font(22)
    mouse_down_pos = None

    while running:
        screen.fill(BG_COLOR)
        sw, sh = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                voice_system.shutdown()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            # 鼠标按下记录位置
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down_pos = event.pos
            # 鼠标释放时判断是否为有效点击
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if mouse_down_pos is not None:
                    dx = event.pos[0] - mouse_down_pos[0]
                    dy = event.pos[1] - mouse_down_pos[1]
                    # 移动距离小于 5 像素视为点击
                    if (dx*dx + dy*dy) < 25:
                        for card in cards:
                            rect = card["rect"].copy()
                            rect.y -= scroll_y
                            if rect.collidepoint(event.pos):
                                selected_scene = card["name"]
                                running = False
                                break
                mouse_down_pos = None
            # 滚轮滚动
            if event.type == pygame.MOUSEWHEEL:
                scroll_y -= event.y * 30
                scroll_y = max(0, min(scroll_y, max_scroll))

        # 绘制滚动条背景（仅当内容超出时显示）
        scroll_bar_width = 12
        if max_scroll > 0:
            scroll_bar_x = sw - 30
            scroll_bar_height = sh - header_height * 2
            scroll_bar_rect = pygame.Rect(scroll_bar_x, header_height, scroll_bar_width, scroll_bar_height)
            pygame.draw.rect(screen, (200,200,200), scroll_bar_rect, border_radius=6)
            slider_height = max(40, scroll_bar_height * (sh - header_height) / max_y)
            slider_y = header_height + (scroll_y / max_scroll) * (scroll_bar_height - slider_height)
            slider_rect = pygame.Rect(scroll_bar_x, slider_y, scroll_bar_width, slider_height)
            pygame.draw.rect(screen, (100,100,100), slider_rect, border_radius=6)

        # 标题区域（固定在顶部，不受裁剪影响）
        title_surf = title_font.render("选择一个场景", True, BLUE)
        screen.blit(title_surf, ((sw - title_surf.get_width())//2, 30))
        hint_surf = font_hint.render("按 ESC 返回主菜单", True, DARK_GRAY)
        screen.blit(hint_surf, (20, sh - 30))

        # 设置裁剪区域（标题以下，底部留空），防止卡片溢出覆盖标题
        clip_rect = pygame.Rect(0, header_height, sw, sh - header_height)
        screen.set_clip(clip_rect)

        # 绘制所有卡片（应用滚动偏移）
        for card in cards:
            rect = card["rect"].copy()
            rect.y -= scroll_y
            # 简单可见性裁剪
            if rect.y + rect.height < header_height or rect.y > sh:
                continue
            draw_rounded_rect(screen, WHITE, (rect.x, rect.y, card_w, card_h), 0.1, shadow=True)
            if card["thumb"]:
                thumb_rect = pygame.Rect(rect.x+5, rect.y+5, card_w-10, card_h-10)
                screen.blit(card["thumb"], thumb_rect)
            name_surf = name_font.render(card["name"], True, BLACK)
            name_rect = name_surf.get_rect(center=(rect.centerx, rect.y + card_h + 15))
            screen.blit(name_surf, name_rect)

        # 取消裁剪，以便后续绘制不受影响
        screen.set_clip(None)

        pygame.display.flip()
        clock.tick(30)

    if selected_scene:
        globals()['game_mode'] = "scene"
        globals()['selected_scene_name'] = selected_scene
        game_loop()

# -------------------------- 主菜单 --------------------------
def main_menu():
    theme = themes.THEME_SOLARIZED.copy()
    theme.widget_font = get_font(36)
    theme.title_font = get_font(60, bold=True)
    theme.title_background_color = (70, 130, 230)
    theme.title_font_color = (255, 255, 255)

    menu = pygame_menu.Menu(
        title="Word Hunt - 单词射击游戏",
        width=current_width,
        height=current_height,
        theme=theme
    )
    menu.add.button("经典模式", run_classic_menu)
    menu.add.button("场景选词", run_scene_menu)
    menu.add.button("设置", run_settings_menu)
    menu.add.button("退出", pygame_menu.events.EXIT)
    menu.mainloop(screen)

if __name__ == "__main__":
    try:
        main_menu()
    finally:
        voice_system.shutdown()