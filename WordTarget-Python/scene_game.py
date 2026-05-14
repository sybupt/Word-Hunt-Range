import pygame
import random
import os
import json
import sys
import re

JSON_DIR = os.path.join("resource", "scene")
IMG_DIR = os.path.join("resource", "scene_img")

# -------------------------- 字体工具（支持中文） --------------------------
def get_font(size, bold=False):
    font_names = [
        "Microsoft YaHei", "SimHei", "Arial",
        "PingFang SC", "Heiti TC", "WenQuanYi Micro Hei",
        "Noto Sans CJK SC", "freesans", "sans-serif"
    ]
    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            test_surf = font.render("测试", True, (30, 30, 30))
            if test_surf.get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)

# -------------------------- 描边文字绘制 --------------------------
def draw_text_with_outline(surface, text, font, text_color, outline_color, pos):
    x, y = pos
    # 四个方向绘制轮廓
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        outline_surf = font.render(text, True, outline_color)
        surface.blit(outline_surf, (x+dx, y+dy))
    text_surf = font.render(text, True, text_color)
    surface.blit(text_surf, pos)

# -------------------------- 长中文截断 --------------------------
def shorten_chinese_text(text, max_width, font):
    if font.render(text, True, (30,30,30)).get_width() <= max_width:
        return text
    # 按词性缩写分段
    pos_pattern = r'(?:n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|art\.|int\.|aux\.|num\.|det\.|abbr\.)\s*'
    matches = list(re.finditer(pos_pattern, text))
    if matches:
        last_match = matches[-1]
        short = text[last_match.start():].strip()
        if font.render(short, True, (30,30,30)).get_width() <= max_width:
            return short
    # 逐字截断并加…
    short = text
    while len(short) > 0:
        short = short[:-1]
        if font.render(short + "…", True, (30,30,30)).get_width() <= max_width:
            return short + "…"
    return "…"

# -------------------------- 场景加载 --------------------------
def load_scene(scene_name):
    json_path = os.path.join(JSON_DIR, f"{scene_name}.json")
    if not os.path.exists(json_path):
        print(f"场景JSON {json_path} 不存在")
        return None, None, None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    img_filename = os.path.basename(data["image_path"])
    img_path = os.path.join(IMG_DIR, img_filename)
    if not os.path.exists(img_path):
        print(f"场景图片 {img_path} 不存在")
        return None, None, None

    original_img = pygame.image.load(img_path).convert()
    orig_w, orig_h = original_img.get_size()
    return original_img, data["annotations"], (orig_w, orig_h)

def get_scene_list():
    if not os.path.exists(JSON_DIR):
        return []
    return [f[:-5] for f in os.listdir(JSON_DIR) if f.endswith(".json")]

# -------------------------- 场景游戏主循环 --------------------------
def scene_game_loop(screen, clock, voice_system, settings):
    import pygame.display
    from pygame import Rect
    import time

    scene_name = settings.get("scene_name")
    if not scene_name:
        scenes = get_scene_list()
        if not scenes:
            return 0
        scene_name = random.choice(scenes)

    original_img, annotations, (orig_w, orig_h) = load_scene(scene_name)
    if not original_img or not annotations:
        return 0

    sw, sh = screen.get_size()
    bg_img = pygame.transform.scale(original_img, (sw, sh))
    scale_x = sw / orig_w
    scale_y = sh / orig_h

    score = 0
    start_ticks = pygame.time.get_ticks()
    game_time = settings.get("game_time", 60)
    target_word = None
    options = []
    show_feedback = False
    feedback_color = None
    feedback_timer = 0

    # 字体
    font_card = get_font(20)           # 卡片文字
    font_ui = get_font(28, bold=True)  # 顶部 UI
    font_prompt = get_font(42, bold=True)  # 目标单词

    def generate_round():
        nonlocal target_word, options, show_feedback, feedback_color
        show_feedback = False
        options.clear()

        words = list(annotations.keys())
        if len(words) < 3:
            return False

        target_word = random.choice(words)
        other_words = [w for w in words if w != target_word]
        if len(other_words) >= 4:
            selected = random.sample(other_words, 4)
        else:
            selected = other_words[:]
        selected.append(target_word)
        random.shuffle(selected)

        # 卡片尺寸缩小，减轻重叠
        card_w, card_h = 160, 50
        max_card_width = 240   # 文本超宽时自动扩展但不超过此值

        for word in selected:
            entry = annotations[word]
            pos_list = entry["pos"]
            x, y = random.choice(pos_list)
            screen_x = int(x * scale_x)
            screen_y = int(y * scale_y)

            # 截断过长的中文
            chinese = entry["chinese"]
            chinese = shorten_chinese_text(chinese, max_card_width - 20, font_card)

            # 计算实际卡片宽度
            text_surf = font_card.render(chinese, True, (30,30,30))
            desired_w = min(text_surf.get_width() + 20, max_card_width)
            card_width = max(card_w, desired_w)

            # 确保卡片不超出屏幕
            card_x = max(10, min(screen_x - card_width // 2, sw - card_width - 10))
            card_y = max(10, min(screen_y - card_h // 2, sh - card_h - 10))

            rect = Rect(card_x, card_y, card_width, card_h)
            options.append({
                "word": word,
                "chinese": chinese,
                "rect": rect,
                "is_target": word == target_word
            })

        voice_system.speak(target_word)
        return True

    if not generate_round():
        return 0

    running = True
    while running:
        dt = clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                voice_system.shutdown()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        if mouse_click and not show_feedback:
            for opt in options:
                if opt["rect"].collidepoint(mouse_pos):
                    if opt["is_target"]:
                        score += 10
                        feedback_color = (50, 210, 80)
                    else:
                        feedback_color = (255, 70, 70)
                    show_feedback = True
                    feedback_timer = 20
                    break

        if show_feedback:
            feedback_timer -= 1
            if feedback_timer <= 0:
                show_feedback = False
                if not generate_round():
                    running = False

        elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
        remaining = game_time - elapsed
        if remaining <= 0:
            running = False

        # 绘制背景
        screen.blit(bg_img, (0, 0))

        # 绘制顶部 UI：得分、剩余时间、目标单词（带黑边白字）
        # 得分和剩余时间位于左上角，目标单词居中
        draw_text_with_outline(screen, f"得分: {score}", font_ui, (255,255,255), (0,0,0), (20, 20))
        draw_text_with_outline(screen, f"剩余: {remaining}s", font_ui, (255,255,255), (0,0,0), (20, 55))
        # 目标单词居中显示
        prompt_text = target_word if target_word else ""
        prompt_surf = font_prompt.render(prompt_text, True, (255,255,255))
        prompt_rect = prompt_surf.get_rect(center=(sw//2, 40))
        # 先画黑色描边
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            outline = font_prompt.render(prompt_text, True, (0,0,0))
            screen.blit(outline, prompt_rect.move(dx, dy))
        screen.blit(prompt_surf, prompt_rect)

        # 绘制选项卡片
        for opt in options:
            rect = opt["rect"]
            # 卡片背景
            card_color = (255, 255, 255, 230)
            if show_feedback and opt["is_target"]:
                card_color = (*feedback_color, 200)
            # 简单阴影
            pygame.draw.rect(screen, (0,0,0,80), rect.inflate(4,4), border_radius=10)
            card_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            card_surf.fill(card_color)
            screen.blit(card_surf, rect.topleft)
            # 文字
            text_surf = font_card.render(opt["chinese"], True, (30,30,30))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        pygame.display.flip()

    return score