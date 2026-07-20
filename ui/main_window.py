from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
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
from core.renderer import RenderConfig, render_sheet


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PALETTE_PATH = PROJECT_ROOT / "data" / "mard_221.csv"


class MainWindow(QMainWindow):
    """
    BeadCraft 主窗口。

    第一版功能：
    - 打开图片
    - 设置图纸宽度
    - 自动生成 MARD 拼豆图纸
    - 在窗口中预览
    - 保存为 PNG
    """

    def __init__(self) -> None:
        super().__init__()

        self.source_path: Path | None = None
        self.sheet_image: Image.Image | None = None
        self.sheet_pixmap: QPixmap | None = None

        self.palette = self._load_palette()
        self.processor = ImageProcessor()
        self.matcher = ColorMatcher(self.palette)

        self.setWindowTitle("XBeadCraft")
        self.resize(1280, 820)

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

        root_layout.addWidget(controls)
        root_layout.addWidget(preview, stretch=1)

    def _create_control_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedWidth(280)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("图纸设置")
        title.setStyleSheet(
            "font-size: 20px; font-weight: 600;"
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

        self.width_spin = QSpinBox()
        self.width_spin.setRange(4, 200)
        self.width_spin.setValue(39)
        self.width_spin.setSuffix(" 颗")
        form.addRow("图纸宽度：", self.width_spin)

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

        self.checkerboard_check = QCheckBox("透明区域显示棋盘格")
        self.checkerboard_check.setChecked(True)
        layout.addWidget(self.checkerboard_check)

        generate_button = QPushButton("生成图纸")
        generate_button.setMinimumHeight(42)
        generate_button.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        generate_button.clicked.connect(self.generate_sheet)
        layout.addWidget(generate_button)

        self.save_button = QPushButton("保存 PNG")
        self.save_button.setMinimumHeight(38)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_sheet)
        layout.addWidget(self.save_button)

        layout.addStretch()

        palette_info = QLabel(
            f"色卡：MARD\n"
            f"已加载颜色：{len(self.palette)}"
        )
        palette_info.setStyleSheet("color: #777777;")
        layout.addWidget(palette_info)

        return panel

    def _create_preview_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel(
            "请选择一张图片，然后点击“生成图纸”。"
        )
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "background: #eeeeee;"
            "color: #777777;"
            "padding: 30px;"
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
            self.statusBar().showMessage("正在生成图纸…")

            with Image.open(self.source_path) as source:
                processed = self.processor.process(
                    image=source,
                    width=self.width_spin.value(),
                    keep_ratio=self.keep_ratio_check.isChecked(),
                    trim=self.trim_check.isChecked(),
                    method="lanczos",
                )

            pattern = self.matcher.match(
                image=processed,
                alpha_threshold=self.alpha_spin.value(),
            )

            pattern.title = self.source_path.stem

            config = RenderConfig(
                cell_size=self.cell_size_spin.value(),
                show_color=self.show_color_check.isChecked(),
                show_coordinate=self.coordinate_check.isChecked(),
                major_grid_every=self.major_grid_spin.value(),
                checkerboard=self.checkerboard_check.isChecked(),
            )

            self.sheet_image = render_sheet(
                pattern=pattern,
                config=config,
            )

            self.sheet_pixmap = self._pil_to_pixmap(
                self.sheet_image
            )

            self.preview_label.setText("")
            self.preview_label.setPixmap(self.sheet_pixmap)
            self.preview_label.resize(self.sheet_pixmap.size())

            self.scroll_area.setWidgetResizable(False)
            self.save_button.setEnabled(True)

            self.statusBar().showMessage(
                f"生成完成：{pattern.width} × {pattern.height}，"
                f"{pattern.bead_count} 颗，"
                f"{pattern.color_count} 种颜色"
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "生成失败",
                str(exc),
            )
            self.statusBar().showMessage("生成失败")

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
                f"{self.source_path.stem}_bead_pattern.png"
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
            output_path = output_path.with_suffix(".png")

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
                f"图纸已经保存到：\n{output_path}",
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "保存失败",
                str(exc),
            )

    @staticmethod
    def _pil_to_pixmap(image: Image.Image) -> QPixmap:
        """
        将 PIL 图片转换为 Qt QPixmap。

        必须调用 copy()，否则 QImage 可能继续引用
        已被 Python 回收的临时字节数据。
        """

        rgba = image.convert("RGBA")
        raw_data = rgba.tobytes("raw", "RGBA")

        qimage = QImage(
            raw_data,
            rgba.width,
            rgba.height,
            rgba.width * 4,
            QImage.Format.Format_RGBA8888,
        ).copy()

        return QPixmap.fromImage(qimage)