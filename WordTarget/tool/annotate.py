import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw

# 支持的图片格式
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


class PointAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("标点工具 - 支持多点标记与标签管理")
        self.root.geometry("1400x800")

        # ---------- 数据变量 ----------
        self.image_paths = []  # 图片路径列表
        self.current_idx = -1  # 当前图片索引
        self.orig_img = None  # 原始PIL图像
        self.disp_img = None  # 显示用的PIL图像
        self.disp_tk = None  # 显示用的ImageTk对象
        self.disp_w = 0  # 显示宽度
        self.disp_h = 0  # 显示高度
        self.orig_w = 0  # 原始宽度
        self.orig_h = 0  # 原始高度

        # 标注数据: 扁平点列表 [ {"label_en": "book", "label_cn": "书", "x": 120, "y": 350}, ... ]
        self.points = []
        # 标签字典: {"book": "书", "pen": "笔"}
        self.labels = {}
        # 当前选中的标签（英文key）
        self.current_label = None

        # ---------- UI布局 ----------
        # 主框架：左侧画布 + 右侧控制面板
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧画布
        self.canvas = tk.Canvas(main_frame, bg="#2d2d2d", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧面板（Notebook标签页）
        right_panel = tk.Frame(main_frame, width=280)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        right_panel.pack_propagate(False)

        # 笔记本控件
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        # ---- 标签管理页面 ----
        label_frame = tk.Frame(notebook)
        notebook.add(label_frame, text="🏷️ 标签管理")

        # 当前选中标签提示
        self.label_status = tk.Label(
            label_frame, text="当前标签: 未选中", fg="blue", anchor="w"
        )
        self.label_status.pack(fill=tk.X, padx=5, pady=5)

        # 标签列表 (带滚动条)
        label_list_frame = tk.Frame(label_frame)
        label_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(label_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.label_listbox = tk.Listbox(
            label_list_frame,
            yscrollcommand=scrollbar.set,
            font=("微软雅黑", 10),
            height=12,
        )
        self.label_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.label_listbox.yview)
        self.label_listbox.bind("<<ListboxSelect>>", self.on_label_selected)

        # 标签操作按钮
        btn_frame = tk.Frame(label_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(
            btn_frame, text="➕ 新增标签", command=self.add_new_label, width=10
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            btn_frame, text="🗑️ 删除标签", command=self.delete_selected_label, width=10
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            btn_frame, text="✨ 使用选中标签", command=self.use_selected_label, width=12
        ).pack(side=tk.RIGHT, padx=2)

        tk.Label(
            label_frame, text="提示: 点击图片添加点，将使用当前标签", fg="gray"
        ).pack(pady=2)

        # ---- 点列表页面 ----
        point_frame = tk.Frame(notebook)
        notebook.add(point_frame, text="📍 当前标注点")

        point_list_frame = tk.Frame(point_frame)
        point_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        point_scroll = tk.Scrollbar(point_list_frame)
        point_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.point_listbox = tk.Listbox(
            point_list_frame,
            yscrollcommand=point_scroll.set,
            font=("微软雅黑", 9),
            height=18,
        )
        self.point_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        point_scroll.config(command=self.point_listbox.yview)
        # 右键删除点
        self.point_listbox.bind("<Button-3>", self.show_point_menu)

        # 点操作按钮
        point_btn_frame = tk.Frame(point_frame)
        point_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(
            point_btn_frame,
            text="🗑️ 删除选中点",
            command=self.delete_selected_point,
            width=12,
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            point_btn_frame,
            text="🗑️ 清空所有点",
            command=self.clear_all_points,
            width=12,
        ).pack(side=tk.RIGHT, padx=2)

        # ---- 底部控制栏 ----
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            control_frame, text="📂 选择图片文件夹", command=self.load_folder, width=15
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            control_frame, text="◀ 上一张", command=self.prev_image, width=8
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            control_frame, text="下一张 ▶ (自动保存)", command=self.next_image, width=15
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            control_frame,
            text="💾 手动保存",
            command=self.save_current_annotation,
            width=10,
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            control_frame,
            text="❌ 清除所有当前点",
            command=self.clear_all_points,
            width=12,
        ).pack(side=tk.LEFT, padx=5)
        self.file_label = tk.Label(control_frame, text="未加载图片", fg="gray")
        self.file_label.pack(side=tk.RIGHT, padx=10)

        # 绑定鼠标点击画布添加点
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # 绑定窗口大小变化
        self.canvas.bind("<Configure>", self.on_resize)

    # ====================== 坐标转换 ======================
    def img_to_canvas(self, x_img, y_img):
        """原始图像坐标 -> 画布坐标 (基于当前显示比例)"""
        if self.orig_w == 0 or self.orig_h == 0:
            return 0, 0
        scale_x = self.disp_w / self.orig_w
        scale_y = self.disp_h / self.orig_h
        return int(x_img * scale_x), int(y_img * scale_y)

    def canvas_to_img(self, cx, cy):
        """画布坐标 -> 原始图像坐标 (需确保点在显示图像范围内)"""
        # 判断是否在显示区域内
        if cx < 0 or cy < 0 or cx > self.disp_w or cy > self.disp_h:
            return None
        if self.orig_w == 0 or self.orig_h == 0:
            return None
        scale_x = self.orig_w / self.disp_w
        scale_y = self.orig_h / self.disp_h
        return int(cx * scale_x), int(cy * scale_y)

    # ====================== 显示图片与标注 ======================
    def show_image(self):
        """显示当前图片，并绘制所有已有点"""
        if not self.image_paths or self.current_idx < 0:
            return

        img_path = self.image_paths[self.current_idx]
        # 加载原始图像
        self.orig_img = Image.open(img_path).convert("RGB")
        self.orig_w, self.orig_h = self.orig_img.size

        # 适应画布大小计算显示尺寸
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = 800
        if canvas_h <= 1:
            canvas_h = 600

        # 保持比例缩放
        ratio = min(canvas_w / self.orig_w, canvas_h / self.orig_h)
        self.disp_w = int(self.orig_w * ratio)
        self.disp_h = int(self.orig_h * ratio)
        self.disp_img = self.orig_img.resize(
            (self.disp_w, self.disp_h), Image.Resampling.LANCZOS
        )
        self.disp_tk = ImageTk.PhotoImage(self.disp_img)

        # 清空画布并显示图片
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.disp_tk)
        self.root.title(
            f"标点工具 - {os.path.basename(img_path)}   (尺寸: {self.orig_w}x{self.orig_h})"
        )
        self.file_label.config(
            text=f"{os.path.basename(img_path)}  ({len(self.points)}个点)"
        )

        # 绘制所有点
        self.draw_all_points()

    def draw_all_points(self):
        """在画布上绘制所有点（圆圈 + 标签文字）"""
        # 按标签分组颜色（简单哈希）
        colors = [
            "#FF3333",
            "#33FF33",
            "#3399FF",
            "#FFCC33",
            "#FF33CC",
            "#33CCCC",
            "#FF6633",
        ]
        for idx, point in enumerate(self.points):
            cx, cy = self.img_to_canvas(point["x"], point["y"])
            # 标签英文缩写
            label_short = point["label_en"][:2].upper()
            # 根据标签英文决定颜色
            color = colors[hash(point["label_en"]) % len(colors)]
            # 画圆点
            r = 6
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r, fill=color, outline="white", width=1
            )
            # 显示标签文字
            self.canvas.create_text(
                cx + r + 2,
                cy - r - 2,
                text=f"{label_short}",
                anchor=tk.NW,
                fill=color,
                font=("微软雅黑", 8, "bold"),
            )
            # 添加序号
            self.canvas.create_text(
                cx - r - 2,
                cy - r - 2,
                text=str(idx + 1),
                anchor=tk.NE,
                fill="yellow",
                font=("微软雅黑", 7),
            )

    def refresh_display(self):
        """刷新画布显示（重绘背景和所有点）"""
        if self.disp_tk:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.disp_tk)
            self.draw_all_points()
            self.file_label.config(
                text=f"{os.path.basename(self.image_paths[self.current_idx])}  ({len(self.points)}个点)"
            )
            self.update_point_listbox()
            self.update_label_listbox()

    # ====================== 点与标签管理 ======================
    def add_point(self, x, y, label_en, label_cn):
        """新增一个标注点"""
        self.points.append({"label_en": label_en, "label_cn": label_cn, "x": x, "y": y})
        self.refresh_display()

    def add_new_label(self):
        """添加新标签（英文+中文）"""
        en = simpledialog.askstring(
            "新增标签", "请输入标签英文名称（用作key）:", parent=self.root
        )
        if not en or en.strip() == "":
            return
        en = en.strip()
        if en in self.labels:
            messagebox.showwarning("重复标签", f"标签 '{en}' 已存在，不能重复添加。")
            return
        cn = simpledialog.askstring(
            "新增标签", f"请输入标签 '{en}' 的中文名称:", parent=self.root
        )
        if not cn:
            cn = en
        self.labels[en] = cn.strip()
        # 自动将当前标签设置为新添加的标签
        self.current_label = en
        self.label_status.config(text=f"当前标签: {en} ({self.labels[en]})")
        self.update_label_listbox()
        messagebox.showinfo("成功", f"标签 {en} 已添加，并设为当前使用标签。")

    def delete_selected_label(self):
        """删除选中的标签，同时删除所有具有该标签的点"""
        selection = self.label_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在标签列表中选中要删除的标签。")
            return
        label_en = self.label_listbox.get(selection[0]).split(" : ")[0]
        if messagebox.askyesno(
            "确认删除", f"确定要删除标签 '{label_en}' 及其关联的所有点吗？"
        ):
            # 删除该标签的所有点
            new_points = [p for p in self.points if p["label_en"] != label_en]
            removed_count = len(self.points) - len(new_points)
            self.points = new_points
            # 删除标签字典中的条目
            del self.labels[label_en]
            # 如果当前选中的标签被删了，清空当前标签
            if self.current_label == label_en:
                self.current_label = None
                self.label_status.config(text="当前标签: 未选中")
            self.update_label_listbox()
            self.refresh_display()
            messagebox.showinfo(
                "完成", f"已删除标签 '{label_en}' 及其 {removed_count} 个标注点。"
            )

    def on_label_selected(self, event):
        """点击标签列表时，高亮但不变更当前标签，需要点击“使用选中标签”按钮手动变更"""
        pass

    def use_selected_label(self):
        """将标签列表中选中的标签设为当前使用标签"""
        selection = self.label_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在标签列表中选中一个标签。")
            return
        label_en = self.label_listbox.get(selection[0]).split(" : ")[0]
        self.current_label = label_en
        self.label_status.config(text=f"当前标签: {label_en} ({self.labels[label_en]})")
        messagebox.showinfo(
            "已切换", f"当前标注将使用标签: {label_en} - {self.labels[label_en]}"
        )

    def update_label_listbox(self):
        """刷新右侧标签列表显示"""
        self.label_listbox.delete(0, tk.END)
        for en, cn in self.labels.items():
            self.label_listbox.insert(tk.END, f"{en} : {cn}")

    def update_point_listbox(self):
        """刷新右侧点列表"""
        self.point_listbox.delete(0, tk.END)
        for idx, pt in enumerate(self.points):
            self.point_listbox.insert(
                tk.END, f"{idx+1}. [{pt['label_en']}] ({pt['x']},{pt['y']})"
            )

    def delete_selected_point(self):
        """删除右侧选中的点"""
        selection = self.point_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在点列表中选中要删除的点。")
            return
        idx = selection[0]
        if 0 <= idx < len(self.points):
            del self.points[idx]
            self.refresh_display()
            messagebox.showinfo("完成", "已删除选中的标注点。")

    def show_point_menu(self, event):
        """右键菜单删除点"""
        widget = event.widget
        idx = widget.nearest(event.y)
        if idx < 0 or idx >= len(self.points):
            return
        if messagebox.askyesno("删除点", f"确定要删除点 #{idx+1} 吗？"):
            del self.points[idx]
            self.refresh_display()

    def clear_all_points(self):
        """清空当前图片所有点"""
        if not self.points:
            return
        if messagebox.askyesno("清空所有点", "确定要清空当前图片的所有标注点吗？"):
            self.points.clear()
            self.refresh_display()

    # ====================== 鼠标点击添加点 ======================
    def on_canvas_click(self, event):
        """点击画布，添加一个标注点"""
        if not self.orig_img:
            messagebox.showwarning("提示", "请先加载图片。")
            return

        # 转换到图像坐标
        img_coord = self.canvas_to_img(event.x, event.y)
        if img_coord is None:
            messagebox.showwarning("提示", "点击位置超出图像区域，请在图像范围内点击。")
            return
        x, y = img_coord

        # 检查当前是否有选中的标签
        if self.current_label is None or self.current_label not in self.labels:
            # 如果没有选中标签，提示先去选择/新建标签
            answer = messagebox.askyesno(
                "未选中标签", "当前没有选中的标签。是否要立即新建一个标签？"
            )
            if answer:
                self.add_new_label()
                if self.current_label is None:
                    return
            else:
                return

        # 添加新点
        self.add_point(x, y, self.current_label, self.labels[self.current_label])

    # ====================== 文件保存与加载 ======================
    def save_current_annotation(self):
        """保存当前图片的标注为JSON (按照book:{pos:[], chinese:书}格式)"""
        if not self.image_paths or self.current_idx < 0:
            return

        # 将points列表转换为分组JSON结构
        annotation_dict = {}
        for pt in self.points:
            label_en = pt["label_en"]
            if label_en not in annotation_dict:
                annotation_dict[label_en] = {
                    "pos": [],
                    "chinese": pt["label_cn"],  # 使用该标签第一次出现的中文
                }
            annotation_dict[label_en]["pos"].append([pt["x"], pt["y"]])
            # 确保chinese字段一致（如有多个点使用同一标签，中文统一）
            if annotation_dict[label_en]["chinese"] != pt["label_cn"]:
                # 理论上同一个标签对应的中文应当一致，如果不一致则提示
                pass

        # 保存JSON到同级目录
        img_path = self.image_paths[self.current_idx]
        img_name = os.path.basename(img_path)
        json_name = os.path.splitext(img_name)[0] + ".json"
        json_path = os.path.join(SAVE_DIR, json_name)

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(annotation_dict, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存成功", f"标注已保存至:\n{json_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存出错: {e}")

    def load_annotation(self):
        """加载当前图片对应的JSON标注文件，恢复到self.points和self.labels"""
        if not self.image_paths or self.current_idx < 0:
            return

        img_path = self.image_paths[self.current_idx]
        img_name = os.path.basename(img_path)
        json_name = os.path.splitext(img_name)[0] + ".json"
        json_path = os.path.join(SAVE_DIR, json_name)

        if not os.path.exists(json_path):
            self.points = []
            self.labels = {}
            self.current_label = None
            self.label_status.config(text="当前标签: 未选中")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 解析数据，重建 points 和 labels
            new_points = []
            new_labels = {}
            for label_en, info in data.items():
                chinese = info.get("chinese", label_en)
                new_labels[label_en] = chinese
                pos_list = info.get("pos", [])
                for x, y in pos_list:
                    new_points.append(
                        {"label_en": label_en, "label_cn": chinese, "x": x, "y": y}
                    )
            self.points = new_points
            self.labels = new_labels
            # 默认不自动选中任何标签
            self.current_label = None if not new_labels else list(new_labels.keys())[0]
            if self.current_label:
                self.label_status.config(
                    text=f"当前标签: {self.current_label} ({self.labels[self.current_label]})"
                )
            else:
                self.label_status.config(text="当前标签: 未选中")
        except Exception as e:
            messagebox.showerror("加载失败", f"读取JSON出错: {e}")
            self.points = []
            self.labels = {}

    # ====================== 图片导航 ======================
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        paths = []
        for f in os.listdir(folder):
            if f.lower().endswith(IMAGE_EXTS):
                paths.append(os.path.join(folder, f))
        if not paths:
            messagebox.showwarning("提示", "文件夹中没有找到支持的图片格式")
            return
        self.image_paths = sorted(paths)
        self.current_idx = 0
        self.load_annotation()  # 加载第一张的标注
        self.show_image()
        self.update_label_listbox()
        self.update_point_listbox()

    def next_image(self):
        if not self.image_paths:
            return
        # 先保存当前图片标注
        self.save_current_annotation()
        if self.current_idx < len(self.image_paths) - 1:
            self.current_idx += 1
            self.load_annotation()
            self.show_image()
            self.update_label_listbox()
            self.update_point_listbox()
        else:
            messagebox.showinfo("完成", "已是最后一张图片，标注已保存。")

    def prev_image(self):
        if not self.image_paths:
            return
        if self.current_idx > 0:
            self.save_current_annotation()
            self.current_idx -= 1
            self.load_annotation()
            self.show_image()
            self.update_label_listbox()
            self.update_point_listbox()
        else:
            messagebox.showinfo("提示", "已是第一张图片")

    def on_resize(self, event):
        """窗口大小变化时重新适配图片"""
        if self.orig_img:
            self.show_image()
            self.refresh_display()


# 全局保存目录（脚本所在目录）
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    root = tk.Tk()
    app = PointAnnotator(root)
    root.mainloop()
