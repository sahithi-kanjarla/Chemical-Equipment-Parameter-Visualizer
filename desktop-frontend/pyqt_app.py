# Part 1 of 3 — imports, helpers, MplCanvas, ParameterCard
"""
PyQt5 Desktop client — improved layout with single PDF download control and multi-select options.

Usage:
    python pyqt_app.py

Dependencies:
    pip install pyqt5 matplotlib requests pandas reportlab pillow
"""
import sys
import io
import math
import requests
import pandas as pd
import matplotlib
# use non-GUI Agg backend (safe)
matplotlib.use('Agg')
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QGroupBox,
    QTextEdit, QComboBox, QListWidget, QMessageBox, QSizePolicy, QTabWidget,
    QScrollArea, QFrame, QGridLayout, QSplitter, QToolButton, QMenu, QAction
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

API_BASE_DEFAULT = "http://127.0.0.1:8000"

# -------------------------
# Robust helper: create PNG bytes from values_dict for embedding in PDF
# -------------------------
def safe_label(s: str, max_len=20):
    if s is None:
        return ""
    s = str(s)
    if len(s) <= max_len:
        return s
    return s[:max_len-3] + "..."

def use_constrained_layout(fig: Figure):
    try:
        fig.set_constrained_layout(True)
    except Exception:
        pass

def create_plot_image(param_name, values_dict, chart_type='bar',
                      width_inches=8, height_inches=4, dpi=200, logger_fn=None):
    """
    Build a matplotlib Figure from values_dict (label->value) and return PNG bytes (BytesIO).
    Guarantees a non-empty BytesIO (placeholder image on failure).
    logger_fn: optional callable(str) to receive debug messages (e.g. self.log).
    """
    buf = io.BytesIO()
    try:
        fig = Figure(figsize=(width_inches, height_inches), dpi=dpi)
        use_constrained_layout(fig)
        ax = fig.add_subplot(111)

        labels = list(values_dict.keys()) if values_dict else []
        vals = [values_dict.get(k, 0) or 0 for k in labels]
        labels_short = [safe_label(l, max_len=20) for l in labels]

        n = max(1, len(labels_short))
        use_hbar = n >= 8
        if n <= 6:
            rot = 0; label_fs = 10
        elif n <= 12:
            rot = 30; label_fs = 9
        else:
            rot = 0; label_fs = 9

        if chart_type == 'bar':
            if use_hbar:
                ax.barh(labels_short, vals)
                ax.invert_yaxis()
            else:
                bars = ax.bar(labels_short, vals)
                for bar in bars:
                    h = bar.get_height()
                    ax.annotate(f'{h:.2f}', xy=(bar.get_x()+bar.get_width()/2, h),
                                xytext=(0,4), textcoords='offset points', ha='center', fontsize=8)
            ax.set_ylabel(param_name)
        elif chart_type == 'line':
            ax.plot(labels_short, vals, marker='o', linestyle='-')
            ax.set_ylabel(param_name)
        elif chart_type == 'pie':
            if sum(vals) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
            else:
                wedges, texts, autotexts = ax.pie(vals, labels=None, autopct='%1.0f%%', startangle=90)
                ax.axis('equal')
                ax.legend(wedges, labels_short, title="Type", loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
        elif chart_type == 'hist':
            nums = [v for v in vals if v is not None]
            if nums:
                ax.hist(nums, bins=min(10, max(1, len(nums))), edgecolor='black')
                ax.set_xlabel('Value')
                ax.set_ylabel('Frequency')
            else:
                ax.text(0.5, 0.5, 'No numeric data', ha='center', va='center')
        else:
            ax.bar(labels_short, vals)

        ax.set_title(f'{param_name}', fontsize=11)
        if not use_hbar:
            ax.tick_params(axis='x', rotation=rot, labelsize=label_fs)
        else:
            ax.tick_params(axis='y', labelsize=label_fs)
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass

        fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
        buf.seek(0)

        if buf.getbuffer().nbytes == 0:
            if logger_fn: logger_fn(f"create_plot_image: produced zero-length buffer for {param_name}")
            buf = io.BytesIO()
            fig2 = Figure(figsize=(6,3), dpi=dpi)
            ax2 = fig2.add_subplot(111)
            ax2.text(0.5, 0.5, "No chart (placeholder)", ha='center', va='center')
            ax2.axis('off')
            fig2.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
            buf.seek(0)

        return buf

    except Exception as e:
        if logger_fn: logger_fn(f"create_plot_image exception for {param_name}: {e}")
        buf = io.BytesIO()
        try:
            fig = Figure(figsize=(6,3), dpi=dpi)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f'Error creating chart: {e}', ha='center', va='center')
            ax.axis('off')
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
            buf.seek(0)
            return buf
        except Exception:
            buf.write(b'\x89PNG\r\n\x1a\n')
            buf.seek(0)
            return buf

