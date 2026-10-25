from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QRect, QSettings, QTranslator, QLibraryInfo
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
from core.i18n import translate, translate_error


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PALETTE_PATH = PROJECT_ROOT / "data" / "mard_221.csv"


class PatternPreview(QLabel):
    """Selection is painted as an overlay, never into the exported sheet."""

    def __init__(self, window):
        super().__init__(window._tr("请选择一张图片，然后点击“生成图纸”。"))
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
    """Main desktop window for XXBeadPattern: generation, editing, and PNG export."""

    def __init__(self, language: str | None = None, settings: QSettings | None = None) -> None:
        super().__init__()
        self.settings = settings if settings is not None else QSettings("XXBeadPattern", "XXBeadPattern")
        saved_language = language if language is not None else self.settings.value("language", "zh")
        self.language = saved_language if saved_language in {"zh", "en"} else "zh"
        self._text_bindings = []
        self._combo_bindings = []
        self._qt_translator = None

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

        self.setWindowTitle("XXBeadPattern")
        self.resize(1320, 860)

        self._build_menu()
        self._build_ui()
        self._build_status_bar()
        self._retranslate_ui()
        self._install_qt_translation()

    def _tr(self, text: str, **values) -> str:
        return translate(self.language, text, **values)

    def _text_widget(self, widget_type, text: str, *args):
        widget = widget_type(self._tr(text), *args)
        self._text_bindings.append((widget, text))
        return widget

    def _add_item(self, combo: QComboBox, text: str, data) -> None:
        index = combo.count()
        combo.addItem(self._tr(text), data)
        self._combo_bindings.append((combo, index, text))

    def _add_menu(self, menu_bar, text: str):
        menu = menu_bar.addMenu(self._tr(text))
        self._text_bindings.append((menu.menuAction(), text))
        return menu

    def _install_qt_translation(self) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if self._qt_translator is not None:
            app.removeTranslator(self._qt_translator)
            self._qt_translator = None
        if self.language == "zh":
            translator = QTranslator(self)
            if translator.load("qtbase_zh_CN", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
                app.installTranslator(translator)
                self._qt_translator = translator

    def _retranslate_ui(self) -> None:
        for widget, text in self._text_bindings:
            if widget is self.file_label and self.source_path is not None:
                continue
            widget.setText(self._tr(text))
        for combo, index, text in self._combo_bindings:
            combo.blockSignals(True)
            combo.setItemText(index, self._tr(text))
            combo.blockSignals(False)
        self.control_panel.setFixedWidth(360 if self.language == "en" else 310)
        self.control_scroll.setFixedWidth(385 if self.language == "en" else 335)
        self.major_grid_spin.setSuffix(self._tr(" 格"))
        self._update_size_controls()
        self._update_selection()
        self.palette_info.setText(self._tr("色卡：MARD\n已加载颜色：{count}", count=len(self.palette)))
        if self.pattern is not None:
            self._refresh_source_colors(self.pattern)
        if self.sheet_image is None:
            self.preview_label.setText(self._tr("请选择一张图片，然后点击“生成图纸”。"))

    def _change_language(self) -> None:
        language = self.language_combo.currentData()
        if language not in {"zh", "en"} or language == self.language:
            return
        previous = self.language
        self.language = language
        if self.pattern is not None and self.render_config is not None:
            config = replace(self.render_config, language=language)
            try:
                self._display_sheet(self.pattern, config)
            except Exception as exc:
                self.language = previous
                self.language_combo.blockSignals(True)
                self.language_combo.setCurrentIndex(self.language_combo.findData(previous))
                self.language_combo.blockSignals(False)
                QMessageBox.critical(self, self._tr("语言切换失败"), translate_error(self.language, str(exc)))
                return
            self.render_config = config
        self._retranslate_ui()
        self._install_qt_translation()
        self.settings.setValue("language", language)
        self.statusBar().showMessage(self._tr("界面语言已更新"))

    def _load_palette(self) -> Palette:
        if not PALETTE_PATH.exists():
            raise FileNotFoundError(
                self._tr('找不到 MARD 色卡文件：\n{value0}\n\n请将色卡保存为 data/mard_221.csv。', value0=PALETTE_PATH)
            )

        return Palette(str(PALETTE_PATH))

    def _build_menu(self) -> None:
        file_menu = self._add_menu(self.menuBar(), '文件')

        open_action = self._text_widget(QAction, '打开图片…', self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)

        save_action = self._text_widget(QAction, '保存图纸…', self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_sheet)

        quit_action = self._text_widget(QAction, '退出', self)
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
        self.control_scroll = control_scroll
        control_scroll.setFixedWidth(335)
        control_scroll.setWidget(controls)
        root_layout.addWidget(control_scroll)
        root_layout.addWidget(preview, stretch=1)

    def _create_control_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.control_panel = panel
        panel.setFixedWidth(310)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(13)

        title = self._text_widget(QLabel, '图纸设置')
        title.setStyleSheet(
            "font-size: 20px;"
            "font-weight: 600;"
        )
        layout.addWidget(title)

        self.file_label = self._text_widget(QLabel, '尚未选择图片')
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(
            "color: #666666;"
            "padding: 8px;"
            "border: 1px solid #d6d6d6;"
            "border-radius: 6px;"
        )
        layout.addWidget(self.file_label)

        open_button = self._text_widget(QPushButton, '选择图片')
        open_button.clicked.connect(self.open_image)
        layout.addWidget(open_button)

        language_row = QHBoxLayout()
        language_row.addWidget(self._text_widget(QLabel, "界面语言："))
        self.language_combo = QComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(self.language_combo.findData(self.language))
        self.language_combo.currentIndexChanged.connect(self._change_language)
        language_row.addWidget(self.language_combo)
        layout.addLayout(language_row)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.size_mode_combo = QComboBox()
        self._add_item(self.size_mode_combo, '图鉴模式（推荐）', "collection")
        self._add_item(self.size_mode_combo, '固定最长边', "longest")
        self._add_item(self.size_mode_combo, '固定宽度', "width")
        self._add_item(self.size_mode_combo, '固定高度', "height")
        self.size_mode_combo.currentIndexChanged.connect(
            self._update_size_controls
        )
        form.addRow(self._text_widget(QLabel, '尺寸模式：'), self.size_mode_combo)

        self.collection_size_combo = QComboBox()
        self._add_item(self.collection_size_combo, '小型图鉴 · 约550颗', 550)
        self._add_item(self.collection_size_combo, '标准图鉴 · 约850颗', 850)
        self._add_item(self.collection_size_combo, '大型图鉴 · 约1200颗', 1200)
        self.collection_size_combo.setCurrentIndex(1)
        form.addRow(self._text_widget(QLabel, '图鉴规格：'), self.collection_size_combo)

        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(4, 200)
        self.target_size_spin.setValue(40)
        self.target_size_spin.setSuffix(self._tr(' 颗'))
        form.addRow(self._text_widget(QLabel, '目标尺寸：'), self.target_size_spin)

        self.cell_size_spin = QSpinBox()
        self.cell_size_spin.setRange(18, 60)
        self.cell_size_spin.setValue(30)
        self.cell_size_spin.setSuffix(" px")
        form.addRow(self._text_widget(QLabel, '格子大小：'), self.cell_size_spin)

        self.major_grid_spin = QSpinBox()
        self.major_grid_spin.setRange(1, 20)
        self.major_grid_spin.setValue(5)
        self.major_grid_spin.setSuffix(self._tr(' 格'))
        form.addRow(self._text_widget(QLabel, '粗线间隔：'), self.major_grid_spin)

        self.alpha_spin = QSpinBox()
        self.alpha_spin.setRange(0, 255)
        self.alpha_spin.setValue(128)
        form.addRow(self._text_widget(QLabel, '透明阈值：'), self.alpha_spin)

        layout.addLayout(form)

        self.keep_ratio_check = self._text_widget(QCheckBox, '保持原图比例')
        self.keep_ratio_check.setChecked(True)
        layout.addWidget(self.keep_ratio_check)

        self.trim_check = self._text_widget(QCheckBox, '裁掉透明边缘')
        self.trim_check.setChecked(True)
        layout.addWidget(self.trim_check)

        self.show_color_check = self._text_widget(QCheckBox, '显示颜色背景')
        self.show_color_check.setChecked(True)
        layout.addWidget(self.show_color_check)

        self.coordinate_check = self._text_widget(QCheckBox, '显示四边坐标')
        self.coordinate_check.setChecked(True)
        layout.addWidget(self.coordinate_check)

        self.checkerboard_check = self._text_widget(QCheckBox, '透明区域显示棋盘格')
        self.checkerboard_check.setChecked(True)
        layout.addWidget(self.checkerboard_check)

        generate_button = self._text_widget(QPushButton, '生成图纸')
        generate_button.setMinimumHeight(42)
        generate_button.setStyleSheet(
            "font-size: 16px;"
            "font-weight: 600;"
        )
        generate_button.clicked.connect(self.generate_sheet)
        layout.addWidget(generate_button)

        layout.addWidget(self._text_widget(QLabel, '图例排序：'))
        self.legend_sort_combo = QComboBox()
        self._add_item(self.legend_sort_combo, '豆子数量：从多到少', "count")
        self._add_item(self.legend_sort_combo, '颜色系列：A–M（色号升序）', "series")
        self.legend_sort_combo.currentIndexChanged.connect(self._change_legend_sort)
        layout.addWidget(self.legend_sort_combo)

        self.mirror_check = self._text_widget(QCheckBox, '水平镜像')
        self.mirror_check.setEnabled(False)
        self.mirror_check.toggled.connect(self._toggle_mirror)
        layout.addWidget(self.mirror_check)

        self.save_button = self._text_widget(QPushButton, '保存 PNG')
        self.save_button.setMinimumHeight(38)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_sheet)
        layout.addWidget(self.save_button)

        self.selection_label = self._text_widget(QLabel, '点击图纸选格；按住 Ctrl / ⌘ 可多选')
        self.selection_label.setWordWrap(True)
        layout.addWidget(self.selection_label)

        layout.addWidget(self._text_widget(QLabel, '按色号全选（当前图纸）：'))
        self.source_color_combo = QComboBox()
        self.source_color_combo.setEnabled(False)
        layout.addWidget(self.source_color_combo)

        self.select_color_button = self._text_widget(QPushButton, '全选此色号')
        self.select_color_button.setEnabled(False)
        self.select_color_button.clicked.connect(self.select_all_of_color)
        layout.addWidget(self.select_color_button)

        self.color_combo = QComboBox()
        for index, color in enumerate(self.palette.colors):
            swatch = QPixmap(20, 20)
            swatch.fill(QColor(*color.rgb))
            self.color_combo.addItem(QIcon(swatch), color.code, index)
        self.color_combo.setEnabled(False)
        layout.addWidget(self._text_widget(QLabel, '替换颜色（MARD 221）：'))
        layout.addWidget(self.color_combo)

        self.replace_button = self._text_widget(QPushButton, '替换选中像素')
        self.replace_button.setEnabled(False)
        self.replace_button.clicked.connect(self.replace_selected_cells)
        layout.addWidget(self.replace_button)

        self.clear_selection_button = self._text_widget(QPushButton, '清除选择')
        self.clear_selection_button.setEnabled(False)
        self.clear_selection_button.clicked.connect(self._clear_selection)
        layout.addWidget(self.clear_selection_button)

        self.undo_button = self._text_widget(QPushButton, '撤销换色')
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_color_edit)
        layout.addWidget(self.undo_button)

        layout.addStretch()

        self.palette_info = palette_info = QLabel(
            self._tr('色卡：MARD\n已加载颜色：{value0}', value0=len(self.palette))
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
        self.statusBar().showMessage(self._tr('准备就绪'))

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
            self.target_size_spin.setSuffix(self._tr(' 颗宽'))

        elif mode == "height":
            self.target_size_spin.setSuffix(self._tr(' 颗高'))

        elif mode == "longest":
            self.target_size_spin.setSuffix(self._tr(' 颗最长边'))

        else:
            self.target_size_spin.setSuffix(self._tr(' 颗'))

    def open_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self._tr('选择图片'),
            str(PROJECT_ROOT),
            self._tr('图片文件 (*.png *.jpg *.jpeg *.webp);;PNG 图片 (*.png);;所有文件 (*)'),
            options=QFileDialog.Option.DontUseNativeDialog,
        )

        if not filename:
            return

        self.source_path = Path(filename)
        self.file_label.setText(self.source_path.name)

        self.statusBar().showMessage(
            self._tr('已选择：{value0}', value0=self.source_path.name)
        )

    def generate_sheet(self) -> None:
        if self.source_path is None:
            QMessageBox.information(
                self,
                self._tr('尚未选择图片'),
                self._tr('请先选择一张图片。'),
            )
            return

        try:
            self.statusBar().showMessage(
                self._tr('正在生成图纸…')
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
                language=self.language,
                legend_sort=self.legend_sort_combo.currentData(),
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
                self._tr('生成完成｜{value0}｜{value1} × {value2}｜{value3} 颗｜{value4} 种颜色', value0=mode_label, value1=pattern.width, value2=pattern.height, value3=pattern.bead_count, value4=pattern.color_count)
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                self._tr('生成失败'),
                translate_error(self.language, str(exc)),
            )
            self.statusBar().showMessage(
                self._tr('生成失败')
            )

    def _display_sheet(self, pattern: Pattern, config: RenderConfig) -> None:
        # Use the same complete rendered image for preview and PNG export.
        image = render_sheet(pattern=pattern, config=config)
        pixmap = self._pil_to_pixmap(image)
        self.preview_label.setText("")
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setFixedSize(pixmap.size())
        self.scroll_area.setWidgetResizable(False)
        self.sheet_image = image
        self.sheet_pixmap = pixmap
        self._refresh_source_colors(pattern)

    def _change_legend_sort(self) -> None:
        if self.pattern is None or self.render_config is None:
            return
        config = replace(self.render_config, legend_sort=self.legend_sort_combo.currentData())
        try:
            self._display_sheet(self.pattern, config)
        except Exception as exc:
            self.legend_sort_combo.blockSignals(True)
            self.legend_sort_combo.setCurrentIndex(
                self.legend_sort_combo.findData(self.render_config.legend_sort)
            )
            self.legend_sort_combo.blockSignals(False)
            QMessageBox.critical(self, self._tr('图例排序失败'), translate_error(self.language, str(exc)))
            return
        self.render_config = config
        self.statusBar().showMessage(self._tr('图例排序已更新'))

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
            QMessageBox.critical(self, self._tr('镜像切换失败'), translate_error(self.language, str(exc)))
            return

        self.render_config = config
        self.statusBar().showMessage(
            self._tr('已切换为水平镜像') if checked else self._tr('已恢复正常方向')
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
                QIcon(swatch), self._tr('{value0} · {value1} 颗', value0=color.code, value1=int(row.count)), index
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
            self._tr('已全选 {value0}：{value1} 格，请选择目标色号并替换', value0=self.palette[index].code, value1=len(self.selected_cells))
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
            self._tr('已选中 {value0} 格；按住 Ctrl / ⌘ 可多选', value0=count) if count
            else self._tr('点击图纸选格；按住 Ctrl / ⌘ 可多选')
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
            QMessageBox.critical(self, self._tr('换色失败'), translate_error(self.language, str(exc)))
            return False
        self.pattern = candidate
        self.preview_label.update()
        self.statusBar().showMessage(
            self._tr('图纸已更新｜{value0} 颗｜{value1} 种颜色', value0=candidate.bead_count, value1=candidate.color_count)
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
                self._tr('没有可保存的图纸'),
                self._tr('请先生成图纸。'),
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
            self._tr('保存图纸'),
            str(PROJECT_ROOT / default_name),
            self._tr('PNG 图片 (*.png)'),
            options=QFileDialog.Option.DontUseNativeDialog,
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
                self._tr('已保存：{value0}', value0=output_path)
            )

            QMessageBox.information(
                self,
                self._tr('保存成功'),
                self._tr('图纸已经保存到：\n{value0}', value0=output_path),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                self._tr('保存失败'),
                translate_error(self.language, str(exc)),
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