from manim import *
import numpy as np

# ─────────────────────────────────────────────
#  Word-Hunt-Range  ·  Opening Animation
#  Manim Community Edition
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════
#  🔊 音效文件路径配置 —— 填入你的 mp3 路径即可
#  路径可以是相对路径（相对于本 py 文件）或绝对路径
#  留空字符串 "" 则该音效静默跳过，不报错
# ══════════════════════════════════════════════
SFX_CROSSHAIR_APPEAR = ""  # 准星出场
SFX_CROSSHAIR_PULSE = ""  # 准星脉冲缩放
SFX_WORDS_APPEAR = ""  # 单词集体上场
SFX_AIM = ""  # 准星移动瞄准
SFX_SHOOT = (
    "../WordTarget/assets/SFX/universfield-gunshot-352466.mp3"  # 射击爆炸（每次）
)
SFX_BIG_EXPLOSION = "../WordTarget/assets/SFX/universfield-gunshot-352466.mp3"  # 中心大爆炸（复用同一个）
SFX_TITLE_SWEEP = ""  # 标题扫入
SFX_BUTTON_APPEAR = ""  # 按钮出场
SFX_BUTTON_PULSE = ""  # 按钮呼吸闪烁

# ── 调色板 ──────────────────────────────────
BG = "#050810"
NEON_BLUE = "#00CFFF"
NEON_RED = "#FF2060"
NEON_PURP = "#BF00FF"
GRID_COL = "#0A1A2A"
GRID_LINE = "#0D2540"

WORD_COLORS = ["#00CFFF", "#39FF14", "#FFE000", "#FF6B00", "#FF4DC4", "#BF00FF"]


# ── 辅助：准星组件 ──────────────────────────
def make_crosshair(scale=1.0):
    """返回准星 VGroup，所有部件以 ORIGIN 为中心显式构建，保证红心居中"""
    outer = Circle(
        radius=0.55 * scale, stroke_color=NEON_BLUE, stroke_width=2.5, fill_opacity=0
    )
    outer.move_to(ORIGIN)

    inner = Circle(
        radius=0.22 * scale, stroke_color=WHITE, stroke_width=1.5, fill_opacity=0
    )
    inner.move_to(ORIGIN)

    # 用 Circle 填充代替 Dot，圆心精确在 ORIGIN（Dot 有内置锚点偏移）
    dot = Circle(
        radius=0.058 * scale, fill_color=NEON_RED, fill_opacity=1, stroke_opacity=0
    )
    dot.move_to(ORIGIN)

    line_len = 0.70 * scale
    gap = 0.27 * scale
    lines = VGroup(
        Line(LEFT * line_len, LEFT * gap, stroke_color=WHITE, stroke_width=1.5),
        Line(RIGHT * gap, RIGHT * line_len, stroke_color=WHITE, stroke_width=1.5),
        Line(UP * line_len, UP * gap, stroke_color=WHITE, stroke_width=1.5),
        Line(DOWN * gap, DOWN * line_len, stroke_color=WHITE, stroke_width=1.5),
    )

    tick_r = 0.60 * scale
    ticks = VGroup(
        *[
            Line(
                np.array([np.cos(a) * tick_r, np.sin(a) * tick_r, 0]),
                np.array(
                    [
                        np.cos(a) * (tick_r + 0.18 * scale),
                        np.sin(a) * (tick_r + 0.18 * scale),
                        0,
                    ]
                ),
                stroke_color=NEON_RED,
                stroke_width=2,
            )
            for a in [PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4]
        ]
    )

    ch = VGroup(outer, inner, dot, lines, ticks)
    ch.move_to(ORIGIN)  # 整体归中，消除 VGroup 包围盒偏移
    return ch


def make_shockwave(color=WHITE, max_r=1.2):
    """单个冲击波圆环"""
    c = Circle(radius=0.05, stroke_color=color, stroke_width=3, fill_opacity=0)
    return c