# ---------- Matplotlib canvas wrapper ----------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=9, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        use_constrained_layout(fig)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)

# ---------- ParameterCard ----------
class ParameterCard(QWidget):
    def __init__(self, param_name, values_dict, on_remove_callback=None, canvas_size=(9.5,3.5)):
        super().__init__()
        self.param = param_name
        self.values = values_dict or {}
        self.on_remove_callback = on_remove_callback
        self.canvas_size = canvas_size

        outer = QVBoxLayout()
        header = QHBoxLayout()
        title = QLabel(f"<b>{self.param}</b>")
        title.setTextFormat(QtCore.Qt.RichText)
        header.addWidget(title)
        header.addStretch()

        self.chart_select = QComboBox()
        self.chart_select.addItems(['bar', 'line', 'pie', 'hist'])
        self.chart_select.setCurrentText('bar')
        self.chart_select.setToolTip("Change chart type for this parameter only")
        self.chart_select.currentIndexChanged.connect(self.render_chart)
        header.addWidget(QLabel("Chart:"))
        header.addWidget(self.chart_select)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setToolTip("Hide this chart (use Reset to restore)")
        self.btn_remove.clicked.connect(self.remove_card)
        header.addWidget(self.btn_remove)

        outer.addLayout(header)

        w_inches, h_inches = self.canvas_size
        self.canvas = MplCanvas(width=w_inches, height=h_inches, dpi=100)
        self.canvas.setFixedHeight(int(h_inches * 100))
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        outer.addWidget(self.canvas)

        self.setLayout(outer)
        self.render_chart()

    def set_values(self, values_dict):
        self.values = values_dict or {}
        self.render_chart()

    def render_chart(self):
        fig = self.canvas.figure
        fig.clf()
        use_constrained_layout(fig)
        ax = fig.add_subplot(111)
        self.canvas.ax = ax

        chart_type = self.chart_select.currentText()
        labels = list(self.values.keys())
        vals = [self.values.get(k, 0) or 0 for k in labels]
        labels_short = [safe_label(l, max_len=18) for l in labels]

        n_labels = max(1, len(labels_short))
        use_hbar = n_labels >= 8
        if n_labels <= 6:
            rot = 0; label_fs = 10
        elif n_labels <= 12:
            rot = 30; label_fs = 9
        else:
            rot = 0; label_fs = 9

        try:
            if chart_type == 'bar':
                if use_hbar:
                    ax.barh(labels_short, vals)
                    ax.invert_yaxis()
                else:
                    bars = ax.bar(labels_short, vals)
                    for bar in bars:
                        h = bar.get_height()
                        ax.annotate(f'{h:.2f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, h),
                                    xytext=(0, 4), textcoords='offset points',
                                    ha='center', fontsize=8)
                ax.set_ylabel(self.param)
            elif chart_type == 'line':
                ax.plot(labels_short, vals, marker='o', linestyle='-')
                ax.set_ylabel(self.param)
            elif chart_type == 'pie':
                if sum(vals) == 0:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                else:
                    wedges, texts, autotexts = ax.pie(
                        vals, labels=None, autopct='%1.0f%%', startangle=90, textprops={'fontsize': 8}
                    )
                    ax.axis('equal')
                    ax.legend(wedges, labels_short, title="Type",
                              loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
            elif chart_type == 'hist':
                nums = [v for v in vals if v is not None]
                if nums:
                    ax.hist(nums, bins=min(10, max(1, len(nums))), edgecolor='black')
                    ax.set_xlabel('Value')
                    ax.set_ylabel('Frequency')
                else:
                    ax.text(0.5, 0.5, 'No numeric data', ha='center', va='center')
            else:
                ax.bar(labels_short, vals)

            ax.set_title(f'Average {self.param} by Type', fontsize=10)
            if not use_hbar:
                ax.tick_params(axis='x', rotation=rot, labelsize=label_fs)
            else:
                ax.tick_params(axis='y', labelsize=label_fs)
            try:
                fig.tight_layout()
            except Exception:
                pass
        except Exception as e:
            ax.clear()
            ax.text(0.5, 0.5, f'Error: {e}', ha='center', va='center')
        self.canvas.draw_idle()

    def remove_card(self):
        if callable(self.on_remove_callback):
            try:
                self.on_remove_callback(self.param)
            except Exception:
                pass
        self.setParent(None)
        self.hide()
# Part 2 of 3 — DesktopApp UI, uploads, rendering, analysis cards
# (paste this after Part 1)

class DesktopApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Parameter Visualizer — Desktop (Refined UI)")
        self.resize(1250, 820)

        # state
        self.api_base = API_BASE_DEFAULT
        self.token = ""
        self.current_summary = None
        self.current_preview = []
        self.current_dataset_id = None

        # left sidebar widgets
        left_layout = QVBoxLayout()
        api_group = QGroupBox("Backend / Authentication")
        ag = QVBoxLayout()
        self.api_input = QLineEdit(self.api_base)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        btn_set = QPushButton("Set API & Token")
        btn_set.clicked.connect(self.set_api_token)
        ag.addWidget(QLabel("API Base URL:"))
        ag.addWidget(self.api_input)
        ag.addWidget(QLabel("Token:"))
        ag.addWidget(self.token_input)
        ag.addWidget(btn_set)
        api_group.setLayout(ag)
        left_layout.addWidget(api_group)

        upload_group = QGroupBox("Upload CSV")
        up_layout = QVBoxLayout()
        btn_upload = QPushButton("Upload CSV")
        btn_upload.clicked.connect(self.upload_csv)
        up_layout.addWidget(btn_upload)
        upload_group.setLayout(up_layout)
        left_layout.addWidget(upload_group)

        history_group = QGroupBox("History (last 5)")
        h_layout = QVBoxLayout()
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        btn_refresh = QPushButton("Refresh History")
        btn_refresh.clicked.connect(self.load_history)
        h_layout.addWidget(self.history_list)
        h_layout.addWidget(btn_refresh)
        history_group.setLayout(h_layout)
        left_layout.addWidget(history_group)

        status_group = QGroupBox("Status / Logs")
        s_layout = QVBoxLayout()
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFixedHeight(160)
        s_layout.addWidget(self.status_box)
        status_group.setLayout(s_layout)
        left_layout.addWidget(status_group)
        left_layout.addStretch()

        # Right content: tabs
        right_layout = QVBoxLayout()
        tabs = QTabWidget()

        # Overview tab
        overview_tab = QWidget()
        ov_layout = QVBoxLayout()

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        ov_layout.addLayout(self.kpi_row)

        top_ctrl_row = QHBoxLayout()
        self.summary_label = QLabel("<b>No dataset loaded.</b>")
        self.summary_label.setWordWrap(True)
        top_ctrl_row.addWidget(self.summary_label, 3)

        controls_right = QVBoxLayout()
        ctrl_line = QHBoxLayout()
        ctrl_line.addWidget(QLabel("Overview chart:"))
        self.overview_chart_select = QComboBox()
        self.overview_chart_select.addItems(['bar', 'pie', 'line', 'hist'])
        ctrl_line.addWidget(self.overview_chart_select)
        btn_render_overview = QPushButton("Render")
        btn_render_overview.clicked.connect(self.render_overview_chart)
        ctrl_line.addWidget(btn_render_overview)
        controls_right.addLayout(ctrl_line)

        pdf_line = QHBoxLayout()
        self.btn_download_pdf = QToolButton()
        self.btn_download_pdf.setText("Download PDF")
        self.btn_download_pdf.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn_download_pdf.clicked.connect(self.handle_download_pdf_click)
        self.pdf_menu = QMenu()

        # keep only the include/use options — remove the two submenus per your request
        self.act_use_saved = QAction("Use saved dataset (if available)", self, checkable=True)
        self.act_include_summary = QAction("Include summary", self, checkable=True)
        self.act_include_type_chart = QAction("Include type chart", self, checkable=True)
        self.act_include_analysis = QAction("Include analysis charts", self, checkable=True)
        self.act_include_preview = QAction("Include preview rows", self, checkable=True)

        self.act_include_summary.setChecked(True)
        self.act_include_type_chart.setChecked(True)
        self.act_include_analysis.setChecked(True)
        self.act_include_preview.setChecked(True)
        self.act_use_saved.setChecked(False)

        # removed: type_chart_menu and analysis_chart_menu creation

        self.act_select_all = QAction("Select all includes", self)
        self.act_select_all.triggered.connect(self.select_all_includes)

        # assemble menu (no submenus)
        self.pdf_menu.addAction(self.act_use_saved)
        self.pdf_menu.addSeparator()
        self.pdf_menu.addAction(self.act_include_summary)
        self.pdf_menu.addAction(self.act_include_type_chart)
        self.pdf_menu.addAction(self.act_include_analysis)
        self.pdf_menu.addAction(self.act_include_preview)
        self.pdf_menu.addSeparator()
        self.pdf_menu.addAction(self.act_select_all)

        self.btn_download_pdf.setMenu(self.pdf_menu)
        pdf_line.addWidget(self.btn_download_pdf)
        controls_right.addLayout(pdf_line)

        top_ctrl_row.addLayout(controls_right, 2)
        ov_layout.addLayout(top_ctrl_row)

        self.overview_canvas = MplCanvas(width=11, height=5)
        ov_layout.addWidget(self.overview_canvas, 6)

        preview_toggle_row = QHBoxLayout()
        self.btn_toggle_preview = QPushButton("Hide Preview")
        self.btn_toggle_preview.setCheckable(True)
        self.btn_toggle_preview.clicked.connect(self.toggle_preview)
        preview_toggle_row.addWidget(self.btn_toggle_preview)
        preview_toggle_row.addStretch()
        ov_layout.addLayout(preview_toggle_row)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.preview_table.setFixedHeight(220)
        ov_layout.addWidget(self.preview_table, 3)

        overview_tab.setLayout(ov_layout)
        tabs.addTab(overview_tab, "Overview")

        # Analysis tab (single-column)
        analysis_tab = QWidget()
        an_layout = QVBoxLayout()
        a_ctrl = QHBoxLayout()
        self.btn_reset_analysis = QPushButton("Reset Analysis")
        self.btn_reset_analysis.clicked.connect(self.reset_analysis)
        a_ctrl.addWidget(self.btn_reset_analysis)
        a_ctrl.addStretch()
        an_layout.addLayout(a_ctrl)

        self.analysis_scroll = QScrollArea()
        self.analysis_scroll.setWidgetResizable(True)
        self.analysis_container = QWidget()
        self.analysis_grid_layout = QGridLayout()
        self.analysis_grid_layout.setSpacing(12)
        self.analysis_container.setLayout(self.analysis_grid_layout)
        self.analysis_scroll.setWidget(self.analysis_container)
        an_layout.addWidget(self.analysis_scroll, 9)

        analysis_tab.setLayout(an_layout)
        tabs.addTab(analysis_tab, "Analysis")

        right_layout.addWidget(tabs)
        splitter = QSplitter(QtCore.Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([320, 920])

        top_layout = QVBoxLayout()
        top_layout.addWidget(splitter)
        self.setLayout(top_layout)

        self.param_cards = {}
        self.analysis_params_order = ['Flowrate','Pressure','Temperature']

        self.apply_styles()
        self.log("Ready. Set API base & token then refresh history.")
        self.load_history()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { font-family: Arial; font-size: 11px; }
            QGroupBox { font-weight: bold; }
            QPushButton { padding: 6px; }
            QTableWidget { background: #ffffff; }
            QToolButton { padding:6px; }
        """)

    def log(self, msg: str):
        self.status_box.append(msg)

    def toggle_preview(self):
        if self.btn_toggle_preview.isChecked():
            self.preview_table.hide()
            self.btn_toggle_preview.setText("Show Preview")
        else:
            self.preview_table.show()
            self.btn_toggle_preview.setText("Hide Preview")

    def headers(self):
        h = {}
        if self.token:
            h['Authorization'] = f"Token {self.token}"
        return h

    def set_api_token(self):
        self.api_base = (self.api_input.text() or API_BASE_DEFAULT).strip()
        self.token = self.token_input.text().strip()
        self.log(f"API base set to {self.api_base}")
        if self.token:
            self.log("Token set.")
        self.load_history()

    def upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        self.log(f"Uploading: {path}")
        url = f"{self.api_base.rstrip('/')}/api/upload/"
        try:
            with open(path, 'rb') as fh:
                files = {'file': (path.split('/')[-1], fh, 'text/csv')}
                r = requests.post(url, files=files, headers=self.headers(), timeout=30)
            if r.status_code == 201:
                data = r.json()
                self.current_summary = data.get('summary')
                self.current_dataset_id = data.get('id') or (data.get('object') or {}).get('id')
                self.current_preview = data.get('preview_rows', [])
                self.log("Upload successful.")
                self.update_ui_from_summary()
                self.load_history()
            else:
                self.log(f"Upload failed: {r.status_code} {r.text}")
                QMessageBox.critical(self, "Upload failed", f"{r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            self.log(f"Upload exception: {e}")
            QMessageBox.critical(self, "Upload error", str(e))

    def load_history(self):
        url = f"{self.api_base.rstrip('/')}/api/history/"
        try:
            r = requests.get(url, headers=self.headers(), timeout=10)
            if r.status_code == 200:
                self.history_list.clear()
                items = r.json()
                for it in items:
                    pk = it.get('id')
                    name = it.get('original_filename') or ''
                    label = f"{pk} — {name}"
                    lw = QtWidgets.QListWidgetItem(label)
                    lw.setData(QtCore.Qt.UserRole, pk)
                    self.history_list.addItem(lw)
                self.log("History loaded.")
            elif r.status_code == 401:
                self.log("History: unauthorized (401). Set valid token.")
            else:
                self.log(f"Failed to load history: {r.status_code} {r.text}")
        except requests.exceptions.RequestException as e:
            self.log(f"History exception: {e}")

    def load_history_item(self, item):
        pk = item.data(QtCore.Qt.UserRole)
        self.log(f"Loading dataset {pk}")
        url = f"{self.api_base.rstrip('/')}/api/summary/{pk}/"
        try:
            r = requests.get(url, headers=self.headers(), timeout=12)
            if r.status_code == 200:
                obj = r.json()
                if isinstance(obj, dict) and 'summary' in obj:
                    self.current_summary = obj.get('summary')
                    self.current_preview = obj.get('preview_rows', [])
                else:
                    self.current_summary = obj
                    self.current_preview = []
                self.current_dataset_id = pk
                self.update_ui_from_summary()
            else:
                self.log(f"Failed to load summary: {r.status_code} {r.text}")
                QMessageBox.critical(self, "Load failed", f"{r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            self.log(f"Load exception: {e}")

    def update_ui_from_summary(self):
        s = self.current_summary or {}
        for i in reversed(range(self.kpi_row.count())):
            w = self.kpi_row.takeAt(i).widget()
            if w:
                w.setParent(None)

        def kpi_widget(title, value, subtitle=None):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet("background:#f5f7fa; border-radius:6px; padding:8px;")
            v = QVBoxLayout()
            v.addWidget(QLabel(f"<b>{title}</b>"))
            v.addWidget(QLabel(f"<h2 style='margin:0'>{value}</h2>"))
            if subtitle:
                v.addWidget(QLabel(f"<small>{subtitle}</small>"))
            frame.setLayout(v)
            return frame

        total = s.get('total_count', 'N/A')
        avg_flow = s.get('averages', {}).get('Flowrate')
        avg_flow_display = f"{avg_flow:.2f}" if avg_flow is not None else "N/A"
        ntypes = len(s.get('type_distribution', {}) or {})
        self.kpi_row.addWidget(kpi_widget("Total equipment", total))
        self.kpi_row.addWidget(kpi_widget("Avg Flowrate", avg_flow_display))
        self.kpi_row.addWidget(kpi_widget("Equipment types", ntypes))

        summary_html = f"<b>Total:</b> {total}<br><b>Averages:</b><br>"
        for k,v in (s.get('averages') or {}).items():
            summary_html += f"{k}: {('N/A' if v is None else f'{v:.2f}')}<br>"
        self.summary_label.setText(summary_html)

        if self.current_preview and isinstance(self.current_preview, list) and len(self.current_preview) > 0:
            df = pd.DataFrame(self.current_preview)
            self.populate_table(df, self.preview_table)
        else:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)

        self.render_overview_chart()
        self.build_analysis_cards()

    def populate_table(self, df: pd.DataFrame, table_widget: QTableWidget):
        df.columns = [str(c) for c in df.columns]
        table_widget.setColumnCount(len(df.columns))
        table_widget.setRowCount(len(df.index))
        table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        for r_idx, row in df.iterrows():
            for c_idx, col in enumerate(df.columns):
                val = row[col]
                item = QTableWidgetItem("" if pd.isna(val) else str(val))
                table_widget.setItem(r_idx, c_idx, item)
        table_widget.resizeColumnsToContents()

    def render_overview_chart(self):
        fig = self.overview_canvas.figure
        fig.clf()
        use_constrained_layout(fig)
        ax = fig.add_subplot(111)
        self.overview_canvas.ax = ax

        chart_type = self.overview_chart_select.currentText()
        s = self.current_summary or {}
        type_dist = (s.get('type_distribution') or {}) or {}
        labels = list(type_dist.keys())
        counts = [type_dist.get(k, 0) for k in labels]
        labels_short = [safe_label(l, max_len=18) for l in labels]

        if not labels:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=12)
            self.overview_canvas.draw_idle()
            return

        n = max(1, len(labels))
        use_hbar = n >= 10
        if n <= 6:
            rot = 0; label_fs = 10
        elif n <= 12:
            rot = 30; label_fs = 9
        else:
            rot = 0; label_fs = 9

        try:
            if chart_type == 'bar':
                if use_hbar:
                    ax.barh(labels_short, counts)
                    ax.invert_yaxis()
                else:
                    bars = ax.bar(labels_short, counts)
                    for bar in bars:
                        h = bar.get_height()
                        ax.annotate(f'{h}', xy=(bar.get_x()+bar.get_width()/2, h),
                                    xytext=(0,4), textcoords='offset points', ha='center', fontsize=9)
                ax.set_ylabel('Count')
            elif chart_type == 'pie':
                if sum(counts) == 0:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=12)
                else:
                    wedges, texts, autotexts = ax.pie(
                        counts, labels=None, autopct='%1.0f%%', startangle=90, textprops={'fontsize': 9}
                    )
                    ax.axis('equal')
                    ax.legend(wedges, labels_short, title="Type", loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9)
            elif chart_type == 'line':
                ax.plot(labels_short, counts, marker='o')
                ax.set_ylabel('Count')
            elif chart_type == 'hist':
                nums = [v for v in (s.get('averages') or {}).values() if v is not None]
                if not nums:
                    nums = counts
                if nums:
                    ax.hist(nums, bins=min(10, max(1, len(nums))), edgecolor='black')
                    ax.set_xlabel('Value')
                    ax.set_ylabel('Frequency')
                else:
                    ax.text(0.5, 0.5, 'No numeric data', ha='center', va='center', fontsize=12)
            ax.set_title('Type distribution', fontsize=12)
            if not use_hbar:
                ax.tick_params(axis='x', rotation=rot, labelsize=label_fs)
            else:
                ax.tick_params(axis='y', labelsize=label_fs)
            try:
                fig.tight_layout()
            except Exception:
                pass
        except Exception as e:
            ax.clear()
            ax.text(0.5, 0.5, f'Error: {e}', ha='center', va='center')
        self.overview_canvas.draw_idle()

    def build_analysis_cards(self):
        for i in reversed(range(self.analysis_grid_layout.count())):
            widget = self.analysis_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.param_cards = {}
        per_type = (self.current_summary or {}).get('per_type_averages', {}) or {}
        r = 0
        for p in self.analysis_params_order:
            vals = per_type.get(p, {}) or {}
            card = ParameterCard(p, vals, on_remove_callback=self.handle_remove_card, canvas_size=(9.5,3.5))
            card.show()
            self.param_cards[p] = card
            self.analysis_grid_layout.addWidget(card, r, 0)
            r += 1

    def rebuild_analysis_grid(self):
        if not self.param_cards:
            self.build_analysis_cards()
            return
        vals_snapshot = {p: (card.values if card else {}) for p, card in self.param_cards.items()}
        self.analysis_params_order = list(vals_snapshot.keys())
        for i in reversed(range(self.analysis_grid_layout.count())):
            widget = self.analysis_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        r = 0
        for p, vals in vals_snapshot.items():
            card = ParameterCard(p, vals, on_remove_callback=self.handle_remove_card, canvas_size=(9.5,3.5))
            card.show()
            self.param_cards[p] = card
            self.analysis_grid_layout.addWidget(card, r, 0)
            r += 1

    def handle_remove_card(self, param_name):
        if param_name in self.param_cards:
            self.param_cards.pop(param_name, None)
        if param_name in self.analysis_params_order:
            self.analysis_params_order.remove(param_name)
        self.log(f"Removed analysis chart: {param_name}")

    def reset_analysis(self):
        self.analysis_params_order = ['Flowrate','Pressure','Temperature']
        self.build_analysis_cards()

    def select_all_includes(self):
        self.act_include_summary.setChecked(True)
        self.act_include_type_chart.setChecked(True)
        self.act_include_analysis.setChecked(True)
        self.act_include_preview.setChecked(True)

    # After removing menus, get_selected_type_chart_type now reads overview dropdown
    def get_selected_type_chart_type(self):
        try:
            return self.overview_chart_select.currentText()
        except Exception:
            return 'bar'

    # analysis chart type is taken from per-card selectors; keep this for compatibility
    def get_selected_analysis_chart_type(self):
        # fallback: return 'bar'
        return 'bar'
# Part 3 of 3 — PDF generation, run loop
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import traceback

def _ensure_bytes_and_open(img_buf):
    try:
        img_buf.seek(0)
        pil = Image.open(img_buf)
        return pil
    except Exception:
        return None

# Insert this method into DesktopApp (it uses self.* members)
def handle_download_pdf_click(self):
    """Generate PDF locally (or GET saved report). Uses create_plot_image to reliably render analysis charts."""
    use_saved = self.act_use_saved.isChecked()
    include_summary = self.act_include_summary.isChecked()
    include_type_chart = self.act_include_type_chart.isChecked()
    include_analysis = self.act_include_analysis.isChecked()
    include_preview = self.act_include_preview.isChecked()

    # If user chose saved report on server
    if use_saved and self.current_dataset_id:
        type_chart_type = self.get_selected_type_chart_type()
        url = f"{self.api_base.rstrip('/')}/api/report/{self.current_dataset_id}/?chart_type={type_chart_type}"
        try:
            r = requests.get(url, headers=self.headers(), stream=True, timeout=30)
            if r.status_code == 200:
                path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"report_dataset_{self.current_dataset_id}.pdf", "PDF Files (*.pdf)")
                if path:
                    with open(path, 'wb') as fh:
                        for chunk in r.iter_content(chunk_size=8192):
                            fh.write(chunk)
                    QMessageBox.information(self, "Saved", f"Saved PDF to {path}")
            else:
                QMessageBox.critical(self, "Failed", f"{r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", str(e))
        return

    path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "report_desktop.pdf", "PDF Files (*.pdf)")
    if not path:
        return

    try:
        buf_out = io.BytesIO()
        p = canvas.Canvas(buf_out, pagesize=letter)
        W, H = letter

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(72, H - 72, "Chemical Equipment Report")
        p.setFont("Helvetica", 9)
        p.drawString(72, H - 90, f"Generated by Desktop App")
        p.drawString(72, H - 102, f"Dataset ID: {self.current_dataset_id or 'N/A'}")
        p.drawString(72, H - 114, f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

        y = H - 140
        line_height = 12

        # SUMMARY
        if include_summary and self.current_summary:
            s = self.current_summary or {}
            p.setFont("Helvetica-Bold", 12)
            p.drawString(72, y, "Summary")
            y -= line_height
            p.setFont("Helvetica", 10)
            p.drawString(80, y, f"Total equipment: {s.get('total_count', 'N/A')}")
            y -= line_height
            p.drawString(80, y, "Averages:")
            y -= line_height
            avgs = s.get('averages', {}) or {}
            for k, v in avgs.items():
                try:
                    p.drawString(92, y, f"{k}: {('N/A' if v is None else format(v, '.2f'))}")
                except Exception:
                    p.drawString(92, y, f"{k}: {v}")
                y -= line_height
            y -= line_height / 2

        # OVERVIEW (uses overview dropdown selection)
        if include_type_chart and getattr(self, 'current_summary', None):
            try:
                type_dist = (self.current_summary or {}).get('type_distribution', {}) or {}
                chosen = self.get_selected_type_chart_type()
                img_buf = create_plot_image('Type distribution', type_dist, chart_type=chosen, width_inches=8, height_inches=4, dpi=200, logger_fn=self.log)
                pil = _ensure_bytes_and_open(img_buf)
                if pil:
                    iw, ih = pil.size
                    max_w_pts = 440.0
                    draw_w = max_w_pts
                    draw_h = (ih / iw) * draw_w
                    if draw_h > (y - 72):
                        p.showPage()
                        y = H - 72
                    img_buf.seek(0)
                    p.drawImage(ImageReader(img_buf), 72, y - draw_h, width=draw_w, height=draw_h)
                    y -= (draw_h + 12)
                    self.log("Embedded overview chart")
                else:
                    self.log("Overview image invalid; skipped embedding")
                    y -= 10
            except Exception as e:
                self.log(f"Failed to embed overview chart: {e}")
                y -= 10

        # ANALYSIS (uses per-card selection)
        if include_analysis:
            per_type = (self.current_summary or {}).get('per_type_averages', {}) or {}
            for pname in list(self.analysis_params_order):
                vals = per_type.get(pname)
                if (not vals or len(vals) == 0) and pname in self.param_cards:
                    vals = getattr(self.param_cards[pname], 'values', {}) or {}
                if not vals:
                    self.log(f"No data for analysis {pname}; skipping")
                    continue

                p.setFont("Helvetica-Bold", 11)
                p.drawString(72, y, f"Analysis — {pname}")
                y -= line_height

                ct = 'bar'
                if pname in self.param_cards:
                    try:
                        card_ct = getattr(self.param_cards[pname], 'chart_select', None)
                        if card_ct is not None:
                            ct = card_ct.currentText()
                    except Exception:
                        pass

                try:
                    img_buf = create_plot_image(f"{pname} (per-type avg)", vals, chart_type=ct, width_inches=8.5, height_inches=4.0, dpi=220, logger_fn=self.log)
                    pil = _ensure_bytes_and_open(img_buf)
                    if pil:
                        iw, ih = pil.size
                        max_w_pts = 460.0
                        draw_w = max_w_pts
                        draw_h = (ih / iw) * draw_w
                        if draw_h > (y - 72):
                            p.showPage()
                            y = H - 72
                        img_buf.seek(0)
                        p.drawImage(ImageReader(img_buf), 72, y - draw_h, width=draw_w, height=draw_h)
                        y -= (draw_h + 12)
                        self.log(f"Embedded analysis chart for {pname} (type={ct})")
                    else:
                        self.log(f"Analysis image invalid for {pname}; skipped")
                        y -= 10
                except Exception as e:
                    self.log(f"Failed embedding analysis chart {pname}: {e}")
                    y -= 20

        # PREVIEW rows
        if include_preview and self.current_preview:
            preview = self.current_preview or []
            if isinstance(preview, list) and len(preview) > 0:
                cols = list(preview[0].keys())[:5]
                p.setFont("Helvetica-Bold", 11)
                p.drawString(72, y, "Preview (first rows)")
                y -= line_height
                p.setFont("Helvetica", 9)
                x = 72
                col_w = (W - 144) / max(1, len(cols))
                for c in cols:
                    p.drawString(x, y, str(c)[:18])
                    x += col_w
                y -= line_height
                for row in preview[:8]:
                    if y < 90:
                        p.showPage()
                        y = H - 72
                    x = 72
                    for c in cols:
                        txt = str(row.get(c, ''))[:18]
                        p.drawString(x, y, txt)
                        x += col_w
                    y -= line_height

        p.showPage()
        p.save()
        buf_out.seek(0)
        with open(path, 'wb') as out_f:
            out_f.write(buf_out.read())

        QMessageBox.information(self, "Saved", f"Saved PDF to {path}")

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to generate PDF: {e}")
        self.log("PDF error: " + str(e))
        self.log(traceback.format_exc())

# attach the method to DesktopApp class
DesktopApp.handle_download_pdf_click = handle_download_pdf_click

# ---------- main / run ----------
def main():
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet("""
        QWidget { font-family: Arial; }
        QPushButton { padding:6px; }
        QComboBox { min-width: 90px; }
        QToolButton { padding:6px; }
    """)
    win = DesktopApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
