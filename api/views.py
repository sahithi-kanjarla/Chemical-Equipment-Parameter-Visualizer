# api/views.py
import io
import logging
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import pandas as pd
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Matplotlib (non-GUI backend)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .models import UploadedDataset
from .serializers import UploadedDatasetSerializer

logger = logging.getLogger(__name__)


def create_chart_image(summary, chart_type='bar', width_inches=8, height_inches=3.5, dpi=100):
    """
    Create a PNG image BytesIO of a chart from 'summary' (type_distribution or numeric averages).
    Returns BytesIO (seeked to 0) or None on failure.
    """
    buf = io.BytesIO()
    try:
        type_dist = (summary or {}).get('type_distribution', {}) or {}
        labels = list(type_dist.keys())
        counts = [type_dist.get(k, 0) for k in labels]

        # fallback numeric values for histogram
        if chart_type == 'hist':
            nums = []
            avgs = (summary or {}).get('averages', {}) or {}
            for v in avgs.values():
                if v is not None:
                    nums.append(v)
            if not nums:
                nums = counts
        else:
            nums = None

        plt.figure(figsize=(width_inches, height_inches), dpi=dpi)

        if chart_type == 'bar':
            plt.bar(labels, counts)
            plt.title('Count by Equipment Type')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right', fontsize=9)
        elif chart_type == 'pie':
            if sum(counts) == 0:
                plt.text(0.5, 0.5, 'No data', ha='center', va='center')
            else:
                wedges, texts, autotexts = plt.pie(
                    counts,
                    labels=None,
                    autopct='%1.0f%%',
                    startangle=90,
                    textprops={'fontsize': 8}
                )
                plt.legend(
                    wedges,
                    [str(s) for s in labels],
                    title="Type",
                    loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    fontsize=8,
                )
                plt.axis('equal')
            plt.title('Type Distribution (%)')
        elif chart_type == 'line':
            plt.plot(labels, counts, marker='o')
            plt.title('Type counts (line)')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right', fontsize=9)
        elif chart_type == 'hist':
            if nums:
                plt.hist(nums, bins=min(10, max(1, len(nums))), edgecolor='black')
                plt.title('Histogram (numeric values)')
                plt.xlabel('Value')
                plt.ylabel('Frequency')
            else:
                plt.text(0.5, 0.5, 'No numeric data', ha='center')
        else:
            plt.bar(labels, counts)
            plt.title('Count by Equipment Type')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right', fontsize=9)

        plt.tight_layout(pad=0.4)
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close()
        buf.seek(0)

        if buf.getbuffer().nbytes == 0:
            return None
        return buf

    except Exception:
        logger.exception("create_chart_image failed")
        try:
            plt.close()
        except Exception:
            pass
        return None


def api_root(request):
    """
    Minimal API root / health check.
    """
    return JsonResponse({
        "status": "ok",
        "message": "API root is working."
    })