class WordHuntIntro(Scene):
    # ── 场景配置 ──────────────────────────────
    def setup(self):
        self.camera.background_color = BG

    # ════════════════════════════════════════════
    def construct(self):

        # ━━━ 1. 动态扫描线网格 ━━━━━━━━━━━━━━━━━
        grid = self._build_grid()
        self.add(grid)
        grid.add_updater(lambda m, dt: m.rotate(0.004 * dt, about_point=ORIGIN))

        # 中心径向光晕
        glow = self._build_glow()
        self.add(glow)

        # ━━━ 2. 准星出场 ━━━━━━━━━━━━━━━━━━━━━━
        ch = make_crosshair(scale=1.0)
        ch.move_to(ORIGIN)
        if SFX_CROSSHAIR_APPEAR:
            self.add_sound(SFX_CROSSHAIR_APPEAR)
        self.play(GrowFromCenter(ch), run_time=0.6)
        # 脉冲缩放
        if SFX_CROSSHAIR_PULSE:
            self.add_sound(SFX_CROSSHAIR_PULSE)
        self.play(ch.animate.scale(1.5), rate_func=there_and_back, run_time=0.5)
        self.play(ch.animate.scale(1.2), rate_func=there_and_back, run_time=0.3)

        # ━━━ 3. 单词上场 ━━━━━━━━━━━━━━━━━━━━━━
        # 六个区域各自随机取一个位置；x 范围收紧到 ±5.8，留出单词半宽余量
        # Manim 16:9 默认：x ∈ [-7.1, 7.1]，y ∈ [-4.0, 4.0]
        rng = np.random.default_rng(seed=42)
        zones = [
            (-5.8, -3.2, 2.0, 3.2),  # 左上
            (3.2, 5.8, 2.0, 3.2),  # 右上
            (-5.8, -4.0, -0.7, 0.7),  # 左中
            (4.0, 5.8, -0.7, 0.7),  # 右中
            (-5.8, -3.2, -3.2, -2.0),  # 左下
            (3.2, 5.8, -3.2, -2.0),  # 右下
        ]
        word_names = ["WORD", "HUNT", "RANGE", "TARGET", "VOCAB", "BLAST"]
        words_data = []
        for txt, (x0, x1, y0, y1) in zip(word_names, zones):
            rx = float(rng.uniform(x0, x1))
            ry = float(rng.uniform(y0, y1))
            words_data.append((txt, np.array([rx, ry, 0])))

        word_mobjects = []
        for (txt, pos), col in zip(words_data, WORD_COLORS):
            w = Text(txt, font="Courier New", font_size=38, weight=BOLD, color=col)
            w.move_to(pos)
            # 霓虹描边感
            w_bg = w.copy().set_color(col).set_opacity(0.25).scale(1.08)
            grp = VGroup(w_bg, w)

            # ── 后验裁剪：用稳定 API 获取包围盒边界 ──
            x_lim, y_lim = 6.55, 3.55
            x_min = grp.get_left()[0]
            x_max = grp.get_right()[0]
            y_min = grp.get_bottom()[1]
            y_max = grp.get_top()[1]
            dx = dy = 0.0
            if x_min < -x_lim:
                dx = -x_lim - x_min
            if x_max > x_lim:
                dx = x_lim - x_max
            if y_min < -y_lim:
                dy = -y_lim - y_min
            if y_max > y_lim:
                dy = y_lim - y_max
            if dx != 0.0 or dy != 0.0:
                grp.shift(np.array([dx, dy, 0]))

            word_mobjects.append(grp)

        if SFX_WORDS_APPEAR:
            self.add_sound(SFX_WORDS_APPEAR)
        self.play(
            LaggedStart(
                *[FadeIn(wm, shift=DOWN * 0.3, scale=0.8) for wm in word_mobjects],
                lag_ratio=0.12,
                run_time=1.2
            )
        )

        # ━━━ 4. 准星依次瞄准 & 射击 ━━━━━━━━━━━
        for i, (wm, (txt, pos), col) in enumerate(
            zip(word_mobjects, words_data, WORD_COLORS)
        ):

            # 4-a. 准星移动
            if SFX_AIM:
                self.add_sound(SFX_AIM)
            self.play(
                ch.animate.move_to(pos),
                rate_func=rate_functions.ease_in_out_sine,
                run_time=0.45,
            )
            self.wait(0.08)

            # 4-b. 瞄准闪光（准星变红）
            self.play(
                ch[0].animate.set_stroke(color=col), run_time=0.08  # 外环变单词色
            )

            # 4-c. 爆炸特效
            if SFX_SHOOT:
                self.add_sound(SFX_SHOOT)
            self._shoot_word(wm, pos, col)

            # 4-d. 准星恢复蓝色
            self.play(ch[0].animate.set_stroke(color=NEON_BLUE), run_time=0.06)

        # ━━━ 5. 准星回中心 ━━━━━━━━━━━━━━━━━━━━
        self.play(
            ch.animate.move_to(ORIGIN),
            rate_func=rate_functions.ease_in_out_sine,
            run_time=0.55,
        )
        self.wait(0.1)

        # ━━━ 6. 中心大爆炸 ━━━━━━━━━━━━━━━━━━━━
        if SFX_BIG_EXPLOSION:
            self.add_sound(SFX_BIG_EXPLOSION)
        self._big_explosion(ch)

        # ━━━ 7. 标题文字 ━━━━━━━━━━━━━━━━━━━━━━
        if SFX_TITLE_SWEEP:
            self.add_sound(SFX_TITLE_SWEEP)
        self._show_titles()

        # ━━━ 8. 开始按钮 ━━━━━━━━━━━━━━━━━━━━━━
        btn = self._build_button()
        if SFX_BUTTON_APPEAR:
            self.add_sound(SFX_BUTTON_APPEAR)
        self.play(GrowFromCenter(btn), run_time=0.5)
        # 呼吸 + 放大缩小 ×3：透明度 + scale 同步脉冲
        for _ in range(3):
            if SFX_BUTTON_PULSE:
                self.add_sound(SFX_BUTTON_PULSE)
            self.play(
                btn.animate.scale(1.12).set_opacity(0.4),
                rate_func=there_and_back,
                run_time=0.55,
            )
            self.wait(0.08)

        # ━━━ 9. 淡出 ━━━━━━━━━━━━━━━━━━━━━━━━━
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.9)
        self.wait(0.5)

    # ════════════════════════════════════════════
    #  内部方法
    # ════════════════════════════════════════════

    def _build_grid(self):
        """生成扫描线网格"""
        lines = VGroup()
        step = 0.8
        for x in np.arange(-9, 9.1, step):
            lines.add(
                Line(
                    [x, -5.5, 0],
                    [x, 5.5, 0],
                    stroke_color=GRID_LINE,
                    stroke_width=0.6,
                    stroke_opacity=0.55,
                )
            )
        for y in np.arange(-5.5, 5.6, step):
            lines.add(
                Line(
                    [-9, y, 0],
                    [9, y, 0],
                    stroke_color=GRID_LINE,
                    stroke_width=0.6,
                    stroke_opacity=0.55,
                )
            )
        return lines

    def _build_glow(self):
        """中心光晕（多层同心圆模拟渐变）"""
        glows = VGroup()
        for r, op in [(3.5, 0.04), (2.2, 0.07), (1.0, 0.10)]:
            c = Circle(
                radius=r, fill_color=NEON_BLUE, fill_opacity=op, stroke_opacity=0
            )
            glows.add(c)
        return glows

    def _shoot_word(self, wm, pos, col):
        """单词爆炸动画"""
        # 冲击波环
        sw1 = Circle(radius=0.1, stroke_color=col, stroke_width=3, fill_opacity=0)
        sw2 = Circle(radius=0.1, stroke_color=WHITE, stroke_width=2, fill_opacity=0)
        sw1.move_to(pos)
        sw2.move_to(pos)
        self.add(sw1, sw2)

        # 粒子碎片（简单线段模拟）
        sparks = VGroup()
        n = 10
        for k in range(n):
            angle = 2 * PI * k / n + np.random.uniform(-0.2, 0.2)
            length = np.random.uniform(0.18, 0.45)
            p = Line(
                pos,
                pos + np.array([np.cos(angle) * length, np.sin(angle) * length, 0]),
                stroke_color=col,
                stroke_width=2.5,
            )
            sparks.add(p)
        self.add(sparks)

        # 同步播放：单词淡出 + 冲击波扩散 + 粒子飞散
        self.play(
            FadeOut(wm, scale=1.6),
            sw1.animate.scale(12).set_stroke(opacity=0),
            sw2.animate.scale(7).set_stroke(opacity=0),
            sparks.animate.scale(3.0).set_stroke(opacity=0),
            run_time=0.32,
        )
        self.remove(sw1, sw2, sparks)

    def _big_explosion(self, ch):
        """中心大爆炸"""
        flash = Circle(radius=0.1, fill_color=WHITE, fill_opacity=1, stroke_opacity=0)
        flash.move_to(ORIGIN)
        self.add(flash)

        rings = VGroup(
            *[
                Circle(
                    radius=0.12, stroke_color=c, stroke_width=w, fill_opacity=0
                ).move_to(ORIGIN)
                for c, w in [
                    (WHITE, 5),
                    (NEON_BLUE, 3.5),
                    (NEON_RED, 3),
                    (NEON_PURP, 2.5),
                    (WHITE, 2),
                ]
            ]
        )
        self.add(rings)

        # 准星消失
        self.play(
            FadeOut(ch, scale=0.4),
            flash.animate.scale(30).set_fill(opacity=0),
            rings.animate.scale(18).set_stroke(opacity=0),
            run_time=0.55,
        )
        self.remove(flash, rings, ch)
        self.wait(0.08)

    def _show_titles(self):
        """爆炸后标题登场"""
        # ── 主标题 ──
        title = Text("Word-Hunt-Range", font="Courier New", font_size=64, weight=BOLD)
        # 蓝→红渐变（用 set_color_by_gradient）
        title.set_color_by_gradient(NEON_BLUE, NEON_RED)
        title.move_to(UP * 2.5)

        # 金属光泽描边
        title_glow = (
            title.copy()
            .set_fill(opacity=0)
            .set_stroke(color=WHITE, width=0.8, opacity=0.5)
        )

        # ── 副标题 ──
        sub = Text("射击 · 单词", font="PingFang SC", font_size=30, color="#CCDDEE")
        sub.next_to(title, DOWN, buff=0.45)

        # ── 技术标签 ──
        tag = Text(
            "ESP32 + 智能硬件  |  词汇射击",
            font="Courier New",
            font_size=20,
            color="#4DAACC",
        )
        tag.next_to(sub, DOWN, buff=0.55)

        # 横线装饰
        line_l = Line(LEFT * 2.8, LEFT * 0.3, stroke_color=NEON_BLUE, stroke_width=1.5)
        line_r = Line(RIGHT * 0.3, RIGHT * 2.8, stroke_color=NEON_RED, stroke_width=1.5)
        deco = VGroup(line_l, line_r).next_to(sub, DOWN, buff=0.20)

        # 冲击波扫入主标题
        sweep = Line(LEFT * 9, LEFT * 9, stroke_color=WHITE, stroke_width=4)
        sweep.move_to(UP * 2.5)
        self.add(sweep)
        self.play(
            sweep.animate.put_start_and_end_on(LEFT * 9, RIGHT * 9), run_time=0.22
        )
        self.play(
            FadeIn(title, title_glow, shift=DOWN * 0.2, scale=0.92),
            FadeOut(sweep),
            run_time=0.30,
        )
        self.play(Write(sub), GrowFromCenter(deco), run_time=0.5)
        self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.35)

    def _build_button(self):
        """START HUNTING 按钮：绿色边框 + 半透明填充，白色文字高对比度"""
        rect = RoundedRectangle(
            corner_radius=0.22,
            width=3.8,
            height=0.76,
            stroke_color="#00FF88",
            stroke_width=3.0,
            fill_color="#003322",
            fill_opacity=0.85,
        )
        label = Text(
            "START HUNTING", font="Courier New", font_size=22, weight=BOLD, color=WHITE
        )  # 白色文字，与绿底高对比
        label.move_to(rect.get_center())
        btn = VGroup(rect, label)
        btn.move_to(DOWN * 3.3)
        return btn
