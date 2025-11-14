"""
PyQt5 Desktop client — JWT-only (access/refresh) + nicer PDF layout (ReportLab Platypus).
Usage: python pyqt_app.py
Dependencies:
    pip install pyqt5 matplotlib requests pandas reportlab pillow
"""

import sys
import io
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # safe backend when saving figures to files
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QGroupBox,
    QTextEdit, QComboBox, QListWidget, QMessageBox, QSizePolicy, QTabWidget,
    QScrollArea, QFrame, QGridLayout, QSplitter, QToolButton, QMenu, QAction, QDialog, QFormLayout
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from PIL import Image
import traceback

API_BASE_DEFAULT = "http://127.0.0.1:8000"

# ------------------------- helpers -------------------------
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

def _annotate_bars(ax, vals, use_hbar):
    """
    Annotate bars such that:
      - If a bar is tall/long enough (>= threshold of max), place label inside (white text).
      - Otherwise place label outside (black text).
    Avoid overlap with chart boundary by adding headroom.
    """
    try:
        nums = [v for v in vals if isinstance(v, (int, float))]
        max_val = max(nums) if nums else 0.0
        inside_frac = 0.12 if max_val > 0 else 0.2

        patches = ax.patches
        if not patches:
            return

        if use_hbar:
            headroom = max_val * 0.12 if max_val > 0 else 1.0
            left, right = ax.get_xlim()
            ax.set_xlim(0, max(max_val + headroom, right))
            for bar in patches:
                w = bar.get_width() or 0
                y = bar.get_y() + bar.get_height() / 2
                if max_val > 0 and w >= inside_frac * max_val:
                    ax.annotate(f'{w:.2f}',
                                xy=(w * 0.98, y),
                                xytext=(0, 0),
                                textcoords='offset points',
                                ha='right', va='center',
                                fontsize=8, color='white', weight='bold')
                else:
                    ax.annotate(f'{w:.2f}',
                                xy=(w, y),
                                xytext=(4, 0),
                                textcoords='offset points',
                                ha='left', va='center',
                                fontsize=8, color='black')
        else:
            headroom = max_val * 0.12 if max_val > 0 else 1.0
            bottom, top = ax.get_ylim()
            ax.set_ylim(0, max(max_val + headroom, top))
            for bar in patches:
                h = bar.get_height() or 0
                x = bar.get_x() + bar.get_width() / 2
                if max_val > 0 and h >= inside_frac * max_val:
                    ax.annotate(f'{h:.2f}',
                                xy=(x, h * 0.98),
                                xytext=(0, 0),
                                textcoords='offset points',
                                ha='center', va='top',
                                fontsize=8, color='white', weight='bold')
                else:
                    ax.annotate(f'{h:.2f}',
                                xy=(x, h),
                                xytext=(0, 4),
                                textcoords='offset points',
                                ha='center', va='bottom',
                                fontsize=8, color='black')
    except Exception:
        pass

# create PNG bytes from values_dict for embedding
def create_plot_image(param_name, values_dict, chart_type='bar',
                      width_inches=8, height_inches=4, dpi=200, logger_fn=None):
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
                _annotate_bars(ax, vals, use_hbar=True)
            else:
                ax.bar(labels_short, vals)
                _annotate_bars(ax, vals, use_hbar=False)
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
            _annotate_bars(ax, vals, use_hbar=False)

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
            buf = io.BytesIO()
            fig2 = Figure(figsize=(6,3), dpi=dpi)
            ax2 = fig2.add_subplot(111)
            ax2.text(0.5, 0.5, "No chart (placeholder)", ha='center', va='center')
            ax2.axis('off')
            fig2.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
            buf.seek(0)
        return buf
    except Exception as e:
        if logger_fn:
            try: logger_fn(f"create_plot_image exception for {param_name}: {e}")
            except Exception: pass
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