class MeView(APIView):
    """
    GET /api/me/
    Returns basic info about the currently authenticated user.
    Frontend can use this after refresh to keep username/profile icon.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "date_joined": u.date_joined,
        })


class UploadCSVView(APIView):
    """
    POST /api/upload/
    multipart/form-data with field 'file' (CSV)
    Saves UploadedDataset with user=request.user and summary JSON.
    Keeps only last 5 uploads PER USER.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {"detail": "No file provided in 'file' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        filename = uploaded_file.name

        # Read CSV into pandas
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            logger.exception("Failed to read CSV on upload: %s", e)
            return Response(
                {"detail": f"Failed to read CSV: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize columns
        df.columns = [str(c).strip() for c in df.columns]
        required = {'Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature'}
        if not required.issubset(set(df.columns)):
            return Response(
                {
                    "detail": (
                        f"CSV missing required columns. "
                        f"Required: {sorted(required)}. Found: {list(df.columns)}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Coerce numeric cols
        for col in ['Flowrate', 'Pressure', 'Temperature']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # compute summary
        numeric_cols = ['Flowrate', 'Pressure', 'Temperature']
        averages = {
            col: (float(df[col].mean()) if not df[col].dropna().empty else None)
            for col in numeric_cols
        }
        type_distribution = df['Type'].value_counts().to_dict()
        total_count = int(df.shape[0])

        summary = {
            'total_count': total_count,
            'averages': averages,
            'type_distribution': type_distribution
        }

        # per-type averages
        try:
            per_type_avgs = {}
            for col in numeric_cols:
                grouped = df.groupby('Type')[col].mean()
                per_type_avgs[col] = {
                    str(k): (float(v) if not pd.isna(v) else None)
                    for k, v in grouped.to_dict().items()
                }
            summary['per_type_averages'] = per_type_avgs
        except Exception:
            logger.exception("Failed computing per_type_averages")
            summary['per_type_averages'] = {}

        # preview rows
        try:
            preview_rows = df.head(8).to_dict(orient='records')
        except Exception:
            preview_rows = []

        # Save file content and create model instance — attach current user
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

        try:
            content = uploaded_file.read()
            django_file = ContentFile(content, name=filename)

            obj = UploadedDataset.objects.create(
                user=request.user,
                original_filename=filename,
                csv_file=django_file,
                summary=summary
            )
        except Exception as e:
            logger.exception("Failed to save UploadedDataset: %s", e)
            return Response(
                {"detail": "Failed to save uploaded file on server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Prune older entries for THIS USER: keep only last 5
        try:
            qs_user = UploadedDataset.objects.filter(
                user=request.user
            ).order_by('-uploaded_at')
            to_delete = list(qs_user[5:])
            for old in to_delete:
                try:
                    old.csv_file.delete(save=False)
                except Exception:
                    pass
            if to_delete:
                UploadedDataset.objects.filter(
                    pk__in=[i.pk for i in to_delete]
                ).delete()
        except Exception:
            logger.exception("Failed pruning old UploadedDataset entries (per-user)")

        # Build serializer + include local csv path for the created object
        serializer = UploadedDatasetSerializer(obj, context={'request': request})
        csv_local_path = None
        try:
            csv_local_path = obj.csv_file.path
        except Exception:
            try:
                csv_local_path = obj.csv_file.name
            except Exception:
                csv_local_path = None

        return Response(
            {
                'id': obj.id,
                'summary': summary,
                'object': serializer.data,
                'preview_rows': preview_rows,
                'csv_local_path': csv_local_path,
            },
            status=status.HTTP_201_CREATED
        )


class HistoryView(APIView):
    """
    GET /api/history/
    Returns last 5 UploadedDataset entries for the authenticated user.
    Each item includes 'csv_local_path' (filesystem path) in addition to serializer data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        qs = UploadedDataset.objects.filter(
            user=request.user
        ).order_by('-uploaded_at')[:5]
        instances = list(qs)
        serializer = UploadedDatasetSerializer(
            instances, many=True, context={'request': request}
        )
        data = serializer.data

        # attach csv_local_path for each entry
        for idx, inst in enumerate(instances):
            try:
                data[idx]['csv_local_path'] = inst.csv_file.path
            except Exception:
                data[idx]['csv_local_path'] = (
                    inst.csv_file.name if inst.csv_file else None
                )

        return Response(data)


class DatasetSummaryView(APIView):
    """
    GET /api/summary/<int:pk>/
    Returns summary JSON + preview_rows for a given upload id (only if it belongs to the user).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        obj = get_object_or_404(UploadedDataset, pk=pk, user=request.user)

        preview_rows = []
        try:
            if getattr(obj.csv_file, 'path', None):
                df = pd.read_csv(obj.csv_file.path)
            else:
                with default_storage.open(obj.csv_file.name, mode='rb') as fh:
                    df = pd.read_csv(fh)
            df.columns = [str(c).strip() for c in df.columns]
            preview_rows = df.head(8).to_dict(orient='records')
        except Exception:
            logger.exception(
                "Failed to read CSV for preview in DatasetSummaryView (pk=%s)", pk
            )
            preview_rows = []

        return Response({'summary': obj.summary or {}, 'preview_rows': preview_rows})


class ReportView(APIView):
    """
    GET /api/report/<pk>/
    Generates a PDF report for the stored dataset (summary + chart + preview)
    Only for the owner (request.user).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        obj = get_object_or_404(UploadedDataset, pk=pk, user=request.user)

        df = None
        try:
            if getattr(obj.csv_file, 'path', None):
                df = pd.read_csv(obj.csv_file.path)
            else:
                with default_storage.open(obj.csv_file.name, mode='rb') as fh:
                    df = pd.read_csv(fh)
        except Exception:
            logger.exception("Failed to read CSV for ReportView (pk=%s)", pk)
            df = None

        chart_type = request.GET.get('chart_type', 'bar')

        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Header
            p.setFont("Helvetica-Bold", 16)
            p.drawString(72, height - 72, "Chemical Equipment Report")
            p.setFont("Helvetica", 10)
            p.drawString(72, height - 90, f"File: {obj.original_filename}")
            p.drawString(
                72,
                height - 104,
                f"Uploaded at: {obj.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Summary information
            summary = obj.summary or {}
            y = height - 130
            p.setFont("Helvetica-Bold", 12)
            p.drawString(72, y, "Summary")
            y -= 16
            p.setFont("Helvetica", 10)
            p.drawString(
                80, y, f"Total equipment: {summary.get('total_count', 'N/A')}"
            )
            y -= 14

            averages = summary.get('averages', {})
            p.drawString(80, y, "Averages:")
            y -= 12
            if isinstance(averages, dict):
                for k, v in averages.items():
                    try:
                        p.drawString(
                            92,
                            y,
                            f"{k}: {('N/A' if v is None else f'{v:.2f}')}"
                        )
                    except Exception:
                        p.drawString(92, y, f"{k}: {v}")
                    y -= 12

            # Type distribution
            y -= 6
            p.setFont("Helvetica-Bold", 11)
            p.drawString(72, y, "Type distribution")
            y -= 14
            type_dist = summary.get('type_distribution', {})
            if isinstance(type_dist, dict):
                for t, count in type_dist.items():
                    p.drawString(80, y, f"{t}: {count}")
                    y -= 12
                    if y < 180:
                        p.showPage()
                        y = height - 72

            # Insert chart image
            chart_buf = create_chart_image(summary, chart_type=chart_type)
            if chart_buf:
                try:
                    img = ImageReader(chart_buf)
                    img_w = 440
                    img_h = 240
                    x = 72
                    y_img = y - img_h - 10
                    if y_img < 72:
                        p.showPage()
                        y_img = height - 72 - img_h
                    p.drawImage(img, x, y_img, width=img_w, height=img_h)
                    y = y_img - 12
                except Exception:
                    logger.exception(
                        "Failed to embed chart image for dataset %s", pk
                    )

            # Preview table
            if df is not None and not df.empty:
                if y < 200:
                    p.showPage()
                    y = height - 72
                p.setFont("Helvetica-Bold", 11)
                p.drawString(72, y, "Preview (first rows)")
                y -= 18
                p.setFont("Helvetica", 9)
                preview = df.head(8)
                cols = preview.columns.tolist()
                x = 72
                for col in cols:
                    p.drawString(x, y, str(col)[:15])
                    x += 110
                y -= 14
                for _, row in preview.iterrows():
                    x = 72
                    for col in cols:
                        cell = str(row[col])[:15]
                        p.drawString(x, y, cell)
                        x += 110
                    y -= 12
                    if y < 72:
                        p.showPage()
                        y = height - 72

            p.showPage()
            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="report_dataset_{pk}.pdf"'
            )
            return response

        except Exception:
            logger.exception("Failed to generate PDF for dataset %s", pk)
            return Response(
                {'detail': 'Failed to generate PDF. Check server logs.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportFromSummaryView(APIView):
    """
    POST /api/report-from-summary/
    Accepts a summary + preview_rows + include options and returns a generated PDF.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        data = request.data or {}
        summary = data.get("summary", {}) or {}
        preview_rows = data.get("preview_rows", None)
        filename = data.get("filename") or "report.pdf"
        include = data.get("include", {}) or {}
        analysis_chart_types = data.get("analysis_chart_types", {}) or {}

        # defaults and selections from include block
        chart_type = include.get("type_chart_type", include.get("chart_type", "bar"))
        inc_summary = include.get("summary", True)
        inc_type_chart = include.get("type_chart", True)
        inc_preview = include.get("preview_rows", True)

        analysis_cfg = include.get("analysis", {}) or {}
        inc_analysis = analysis_cfg.get("include", False)
        analysis_mode = analysis_cfg.get("mode", "all")

        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Color scheme
            primary_color = (0, 123/255, 255/255)  # #007bff
            dark_gray = (51/255, 51/255, 51/255)   # #333
            light_gray = (245/255, 245/255, 245/255)  # #f5f5f5

            # Helper to draw section header
            def draw_section_header(canvas_obj, text, y_pos):
                canvas_obj.setFillColorRGB(*light_gray)
                canvas_obj.rect(72, y_pos - 20, width - 144, 24, fill=1, stroke=0)
                canvas_obj.setFont("Helvetica-Bold", 13)
                canvas_obj.setFillColorRGB(*dark_gray)
                canvas_obj.drawString(80, y_pos - 8, text)
                return y_pos - 36

            # Title + metadata
            p.setFont("Helvetica-Bold", 22)
            p.setFillColorRGB(*primary_color)
            p.drawString(72, height - 50, "Chemical Equipment Analysis Report")

            p.setFont("Helvetica", 10)
            p.setFillColorRGB(*dark_gray)
            username = getattr(request.user, "username", "user")
            p.drawString(72, height - 70, f"Generated by: {username}")
            p.drawString(
                72,
                height - 85,
                f"Date: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}"
            )

            p.setLineWidth(1.5)
            p.setStrokeColorRGB(*primary_color)
            p.line(72, height - 95, width - 72, height - 95)

            y = height - 120

            # SUMMARY SECTION
            if inc_summary:
                y = draw_section_header(p, "Summary Statistics", y)
                p.setFont("Helvetica", 10)
                p.setFillColorRGB(*dark_gray)

                total_count = summary.get('total_count', 'N/A')
                p.setFont("Helvetica-Bold", 11)
                p.drawString(80, y, f"Total Equipment Records: {total_count}")
                y -= 20

                p.setFont("Helvetica-Bold", 10)
                p.drawString(80, y, "Parameter Averages:")
                y -= 14

                averages = summary.get('averages', {}) or {}
                p.setFont("Helvetica", 10)
                if isinstance(averages, dict):
                    for k, v in averages.items():
                        try:
                            val_str = f"{v:.2f}" if v is not None else "N/A"
                        except Exception:
                            val_str = str(v) if v is not None else "N/A"
                        p.drawString(92, y, f"• {k}: {val_str}")
                        y -= 12
                y -= 8

            # TYPE distribution chart
            if inc_type_chart:
                if y < 280:
                    p.showPage()
                    y = height - 50

                y = draw_section_header(p, "Equipment Type Distribution", y)

                chart_buf = create_chart_image(
                    summary,
                    chart_type=chart_type,
                    width_inches=7,
                    height_inches=4,
                    dpi=100
                )
                if chart_buf:
                    try:
                        img = ImageReader(chart_buf)
                        img_w = width - 144
                        img_h = 300
                        p.drawImage(img, 72, y - img_h, width=img_w, height=img_h)
                        y -= (img_h + 20)
                    except Exception:
                        logger.exception(
                            "Failed to embed type distribution chart in ad-hoc report"
                        )
                        p.setFont("Helvetica", 10)
                        p.setFillColorRGB(220/255, 53/255, 69/255)
                        p.drawString(
                            72, y, "Failed to render type distribution chart."
                        )
                        y -= 20
                else:
                    p.setFont("Helvetica", 10)
                    p.setFillColorRGB(*dark_gray)
                    p.drawString(72, y, "Type distribution chart not available.")
                    y -= 20

            # ANALYSIS charts (per-type averages)
            if inc_analysis:
                per_type_avgs = (summary or {}).get('per_type_averages', {}) or {}
                if analysis_mode == 'all':
                    params_to_draw = ['Flowrate', 'Pressure', 'Temperature']
                else:
                    params_to_draw = ['Flowrate', 'Pressure', 'Temperature']

                if not per_type_avgs:
                    if y < 200:
                        p.showPage()
                        y = height - 50
                    y = draw_section_header(p, "Parameter Analysis", y)
                    p.setFont("Helvetica", 10)
                    p.setFillColorRGB(*dark_gray)
                    p.drawString(
                        72, y,
                        "Per-type averages not available for this dataset."
                    )
                    y -= 20
                else:
                    for param in params_to_draw:
                        data_dict = per_type_avgs.get(param, {}) or {}
                        if not data_dict:
                            continue

                        if y < 350:
                            p.showPage()
                            y = height - 50

                        y = draw_section_header(
                            p, f"Analysis - Average {param} by Type", y
                        )

                        try:
                            buf_img = io.BytesIO()
                            plt.figure(figsize=(7, 4), dpi=100)
                            labels = list(data_dict.keys())
                            vals = [
                                data_dict[k] if data_dict[k] is not None else 0
                                for k in labels
                            ]

                            param_chart_type = (
                                analysis_chart_types.get(param, 'bar')
                                if isinstance(analysis_chart_types, dict)
                                else 'bar'
                            )

                            if param_chart_type == 'bar':
                                plt.bar(
                                    labels,
                                    vals,
                                    color='#007bff',
                                    edgecolor='#0056b3',
                                    linewidth=1.5
                                )
                            elif param_chart_type == 'pie':
                                if sum(vals) == 0:
                                    plt.bar(labels, vals)
                                else:
                                    colors = [
                                        '#FF6B6B',
                                        '#4ECDC4',
                                        '#45B7D1',
                                        '#FFA07A',
                                        '#98D8C8'
                                    ]
                                    plt.pie(
                                        vals,
                                        labels=None,
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        colors=colors[:len(vals)]
                                    )
                                    plt.legend(
                                        labels,
                                        loc="center left",
                                        bbox_to_anchor=(1.0, 0.5),
                                        fontsize=9
                                    )
                                    plt.axis('equal')
                            elif param_chart_type == 'line':
                                plt.plot(
                                    labels,
                                    vals,
                                    marker='o',
                                    linewidth=2,
                                    markersize=8,
                                    color='#0056b3'
                                )
                                plt.fill_between(
                                    range(len(labels)),
                                    vals,
                                    alpha=0.3,
                                    color='#007bff'
                                )
                            elif param_chart_type == 'hist':
                                plt.hist(
                                    vals,
                                    bins=min(10, max(1, len(vals))),
                                    edgecolor='black',
                                    color='#FF6B6B'
                                )
                            else:
                                plt.bar(
                                    labels,
                                    vals,
                                    color='#007bff',
                                    edgecolor='#0056b3',
                                    linewidth=1.5
                                )

                            plt.title(
                                f'Average {param} by Equipment Type',
                                fontsize=12,
                                fontweight='bold',
                                pad=15
                            )
                            plt.ylabel(param, fontsize=10, fontweight='bold')
                            plt.xlabel('Equipment Type', fontsize=10, fontweight='bold')
                            plt.xticks(
                                rotation=45,
                                ha='right',
                                fontsize=9
                            )
                            plt.grid(axis='y', alpha=0.3, linestyle='--')
                            plt.tight_layout(pad=0.5)
                            plt.savefig(
                                buf_img,
                                format='png',
                                bbox_inches='tight',
                                pad_inches=0.15,
                                dpi=100
                            )
                            plt.close()
                            buf_img.seek(0)

                            img = ImageReader(buf_img)
                            img_w = width - 144
                            img_h = 280
                            p.drawImage(
                                img,
                                72,
                                y - img_h,
                                width=img_w,
                                height=img_h
                            )
                            y -= (img_h + 20)
                        except Exception:
                            logger.exception(
                                "Failed to render analysis chart for %s", param
                            )
                            p.setFont("Helvetica", 10)
                            p.setFillColorRGB(220/255, 53/255, 69/255)
                            p.drawString(
                                72,
                                y,
                                f"Failed to draw analysis chart for {param}."
                            )
                            y -= 20

            # PREVIEW rows
            if inc_preview and preview_rows:
                if y < 250:
                    p.showPage()
                    y = height - 50

                y = draw_section_header(p, "Data Preview", y)

                p.setFont("Helvetica", 9)
                p.setFillColorRGB(*dark_gray)
                cols = list(preview_rows[0].keys()) if preview_rows else []

                if cols:
                    p.setFillColorRGB(*light_gray)
                    p.rect(72, y - 18, width - 144, 18, fill=1, stroke=0)

                    p.setFont("Helvetica-Bold", 9)
                    p.setFillColorRGB(*dark_gray)
                    col_width = (width - 144) / max(1, len(cols))
                    x = 72
                    for col in cols:
                        p.drawString(x + 4, y - 12, str(col)[:12])
                        x += col_width
                    y -= 20

                    p.setFont("Helvetica", 8)
                    row_count = 0
                    for row in preview_rows[:10]:
                        if y < 100:
                            p.showPage()
                            y = height - 50

                        if row_count % 2 == 0:
                            p.setFillColorRGB(245/255, 248/255, 250/255)
                            p.rect(72, y - 14, width - 144, 14, fill=1, stroke=0)

                        p.setFillColorRGB(*dark_gray)
                        x = 72
                        for col in cols:
                            cell_val = str(row.get(col, ""))[:12]
                            p.drawString(x + 4, y - 10, cell_val)
                            x += col_width

                        y -= 14
                        row_count += 1
                else:
                    p.drawString(72, y, "No data available.")
                    y -= 20

            p.showPage()
            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception:
            logger.exception("Failed to generate ad-hoc PDF")
            return Response(
                {'detail': 'Failed to generate PDF (server).'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
