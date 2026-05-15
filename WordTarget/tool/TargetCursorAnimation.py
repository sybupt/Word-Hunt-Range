from manim import *

# ─────────────────────────────────────────────
#  HIGH QUALITY TARGET CURSOR
#  64x64 | 透明背景 | 序列帧 PNG | 高清光标
# ─────────────────────────────────────────────
# manim -pql TargetCursorAnimation.py --format=png --transparent

WHITE = "#ffffff"
RED = "#ff3050"
BLUE = "#00d0ff"

class TargetCursorAnimation(Scene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera.frame_rate = 12
        self.camera.resolution = (64, 64)
        self.camera.background_color = None  # 透明

    def construct(self):
        # ── 高清精致靶心 ──
        outer = Circle(radius=0.52, stroke_color=BLUE, stroke_width=1.8, fill_opacity=0)
        inner = Circle(radius=0.20, stroke_color=WHITE, stroke_width=1.4, fill_opacity=0)
        dot = Dot(radius=0.06, color=RED, fill_opacity=1)

        # 十字线
        line_t = Line(UP * 0.45, UP * 0.20, stroke_color=WHITE, stroke_width=1.4)
        line_b = Line(DOWN * 0.45, DOWN * 0.20, stroke_color=WHITE, stroke_width=1.4)
        line_l = Line(LEFT * 0.45, LEFT * 0.20, stroke_color=WHITE, stroke_width=1.4)
        line_r = Line(RIGHT * 0.45, RIGHT * 0.20, stroke_color=WHITE, stroke_width=1.4)

        cross = VGroup(outer, inner, dot, line_t, line_b, line_l, line_r)
        cross.scale(0.82)
        cross.move_to(ORIGIN)

        self.add(cross)

        # ── 呼吸动画（高清流畅） ──
        self.play(
            cross.animate.scale(1.12),
            rate_func=smooth,
            run_time=0.6
        )
        self.play(
            cross.animate.scale(1.0),
            rate_func=smooth,
            run_time=0.6
        )

        self.wait(0.1)