# ---------- nicer PDF generator (Platypus) ----------
def generate_nice_pdf(path,
                      summary,
                      preview_rows,
                      dataset_id=None,
                      include_summary=True,
                      include_type_chart=True,
                      include_analysis=True,
                      include_preview=True,
                      analysis_params_order=None,
                      create_plot_image_fn=None,
                      overview_chart_choice='bar',
                      analysis_chart_types=None,
                      logger_fn=None):
    """
    Generate a nicer, block-based PDF using ReportLab Platypus.
    analysis_chart_types: dict mapping param name -> chart_type (e.g. {'Flowrate': 'line', ...})
    """
    if analysis_params_order is None:
        analysis_params_order = ['Flowrate','Pressure','Temperature']
    if analysis_chart_types is None:
        analysis_chart_types = {}

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='HeadingLarge', fontSize=16, leading=18, spaceAfter=6, spaceBefore=6))
    styles.add(ParagraphStyle(name='HeadingSmall', fontSize=11, leading=13, spaceAfter=4, textColor=colors.HexColor('#333333')))
    styles.add(ParagraphStyle(name='MonoSmall', fontName='Helvetica', fontSize=9, leading=11))
    styles.add(ParagraphStyle(name='Block', fontSize=10, leading=12, backColor=colors.whitesmoke, borderPadding=6, spaceAfter=6))

    doc = SimpleDocTemplate(path, pagesize=letter,
                            rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    flow = []

    # Header
    title = Paragraph("Chemical Equipment Report", styles['HeadingLarge'])
    meta_lines = []
    meta_lines.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dataset_id:
        meta_lines.append(f"Dataset ID: {dataset_id}")
    meta = Paragraph("<br/>".join(meta_lines), styles['MonoSmall'])

    header_table = Table([[title, meta]], colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    flow.append(header_table)
    flow.append(Spacer(1, 12))

    # SUMMARY BOXES
    if include_summary and summary:
        total = summary.get('total_count', 'N/A')
        avg_flow = summary.get('averages', {}).get('Flowrate')
        avg_flow_display = ("N/A" if avg_flow is None else f"{avg_flow:.2f}")
        ntypes = len(summary.get('type_distribution', {}) or {})

        box_data = [
            [Paragraph("<b>Total equipment</b>", styles['HeadingSmall']),
             Paragraph("<b>Avg Flowrate</b>", styles['HeadingSmall']),
             Paragraph("<b>Equipment types</b>", styles['HeadingSmall'])],
            [Paragraph(str(total), styles['Block']),
             Paragraph(str(avg_flow_display), styles['Block']),
             Paragraph(str(ntypes), styles['Block'])]
        ]
        box_table = Table(box_data, colWidths=[2*inch, 2*inch, 2*inch])
        box_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#dddddd')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,1), (-1,1), colors.whitesmoke)
        ]))
        flow.append(box_table)
        flow.append(Spacer(1, 12))

        # averages detail
        avg_rows = []
        avgs = summary.get('averages', {}) or {}
        for k, v in avgs.items():
            avg_rows.append([Paragraph(k, styles['MonoSmall']), Paragraph(('N/A' if v is None else f"{v:.2f}"), styles['MonoSmall'])])
        if avg_rows:
            avg_table = Table([ [Paragraph("<b>Averages</b>", styles['HeadingSmall']), ''] ] + avg_rows, colWidths=[2.2*inch, 2.8*inch])
            avg_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f6fb')),
                ('BOX', (0,0), (-1,-1), 0.25, colors.HexColor('#e0e0e0')),
                ('INNERGRID', (0,1), (-1,-1), 0.25, colors.HexColor('#eeeeee'))
            ]))
            flow.append(avg_table)
            flow.append(Spacer(1, 10))

    # Type distribution chart
    if include_type_chart and summary:
        td = summary.get('type_distribution', {}) or {}
        if td and create_plot_image_fn:
            try:
                img_buf = create_plot_image_fn('Type distribution', td, chart_type=overview_chart_choice, width_inches=6.5, height_inches=3.0, dpi=200, logger_fn=logger_fn)
                img_buf.seek(0)
                rl_img = RLImage(img_buf, width=6.5*inch, height=3.0*inch)
                flow.append(Paragraph("Type distribution", styles['HeadingSmall']))
                flow.append(rl_img)
                flow.append(Spacer(1, 12))
            except Exception as e:
                if logger_fn:
                    logger_fn(f"Failed to render type chart: {e}")
                flow.append(Paragraph("Type distribution chart unavailable.", styles['MonoSmall']))
                flow.append(Spacer(1, 8))

    # Analysis charts (use provided analysis_chart_types)
    if include_analysis and summary:
        per_type_avgs = summary.get('per_type_averages', {}) or {}
        for param in (analysis_params_order or []):
            data_dict = per_type_avgs.get(param, {}) or {}
            if not data_dict:
                continue
            flow.append(Paragraph(f"Analysis — {param}", styles['HeadingSmall']))
            if create_plot_image_fn:
                chart_type = analysis_chart_types.get(param, 'bar')
                try:
                    img_buf = create_plot_image_fn(f"{param} (avg by type)", data_dict, chart_type=chart_type, width_inches=6.5, height_inches=2.6, dpi=200, logger_fn=logger_fn)
                    img_buf.seek(0)
                    rl_img = RLImage(img_buf, width=6.5*inch, height=2.6*inch)
                    flow.append(rl_img)
                    flow.append(Spacer(1, 8))
                except Exception as e:
                    if logger_fn:
                        logger_fn(f"Failed to render analysis chart for {param}: {e}")
                    flow.append(Paragraph(f"Chart unavailable for {param}.", styles['MonoSmall']))
                    flow.append(Spacer(1, 8))

    # Preview rows table
    if include_preview and preview_rows:
        flow.append(Paragraph("Preview (first rows)", styles['HeadingSmall']))
        cols = list(preview_rows[0].keys())[:6]
        header = [Paragraph(f"<b>{c}</b>", styles['MonoSmall']) for c in cols]
        data = [header]
        for r in preview_rows[:8]:
            row = [Paragraph(str(r.get(c, '')), styles['MonoSmall']) for c in cols]
            data.append(row)
        preview_table = Table(data, colWidths=[(doc.width / max(1, len(cols))) for _ in cols])
        preview_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#e6e6e6')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f7f9fc')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        flow.append(preview_table)
        flow.append(Spacer(1, 8))

    flow.append(Spacer(1, 12))
    flow.append(Paragraph("Generated by Chemical Equipment Parameter Visualizer — desktop client", styles['MonoSmall']))

    doc.build(flow)

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
                    _annotate_bars(ax, vals, use_hbar=True)
                else:
                    ax.bar(labels_short, vals)
                    _annotate_bars(ax, vals, use_hbar=False)
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
                _annotate_bars(ax, vals, use_hbar=False)

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

