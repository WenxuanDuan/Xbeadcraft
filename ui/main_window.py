from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.color_matcher import ColorMatcher
from core.image_processor import ImageProcessor
from core.palette import Palette
from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PALETTE_PATH = PROJECT_ROOT / "data" / "mard_221.csv"


class PatternPreview(QLabel):
    """Selection is painted as an overlay, never into the exported sheet."""

    def __init__(self, window):
        super().__init__("请选择一张图片，然后点击“生成图纸”。")
        self.window = window

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.window._select_cell(event.position(), event.modifiers())
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        window = self.window
        if window.pattern is None or window.render_config is None:
            return
        left, top, cell = window._grid_geometry()
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#0066ff"), 3))
        for x, y in window.selected_cells:
            if window.render_config.mirror_horizontal:
                x = window.pattern.width - 1 - x
            painter.drawRect(QRect(left+x*cell+2, top+y*cell+2, cell-4, cell-4))


class MainWindow(QMainWindow):
    """
    XBeadCraft 主窗口。

    当前支持：
    - 打开图片
    - 固定宽度、固定高度、固定最长边
    - 图鉴模式：按目标拼豆数量统一视觉体量
    - MARD 色卡自动匹配
    - 生成完整拼豆图纸
    - 保存 PNG
    """

    def __init__(self) -> None:
        super().__init__()

        self.selected_cells: set[tuple[int, int]] = set()
        self.edit_history: list[dict[tuple[int, int], int]] = []
        self.pattern: Pattern | None = None
        self.render_config: RenderConfig | None = None
        self.source_path: Path | None = None
        self.sheet_image: Image.Image | None = None
        self.sheet_pixmap: QPixmap | None = None

        self.palette = self._load_palette()
        self.processor = ImageProcessor()
        self.matcher = ColorMatcher(self.palette)

        self.setWindowTitle("XBeadCraft")
        self.resize(1320, 860)

        self._build_menu()
        self._build_ui()
        self._build_status_bar()

    def _load_palette(self) -> Palette:
        if not PALETTE_PATH.exists():
            raise FileNotFoundError(
                "找不到 MARD 色卡文件：\n"
                f"{PALETTE_PATH}\n\n"
                "请将色卡保存为 data/mard_221.csv。"
            )

        return Palette(str(PALETTE_PATH))

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")

        open_action = QAction("打开图片…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)

        save_action = QAction("保存图纸…", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_sheet)

        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        controls = self._create_control_panel()
        preview = self._create_preview_panel()

        control_scroll = QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setFixedWidth(335)
        control_scroll.setWidget(controls)
        root_layout.addWidget(control_scroll)
        root_layout.addWidget(preview, stretch=1)

    def _create_control_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedWidth(310)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(13)

        title = QLabel("图纸设置")
        title.setStyleSheet(
            "font-size: 20px;"
            "font-weight: 600;"
        )
        layout.addWidget(title)

        self.file_label = QLabel("尚未选择图片")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(
            "color: #666666;"
            "padding: 8px;"
            "border: 1px solid #d6d6d6;"
            "border-radius: 6px;"
        )
        layout.addWidget(self.file_label)

        open_button = QPushButton("选择图片")
        open_button.clicked.connect(self.open_image)
        layout.addWidget(open_button)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.size_mode_combo = QComboBox()
        self.size_mode_combo.addItem(
            "图鉴模式（推荐）",
            "collection",
        )
        self.size_mode_combo.addItem(
            "固定最长边",
            "longest",
        )
        self.size_mode_combo.addItem(
            "固定宽度",
            "width",
        )
        self.size_mode_combo.addItem(
            "固定高度",
            "height",
        )
        self.size_mode_combo.currentIndexChanged.connect(
            self._update_size_controls
        )
        form.addRow("尺寸模式：", self.size_mode_combo)

        self.collection_size_combo = QComboBox()
        self.collection_size_combo.addItem(
            "小型图鉴 · 约550颗",
            550,
        )
        self.collection_size_combo.addItem(
            "标准图鉴 · 约850颗",
            850,
        )
        self.collection_size_combo.addItem(
            "大型图鉴 · 约1200颗",
            1200,
        )
        self.collection_size_combo.setCurrentIndex(1)
        form.addRow("图鉴规格：", self.collection_size_combo)

        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(4, 200)
        self.target_size_spin.setValue(40)
        self.target_size_spin.setSuffix(" 颗")
        form.addRow("目标尺寸：", self.target_size_spin)

        self.cell_size_spin = QSpinBox()
        self.cell_size_spin.setRange(18, 60)
        self.cell_size_spin.setValue(30)
        self.cell_size_spin.setSuffix(" px")
        form.addRow("格子大小：", self.cell_size_spin)

        self.major_grid_spin = QSpinBox()
        self.major_grid_spin.setRange(1, 20)
        self.major_grid_spin.setValue(5)
        self.major_grid_spin.setSuffix(" 格")
        form.addRow("粗线间隔：", self.major_grid_spin)

        self.alpha_spin = QSpinBox()
        self.alpha_spin.setRange(0, 255)
        self.alpha_spin.setValue(128)
        form.addRow("透明阈值：", self.alpha_spin)

        layout.addLayout(form)

        self.keep_ratio_check = QCheckBox("保持原图比例")
        self.keep_ratio_check.setChecked(True)
        layout.addWidget(self.keep_ratio_check)

        self.trim_check = QCheckBox("裁掉透明边缘")
        self.trim_check.setChecked(True)
        layout.addWidget(self.trim_check)

        self.show_color_check = QCheckBox("显示颜色背景")
        self.show_color_check.setChecked(True)
        layout.addWidget(self.show_color_check)

        self.coordinate_check = QCheckBox("显示四边坐标")
        self.coordinate_check.setChecked(True)
        layout.addWidget(self.coordinate_check)

        self.checkerboard_check = QCheckBox(
            "透明区域显示棋盘格"
        )
        self.checkerboard_check.setChecked(True)
        layout.addWidget(self.checkerboard_check)

        generate_button = QPushButton("生成图纸")
        generate_button.setMinimumHeight(42)
        generate_button.setStyleSheet(
            "font-size: 16px;"
            "font-weight: 600;"
        )
        generate_button.clicked.connect(self.generate_sheet)
        layout.addWidget(generate_button)

        self.mirror_check = QCheckBox("水平镜像")
        self.mirror_check.setEnabled(False)
        self.mirror_check.toggled.connect(self._toggle_mirror)
        layout.addWidget(self.mirror_check)

        self.save_button = QPushButton("保存 PNG")
        self.save_button.setMinimumHeight(38)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_sheet)
        layout.addWidget(self.save_button)

        self.selection_label = QLabel("点击图纸选格；按住 Ctrl / ⌘ 可多选")
        self.selection_label.setWordWrap(True)
        layout.addWidget(self.selection_label)

        layout.addWidget(QLabel("按色号全选（当前图纸）："))
        self.source_color_combo = QComboBox()
        self.source_color_combo.setEnabled(False)
        layout.addWidget(self.source_color_combo)

        self.select_color_button = QPushButton("全选此色号")
        self.select_color_button.setEnabled(False)
        self.select_color_button.clicked.connect(self.select_all_of_color)
        layout.addWidget(self.select_color_button)

        self.color_combo = QComboBox()
        for index, color in enumerate(self.palette.colors):
            swatch = QPixmap(20, 20)
            swatch.fill(QColor(*color.rgb))
            self.color_combo.addItem(QIcon(swatch), color.code, index)
        self.color_combo.setEnabled(False)
        layout.addWidget(QLabel("替换颜色（MARD 221）："))
        layout.addWidget(self.color_combo)

        self.replace_button = QPushButton("替换选中像素")
        self.replace_button.setEnabled(False)
        self.replace_button.clicked.connect(self.replace_selected_cells)
        layout.addWidget(self.replace_button)

        self.clear_selection_button = QPushButton("清除选择")
        self.clear_selection_button.setEnabled(False)
        self.clear_selection_button.clicked.connect(self._clear_selection)
        layout.addWidget(self.clear_selection_button)

        self.undo_button = QPushButton("撤销换色")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_color_edit)
        layout.addWidget(self.undo_button)

        layout.addStretch()

        palette_info = QLabel(
            f"色卡：MARD\n"
            f"已加载颜色：{len(self.palette)}"
        )
        palette_info.setStyleSheet(
            "color: #777777;"
        )
        layout.addWidget(palette_info)

        self._update_size_controls()

        return panel

    def _create_preview_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = PatternPreview(self)
        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.preview_label.setStyleSheet(
            "background: #eeeeee;"
            "color: #777777;"
            "padding: 0px;"
        )

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.scroll_area.setWidget(self.preview_label)

        layout.addWidget(self.scroll_area)

        return panel

    def _build_status_bar(self) -> None:
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("准备就绪")

    def _update_size_controls(self) -> None:
        mode = self.size_mode_combo.currentData()

        is_collection = mode == "collection"

        self.collection_size_combo.setEnabled(
            is_collection
        )
        self.target_size_spin.setEnabled(
            not is_collection
        )

        if mode == "width":
            self.target_size_spin.setSuffix(" 颗宽")

        elif mode == "height":
            self.target_size_spin.setSuffix(" 颗高")

        elif mode == "longest":
            self.target_size_spin.setSuffix(" 颗最长边")

        else:
            self.target_size_spin.setSuffix(" 颗")

    def open_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            str(PROJECT_ROOT),
            (
                "图片文件 (*.png *.jpg *.jpeg *.webp);;"
                "PNG 图片 (*.png);;"
                "所有文件 (*)"
            ),
        )

        if not filename:
            return

        self.source_path = Path(filename)
        self.file_label.setText(self.source_path.name)

        self.statusBar().showMessage(
            f"已选择：{self.source_path.name}"
        )

    def generate_sheet(self) -> None:
        if self.source_path is None:
            QMessageBox.information(
                self,
                "尚未选择图片",
                "请先选择一张图片。",
            )
            return

        try:
            self.statusBar().showMessage(
                "正在生成图纸…"
            )

            size_mode = str(
                self.size_mode_combo.currentData()
            )

            target_beads_data = (
                self.collection_size_combo.currentData()
            )

            target_beads = int(
                target_beads_data
                if target_beads_data is not None
                else 850
            )

            with Image.open(self.source_path) as source:
                processed = self.processor.process(
                    image=source,
                    width=self.target_size_spin.value(),
                    keep_ratio=(
                        self.keep_ratio_check.isChecked()
                    ),
                    trim=self.trim_check.isChecked(),
                    method="lanczos",
                    size_mode=size_mode,
                    height=self.target_size_spin.value(),
                    target_beads=target_beads,
                    alpha_threshold=self.alpha_spin.value(),
                )

            pattern = self.matcher.match(
                image=processed,
                alpha_threshold=self.alpha_spin.value(),
            )

            pattern.title = self.source_path.stem

            config = RenderConfig(
                cell_size=self.cell_size_spin.value(),
                show_color=(
                    self.show_color_check.isChecked()
                ),
                show_coordinate=(
                    self.coordinate_check.isChecked()
                ),
                major_grid_every=(
                    self.major_grid_spin.value()
                ),
                checkerboard=(
                    self.checkerboard_check.isChecked()
                ),
            )

            self._display_sheet(pattern, config)
            self.pattern = pattern
            self.render_config = config
            self.edit_history.clear()
            self._clear_selection()
            self.color_combo.setEnabled(True)
            self.undo_button.setEnabled(False)
            self.mirror_check.blockSignals(True)
            self.mirror_check.setChecked(False)
            self.mirror_check.blockSignals(False)
            self.mirror_check.setEnabled(True)
            self.save_button.setEnabled(True)

            mode_label = (
                self.size_mode_combo.currentText()
            )

            self.statusBar().showMessage(
                f"生成完成｜"
                f"{mode_label}｜"
                f"{pattern.width} × {pattern.height}｜"
                f"{pattern.bead_count} 颗｜"
                f"{pattern.color_count} 种颜色"
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "生成失败",
                str(exc),
            )
            self.statusBar().showMessage(
                "生成失败"
            )

    def _display_sheet(self, pattern: Pattern, config: RenderConfig) -> None:
        # 预览和保存共用同一张完整渲染结果。
        image = render_sheet(pattern=pattern, config=config)
        pixmap = self._pil_to_pixmap(image)
        self.preview_label.setText("")
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setFixedSize(pixmap.size())
        self.scroll_area.setWidgetResizable(False)
        self.sheet_image = image
        self.sheet_pixmap = pixmap
        self._refresh_source_colors(pattern)

    def _toggle_mirror(self, checked: bool) -> None:
        if self.pattern is None or self.render_config is None:
            return

        config = replace(self.render_config, mirror_horizontal=checked)
        try:
            self._display_sheet(self.pattern, config)
        except Exception as exc:
            self.mirror_check.blockSignals(True)
            self.mirror_check.setChecked(self.render_config.mirror_horizontal)
            self.mirror_check.blockSignals(False)
            QMessageBox.critical(self, "镜像切换失败", str(exc))
            return

        self.render_config = config
        self.statusBar().showMessage(
            "已切换为水平镜像" if checked else "已恢复正常方向"
        )

    def _refresh_source_colors(self, pattern: Pattern) -> None:
        previous = self.source_color_combo.currentData()
        self.source_color_combo.clear()
        for row in pattern.statistics().itertuples(index=False):
            index = int(row.palette_index)
            color = pattern.palette[index]
            swatch = QPixmap(20, 20)
            swatch.fill(QColor(*color.rgb))
            self.source_color_combo.addItem(
                QIcon(swatch), f"{color.code} · {int(row.count)} 颗", index
            )
        position = self.source_color_combo.findData(previous)
        if position >= 0:
            self.source_color_combo.setCurrentIndex(position)
        available = self.source_color_combo.count() > 0
        self.source_color_combo.setEnabled(available)
        self.select_color_button.setEnabled(available)

    def select_all_of_color(self) -> None:
        if self.pattern is None:
            return
        index = self.source_color_combo.currentData()
        if not isinstance(index, int) or not 0 <= index < len(self.palette):
            return
        rows, columns = (self.pattern.grid == index).nonzero()
        self.selected_cells = {(int(x), int(y)) for y, x in zip(rows, columns)}
        self._update_selection()
        self.statusBar().showMessage(
            f"已全选 {self.palette[index].code}：{len(self.selected_cells)} 格，请选择目标色号并替换"
        )

    def _grid_geometry(self) -> tuple[int, int, int]:
        config = self.render_config
        cell = max(18, int(config.cell_size))
        margin = max(24, int(cell * 0.9))
        return (config.sheet_padding + margin,
                config.sheet_padding + 76 + config.sheet_spacing + margin,
                cell)

    def _select_cell(self, position, modifiers) -> None:
        if self.pattern is None or self.render_config is None:
            return
        left, top, cell = self._grid_geometry()
        x = int((position.x() - left) // cell)
        y = int((position.y() - top) // cell)
        if not (0 <= x < self.pattern.width and 0 <= y < self.pattern.height):
            return
        if self.render_config.mirror_horizontal:
            x = self.pattern.width - 1 - x
        multiple = modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)
        if not multiple:
            self.selected_cells.clear()
        if (x, y) in self.selected_cells:
            self.selected_cells.remove((x, y))
        else:
            self.selected_cells.add((x, y))
        self._update_selection()

    def _clear_selection(self) -> None:
        self.selected_cells.clear()
        self._update_selection()

    def _update_selection(self) -> None:
        count = len(self.selected_cells)
        self.selection_label.setText(
            f"已选中 {count} 格；按住 Ctrl / ⌘ 可多选" if count
            else "点击图纸选格；按住 Ctrl / ⌘ 可多选"
        )
        self.replace_button.setEnabled(bool(count))
        self.clear_selection_button.setEnabled(bool(count))
        if hasattr(self, "preview_label"):
            self.preview_label.update()

    def _apply_cell_colors(self, colors: dict[tuple[int, int], int]) -> bool:
        # Render before committing the edit so failures preserve the previous state.
        candidate = self.pattern.copy()
        candidate.title = getattr(self.pattern, "title", "")
        for (x, y), index in colors.items():
            candidate.set(x, y, index)
        try:
            self._display_sheet(candidate, self.render_config)
        except Exception as exc:
            QMessageBox.critical(self, "换色失败", str(exc))
            return False
        self.pattern = candidate
        self.preview_label.update()
        self.statusBar().showMessage(
            f"图纸已更新｜{candidate.bead_count} 颗｜{candidate.color_count} 种颜色"
        )
        return True

    def replace_selected_cells(self) -> None:
        if self.pattern is None or not self.selected_cells:
            return
        index = self.color_combo.currentData()
        if not isinstance(index, int) or not 0 <= index < len(self.palette):
            return
        previous = {(x, y): self.pattern.get(x, y)
                    for x, y in self.selected_cells if self.pattern.get(x, y) != index}
        if previous and self._apply_cell_colors({pos: index for pos in previous}):
            self.edit_history.append(previous)
            self.undo_button.setEnabled(True)

    def undo_color_edit(self) -> None:
        if self.pattern is None or not self.edit_history:
            return
        if self._apply_cell_colors(self.edit_history[-1]):
            self.edit_history.pop()
            self.undo_button.setEnabled(bool(self.edit_history))

    def save_sheet(self) -> None:
        if self.sheet_image is None:
            QMessageBox.information(
                self,
                "没有可保存的图纸",
                "请先生成图纸。",
            )
            return

        default_name = "bead_pattern.png"

        if self.source_path is not None:
            default_name = (
                f"{self.source_path.stem}"
                "_bead_pattern.png"
            )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存图纸",
            str(PROJECT_ROOT / default_name),
            "PNG 图片 (*.png)",
        )

        if not filename:
            return

        output_path = Path(filename)

        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(
                ".png"
            )

        try:
            self.sheet_image.save(
                output_path,
                format="PNG",
            )

            self.statusBar().showMessage(
                f"已保存：{output_path}"
            )

            QMessageBox.information(
                self,
                "保存成功",
                f"图纸已经保存到：\n"
                f"{output_path}",
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "保存失败",
                str(exc),
            )

    @staticmethod
    def _pil_to_pixmap(
        image: Image.Image,
    ) -> QPixmap:
        rgba = image.convert("RGBA")
        raw_data = rgba.tobytes(
            "raw",
            "RGBA",
        )

        qimage = QImage(
            raw_data,
            rgba.width,
            rgba.height,
            rgba.width * 4,
            QImage.Format.Format_RGBA8888,
        ).copy()

        return QPixmap.fromImage(qimage)