# ---------- Login dialog ----------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login (JWT)")
        self.resize(320, 120)
        layout = QFormLayout(self)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)
        btn_row = QHBoxLayout()
        ok = QPushButton("Login"); cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(ok); btn_row.addWidget(cancel)
        layout.addRow(btn_row)

    def get_credentials(self):
        return self.username.text().strip(), self.password.text().strip()

# ---------- Main application ----------
class DesktopApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Parameter Visualizer — Desktop")
        self.resize(1250, 820)

        # state
        self.api_base = API_BASE_DEFAULT
        self.access_token = None
        self.refresh_token = None
        self.current_summary = None
        self.current_preview = []
        self.current_dataset_id = None
        self.logged_in_username = None

        # left sidebar widgets
        left_layout = QVBoxLayout()
        api_group = QGroupBox("Backend / Authentication")
        ag = QVBoxLayout()
        self.api_input = QLineEdit(self.api_base)

        # login status label
        self.login_status_label = QLabel("Not logged in")
        self.login_status_label.setStyleSheet("color: #b65a00;")
        self.login_status_label.setWordWrap(True)

        ag.addWidget(QLabel("API Base URL:"))
        ag.addWidget(self.api_input)
        ag.addWidget(self.login_status_label)

        # Login / Logout buttons (JWT)
        btn_row = QHBoxLayout()
        btn_login = QPushButton("Login (get JWT)")
        btn_login.clicked.connect(self.show_login_dialog)
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.logout)
        self.btn_logout.setEnabled(False)
        btn_row.addWidget(btn_login)
        btn_row.addWidget(self.btn_logout)
        ag.addLayout(btn_row)

        api_group.setLayout(ag)
        left_layout.addWidget(api_group)

        upload_group = QGroupBox("Upload CSV")
        up_layout = QVBoxLayout()
        self.btn_upload = QPushButton("Upload CSV")
        self.btn_upload.clicked.connect(self.upload_csv)
        # disabled until JWT login
        self.btn_upload.setEnabled(False)
        up_layout.addWidget(self.btn_upload)
        upload_group.setLayout(up_layout)
        left_layout.addWidget(upload_group)

        history_group = QGroupBox("History (last 5)")
        h_layout = QVBoxLayout()
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        self.btn_refresh = QPushButton("Refresh History")
        self.btn_refresh.clicked.connect(self.load_history)
        self.btn_refresh.setEnabled(False)
        h_layout.addWidget(self.history_list)
        h_layout.addWidget(self.btn_refresh)
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

        self.act_select_all = QAction("Select all includes", self)
        self.act_select_all.triggered.connect(self.select_all_includes)

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
        self.log("Ready. Set API base then Login to proceed.")
        # initial load history (will warn if unauthorized)
        self.load_history()

    # ---------- small UI helpers ----------
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { font-family: Arial; font-size: 11px; }
            QGroupBox { font-weight: bold; }
            QPushButton { padding: 6px; }
            QTableWidget { background: #ffffff; }
            QToolButton { padding:6px; }
        """)

    def log(self, msg: str, level: str = "info"):
        """
        Append colored, timestamped messages to the status box.
        level: "info"|"warn"|"error"|"success"
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "#000"
        if level == "error":
            color = "#b00"
        elif level == "warn":
            color = "#b65a00"
        elif level == "success":
            color = "#080"
        else:
            color = "#000"
        try:
            self.status_box.append(f"<span style='color:{color}'>[{ts}] {msg}</span>")
        except Exception:
            try:
                self.status_box.append(f"[{ts}] {msg}")
            except Exception:
                pass

    def toggle_preview(self):
        if self.btn_toggle_preview.isChecked():
            self.preview_table.hide()
            self.btn_toggle_preview.setText("Show Preview")
        else:
            self.preview_table.show()
            self.btn_toggle_preview.setText("Hide Preview")

    # ---------- AUTH helpers (JWT) ----------
    def headers(self):
        h = {}
        if getattr(self, "access_token", None):
            h['Authorization'] = f"Bearer {self.access_token}"
        return h

    def show_login_dialog(self):
        dlg = LoginDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            username, password = dlg.get_credentials()
            if username and password:
                QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                try:
                    ok = self.obtain_jwt_tokens(username, password)
                finally:
                    QApplication.restoreOverrideCursor()
                if ok:
                    QMessageBox.information(self, "Login", "Login successful — access token obtained.")
                    self.btn_logout.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Login failed", "Failed to obtain tokens. Check credentials and server.")
            else:
                QMessageBox.warning(self, "Login", "Provide both username and password.")

    def obtain_jwt_tokens(self, username: str, password: str) -> bool:
        """
        POST to /api/token/ to obtain access & refresh tokens.
        Stores them in self.access_token & self.refresh_token.
        """
        url = f"{self.api_base.rstrip('/')}/api/token/"
        try:
            r = requests.post(url, json={"username": username, "password": password}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                self.logged_in_username = username
                try:
                    self.login_status_label.setText(f"Logged in as: {username}")
                    self.login_status_label.setStyleSheet("color: #080;")
                except Exception:
                    pass
                # enable relevant buttons
                self.btn_upload.setEnabled(True)
                self.btn_refresh.setEnabled(True)
                self.btn_logout.setEnabled(True)
                self.log("Obtained JWT access & refresh tokens.", level="success")
                return True
            else:
                try:
                    self.login_status_label.setText("Login failed")
                    self.login_status_label.setStyleSheet("color: #b00;")
                except Exception:
                    pass
                self.log(f"Token obtain failed: {r.status_code} {r.text}", level="error")
                return False
        except requests.exceptions.RequestException as e:
            try:
                self.login_status_label.setText("Login error")
                self.login_status_label.setStyleSheet("color: #b00;")
            except Exception:
                pass
            self.log(f"Token request error: {e}", level="error")
            return False

    def refresh_access_token(self) -> bool:
        """
        Use the refresh token to get a new access token.
        """
        if not getattr(self, "refresh_token", None):
            return False
        url = f"{self.api_base.rstrip('/')}/api/token/refresh/"
        try:
            r = requests.post(url, json={"refresh": self.refresh_token}, timeout=12)
            if r.status_code == 200:
                self.access_token = r.json().get("access")
                self.log("Refreshed access token.", level="info")
                return True
            else:
                self.log(f"Refresh failed: {r.status_code} {r.text}", level="warn")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"Refresh error: {e}", level="error")
            return False

    def logout(self):
        """
        Clear tokens and disable actions that require authentication.
        """
        self.access_token = None
        self.refresh_token = None
        self.logged_in_username = None
        self.btn_upload.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.btn_logout.setEnabled(False)
        try:
            self.login_status_label.setText("Not logged in")
            self.login_status_label.setStyleSheet("color: #b65a00;")
        except Exception:
            pass
        self.log("Logged out — tokens cleared.", level="info")

    # ---------- uploads / history / summary ----------
    def upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        self.log(f"Uploading: {path}", level="info")
        url = f"{self.api_base.rstrip('/')}/api/upload/"
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            with open(path, 'rb') as fh:
                files = {'file': (path.split('/')[-1], fh, 'text/csv')}
                r = requests.post(url, files=files, headers=self.headers(), timeout=60)
            if r.status_code in (200, 201):
                data = r.json()
                self.current_summary = data.get('summary')
                self.current_dataset_id = data.get('id') or (data.get('object') or {}).get('id')
                self.current_preview = data.get('preview_rows', [])
                self.log("Upload successful.", level="success")
                self.update_ui_from_summary()
                self.load_history()
            else:
                self.log(f"Upload failed: {r.status_code} {r.text}", level="error")
                QMessageBox.critical(self, "Upload failed", f"{r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            self.log(f"Upload exception: {e}", level="error")
            QMessageBox.critical(self, "Upload error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_history(self):
        url = f"{self.api_base.rstrip('/')}/api/history/"
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            r = requests.get(url, headers=self.headers(), timeout=12)
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
                self.log("History loaded.", level="info")
            elif r.status_code == 401:
                self.log("History: unauthorized (401). Use Login to obtain JWT.", level="warn")
            else:
                self.log(f"Failed to load history: {r.status_code} {r.text}", level="error")
        except requests.exceptions.RequestException as e:
            self.log(f"History exception: {e}", level="error")
        finally:
            QApplication.restoreOverrideCursor()

    def load_history_item(self, item):
        pk = item.data(QtCore.Qt.UserRole)
        self.log(f"Loading dataset {pk}", level="info")
        url = f"{self.api_base.rstrip('/')}/api/summary/{pk}/"
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
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
            elif r.status_code == 401:
                self.log("Unauthorized loading summary — token may be missing or expired. Try Login/Refresh.", level="warn")
                QMessageBox.warning(self, "Unauthorized", "Token missing or expired. Please login again.")
            else:
                self.log(f"Failed to load summary: {r.status_code} {r.text}", level="error")
                QMessageBox.critical(self, "Load failed", f"{r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            self.log(f"Load exception: {e}", level="error")
        finally:
            QApplication.restoreOverrideCursor()

    # ---------- UI / update ----------
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

    # ---------- Overview ----------
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
                    _annotate_bars(ax, counts, use_hbar=True)
                else:
                    ax.bar(labels_short, counts)
                    _annotate_bars(ax, counts, use_hbar=False)
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

    # ---------- Analysis ----------
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
        self.log(f"Removed analysis chart: {param_name}", level="info")

    def reset_analysis(self):
        self.analysis_params_order = ['Flowrate','Pressure','Temperature']
        self.build_analysis_cards()

    def select_all_includes(self):
        self.act_include_summary.setChecked(True)
        self.act_include_type_chart.setChecked(True)
        self.act_include_analysis.setChecked(True)
        self.act_include_preview.setChecked(True)

    # --------- PDF handler (uses Platypus generator) ----------
    def handle_download_pdf_click(self):
        use_saved = self.act_use_saved.isChecked()
        include_summary = self.act_include_summary.isChecked()
        include_type_chart = self.act_include_type_chart.isChecked()
        include_analysis = self.act_include_analysis.isChecked()
        include_preview = self.act_include_preview.isChecked()

        # server-saved PDF
        if use_saved and self.current_dataset_id:
            type_chart_type = 'bar'
            url = f"{self.api_base.rstrip('/')}/api/report/{self.current_dataset_id}/?chart_type={type_chart_type}"
            QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                r = requests.get(url, headers=self.headers(), stream=True, timeout=30)
                if r.status_code == 200:
                    path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"report_dataset_{self.current_dataset_id}.pdf", "PDF Files (*.pdf)")
                    if path:
                        with open(path, 'wb') as fh:
                            for chunk in r.iter_content(chunk_size=8192):
                                fh.write(chunk)
                        QMessageBox.information(self, "Saved", f"Saved PDF to {path}")
                        self.log(f"Saved server PDF to {path}", level="success")
                else:
                    QMessageBox.critical(self, "Failed", f"{r.status_code}: {r.text}")
                    self.log(f"Failed to download server PDF: {r.status_code}", level="error")
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Error", str(e))
                self.log(f"Server PDF request error: {e}", level="error")
            finally:
                QApplication.restoreOverrideCursor()
            return

        # Local PDF generation using Platypus
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "report_desktop.pdf", "PDF Files (*.pdf)")
        if not path:
            return

        # build analysis_chart_types mapping from current cards' selected chart types
        analysis_chart_types = {}
        for pname, card in self.param_cards.items():
            try:
                analysis_chart_types[pname] = card.chart_select.currentText()
            except Exception:
                analysis_chart_types[pname] = 'bar'

        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            generate_nice_pdf(
                path=path,
                summary=self.current_summary or {},
                preview_rows=self.current_preview or [],
                dataset_id=self.current_dataset_id,
                include_summary=include_summary,
                include_type_chart=include_type_chart,
                include_analysis=include_analysis,
                include_preview=include_preview,
                analysis_params_order=self.analysis_params_order,
                create_plot_image_fn=create_plot_image,
                overview_chart_choice=self.overview_chart_select.currentText(),
                analysis_chart_types=analysis_chart_types,
                logger_fn=self.log
            )
            QMessageBox.information(self, "Saved", f"Saved PDF to {path}")
            self.log(f"Saved local PDF to {path}", level="success")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {e}")
            self.log("PDF error: " + str(e), level="error")
            self.log(traceback.format_exc(), level="error")
        finally:
            QApplication.restoreOverrideCursor()

# ---------- main ----------
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
