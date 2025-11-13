# api/views.py
import io
import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import pandas as pd

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UploadedDataset
from .serializers import UploadedDatasetSerializer

# PDF generation (ReportLab)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Matplotlib for chart rendering (non-GUI backend)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def create_chart_image(summary, chart_type='bar'):
    """
    Creates a matplotlib chart from `summary` and returns a BytesIO containing PNG image.
    Improved layout: wider figure, rotated ticks, smaller tick fonts, tight_layout with padding.
    """
    buf = io.BytesIO()
    try:
        type_dist = (summary or {}).get('type_distribution', {}) or {}
        labels = list(type_dist.keys())
        counts = [type_dist.get(k, 0) for k in labels]

        # make figure wider so labels have space
        plt.figure(figsize=(8, 3.5), dpi=100)

        if chart_type == 'bar':
            plt.bar(labels, counts)
            plt.title('Count by Equipment Type')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right', fontsize=9)
        elif chart_type == 'pie':
            if sum(counts) == 0:
                plt.text(0.5, 0.5, 'No data', ha='center')
            else:
                plt.pie(counts, labels=labels, autopct='%1.0f%%')
                plt.title('Type Distribution (%)')
        elif chart_type == 'line':
            plt.plot(labels, counts, marker='o')
            plt.title('Type counts (line)')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right', fontsize=9)
        elif chart_type == 'hist':
            nums = []
            avgs = (summary or {}).get('averages', {}) or {}
            for v in avgs.values():
                if v is not None:
                    nums.append(v)
            if not nums:
                nums = counts
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

        # tighten layout and save with tight bbox
        plt.tight_layout(pad=0.4)
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close()
        buf.seek(0)
        return buf
    except Exception:
        try:
            plt.close()
        except Exception:
            pass
        logger.exception("create_chart_image failed")
        return None

def api_root(request):
    """
    Minimal API root / health check.
    """
    return JsonResponse({
        "status": "ok",
        "message": "API root is working."
    })


class UploadCSVView(APIView):
    """
    POST /api/upload/
    multipart/form-data with field 'file' (CSV)
    Returns created object id, the computed summary, and a small preview_rows list.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"detail": "No file provided in 'file' field."},
                            status=status.HTTP_400_BAD_REQUEST)

        filename = uploaded_file.name

        try:
            # Read CSV into pandas (uploaded_file is file-like)
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            logger.exception("Failed to read CSV on upload: %s", e)
            return Response({"detail": f"Failed to read CSV: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        required = {'Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature'}
        if not required.issubset(set(df.columns)):
            return Response({
                "detail": f"CSV missing required columns. Required: {required}. Found: {list(df.columns)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Coerce numeric columns
        for col in ['Flowrate', 'Pressure', 'Temperature']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # compute summary
        numeric_cols = ['Flowrate', 'Pressure', 'Temperature']
        averages = {col: (float(df[col].mean()) if not df[col].dropna().empty else None)
                    for col in numeric_cols}
        type_distribution = df['Type'].value_counts().to_dict()
        total_count = int(df.shape[0])

        summary = {
            'total_count': total_count,
            'averages': averages,
            'type_distribution': type_distribution
        }

        # compute per-type averages for each numeric column and add to summary
        try:
            per_type_avgs = {}
            for col in numeric_cols:
                grouped = df.groupby('Type')[col].mean()
                # convert to plain python floats / None
                per_type_avgs[col] = {str(k): (float(v) if not pd.isna(v) else None) for k, v in grouped.to_dict().items()}
            summary['per_type_averages'] = per_type_avgs
        except Exception:
            # if something goes wrong, ensure key exists and keep going
            summary['per_type_averages'] = {}

        # prepare preview rows (first up to 8 rows) as list of dicts
        try:
            preview_rows = df.head(8).to_dict(orient='records')
        except Exception:
            preview_rows = []

        # Save file contents to model (store original bytes)
        try:
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
        except Exception:
            pass

        content = uploaded_file.read()
        django_file = ContentFile(content, name=filename)

        obj = UploadedDataset.objects.create(
            original_filename=filename,
            csv_file=django_file,
            summary=summary
        )

        # Prune older entries: keep only last 5
        qs = UploadedDataset.objects.order_by('-uploaded_at')
        to_delete = qs[5:]
        for old in to_delete:
            try:
                old.csv_file.delete(save=False)
            except Exception:
                pass
            old.delete()

        serializer = UploadedDatasetSerializer(obj)
        return Response({
            'id': obj.id,
            'summary': summary,
            'object': serializer.data,
            'preview_rows': preview_rows
        }, status=status.HTTP_201_CREATED)


class HistoryView(APIView):
    """
    GET /api/history/
    Returns last 5 UploadedDataset entries (metadata + summary).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        qs = UploadedDataset.objects.order_by('-uploaded_at')[:5]
        serializer = UploadedDatasetSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class DatasetSummaryView(APIView):
    """
    GET /api/summary/<int:pk>/
    Returns summary JSON + preview_rows for a given upload id.
    Response shape:
      {
        "summary": { ... },
        "preview_rows": [ {row}, ... ]   # up to first 8 rows
      }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        obj = get_object_or_404(UploadedDataset, pk=pk)

        # default empty preview
        preview_rows = []

        # try reading CSV stored with this object
        try:
            if getattr(obj.csv_file, 'path', None):
                df = pd.read_csv(obj.csv_file.path)
            else:
                with default_storage.open(obj.csv_file.name, mode='rb') as fh:
                    df = pd.read_csv(fh)
            # normalize columns to strings and take first 8 rows
            df.columns = [str(c).strip() for c in df.columns]
            preview_rows = df.head(8).to_dict(orient='records')
        except Exception:
            # if reading fails, leave preview_rows empty and log
            logger.exception("Failed to read CSV for preview in DatasetSummaryView (pk=%s)", pk)

        # return both summary and preview_rows
        return Response({'summary': obj.summary or {}, 'preview_rows': preview_rows})


class ReportView(APIView):
    """
    GET /api/report/<pk>/
    Generates a PDF report for the stored dataset (summary + chart + preview)
    Query param: chart_type (optional) -> 'bar'|'pie'|'line'|'hist'
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        obj = get_object_or_404(UploadedDataset, pk=pk)

        # Try to read CSV associated with this object for preview
        df = None
        try:
            if getattr(obj.csv_file, 'path', None):
                df = pd.read_csv(obj.csv_file.path)
            else:
                with default_storage.open(obj.csv_file.name, mode='rb') as fh:
                    df = pd.read_csv(fh)
        except Exception as e:
            logger.exception("Failed to read CSV for ReportView (pk=%s): %s", pk, e)
            df = None  # proceed without preview

        # Chart type from query param
        chart_type = request.GET.get('chart_type', 'bar')

        # Create PDF in memory
        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Header
            p.setFont("Helvetica-Bold", 16)
            p.drawString(72, height - 72, "Chemical Equipment Report")
            p.setFont("Helvetica", 10)
            p.drawString(72, height - 90, f"File: {obj.original_filename}")
            p.drawString(72, height - 104, f"Uploaded at: {obj.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Summary information
            summary = obj.summary or {}
            y = height - 130
            p.setFont("Helvetica-Bold", 12)
            p.drawString(72, y, "Summary")
            y -= 16
            p.setFont("Helvetica", 10)
            p.drawString(80, y, f"Total equipment: {summary.get('total_count', 'N/A')}")
            y -= 14

            averages = summary.get('averages', {})
            p.drawString(80, y, "Averages:")
            y -= 12
            if isinstance(averages, dict):
                for k, v in averages.items():
                    try:
                        # use f-string (avoid shadowing built-in format)
                        p.drawString(92, y, f"{k}: {('N/A' if v is None else f'{v:.2f}')}")
                    except Exception:
                        p.drawString(92, y, f"{k}: {v}")
                    y -= 12

            # Type distribution
            y -= 6
            p.setFont("Helvetica-Bold", 11)
            p.drawString(72, y, "Type distribution")
            y -= 14
            p.setFont("Helvetica", 10)
            type_dist = summary.get('type_distribution', {})
            if isinstance(type_dist, dict):
                for t, count in type_dist.items():
                    p.drawString(80, y, f"{t}: {count}")
                    y -= 12
                    if y < 180:
                        p.showPage()
                        y = height - 72

            # Insert chart image (if possible)
            chart_buf = create_chart_image(summary, chart_type=chart_type)
            if chart_buf:
                try:
                    img = ImageReader(chart_buf)
                    img_w = 440  # points
                    img_h = 240
                    x = 72
                    y_img = y - img_h - 10
                    if y_img < 72:
                        p.showPage()
                        y_img = height - 72 - img_h
                    p.drawImage(img, x, y_img, width=img_w, height=img_h)
                    y = y_img - 12
                except Exception:
                    logger.exception("Failed to embed chart image for dataset %s", pk)

            # Preview table (first up to 8 rows)
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
                # header
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
            response['Content-Disposition'] = f'attachment; filename="report_dataset_{pk}.pdf"'
            return response

        except Exception as e:
            logger.exception("Failed to generate PDF for dataset %s: %s", pk, e)
            return Response({'detail': 'Failed to generate PDF. Check server logs.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportFromSummaryView(APIView):
    """
    POST /api/report-from-summary/
    Expected JSON:
    {
      "filename": "optional_name.pdf",
      "include": {
        "summary": true,
        "type_chart": true,
        "type_chart_type": "bar" | "pie" | "line" | "hist",
        "analysis": { "include": true, "mode": "single"|"multi", "parameter": "Flowrate", "chart_type": "bar" },
        "preview_rows": true
      },
      "summary": {...},
      "preview_rows": [...]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        data = request.data or {}
        summary = data.get("summary", {}) or {}
        preview_rows = data.get("preview_rows", None)
        filename = data.get("filename") or "report.pdf"
        include = data.get("include", {}) or {}

        # defaults and selections from include block
        chart_type = include.get("type_chart_type", include.get("chart_type", "bar"))
        inc_summary = include.get("summary", True)
        inc_type_chart = include.get("type_chart", True)
        inc_preview = include.get("preview_rows", True)

        analysis_cfg = include.get("analysis", {}) or {}
        inc_analysis = analysis_cfg.get("include", False)
        analysis_mode = analysis_cfg.get("mode", "single")
        analysis_param = analysis_cfg.get("parameter", "Flowrate")
        analysis_chart_type = analysis_cfg.get("chart_type", "bar")  # applies to analysis charts

        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Header
            p.setFont("Helvetica-Bold", 16)
            p.drawString(72, height - 72, "Chemical Equipment Report (Ad-hoc)")
            p.setFont("Helvetica", 10)
            p.drawString(72, height - 90, f"Generated by: {request.user.username if request.user and hasattr(request.user,'username') else 'user'}")
            p.drawString(72, height - 104, f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

            y = height - 132

            # SUMMARY
            if inc_summary:
                p.setFont("Helvetica-Bold", 12)
                p.drawString(72, y, "Summary")
                y -= 16
                p.setFont("Helvetica", 10)
                p.drawString(80, y, f"Total equipment: {summary.get('total_count', 'N/A')}")
                y -= 14

                averages = summary.get('averages', {}) or {}
                p.drawString(80, y, "Averages:")
                y -= 12
                if isinstance(averages, dict):
                    for k, v in averages.items():
                        try:
                            p.drawString(92, y, f"{k}: {('N/A' if v is None else f'{v:.2f}')}")
                        except Exception:
                            p.drawString(92, y, f"{k}: {v}")
                        y -= 12
                y -= 6

            # TYPE distribution chart (Matplotlib) - use `chart_type` from include
            if inc_type_chart:
                if y < 240:
                    p.showPage()
                    y = height - 72
                chart_buf = create_chart_image(summary, chart_type=chart_type)
                if chart_buf:
                    try:
                        img = ImageReader(chart_buf)
                        img_w = width - 144
                        img_h = img_w * 0.45
                        if img_h > (height - 160):
                            img_h = height - 160
                        p.drawImage(img, 72, y - img_h, width=img_w, height=img_h)
                        y -= (img_h + 12)
                    except Exception:
                        logger.exception("Failed to embed type distribution chart in ad-hoc report")
                        p.setFont("Helvetica", 10)
                        p.drawString(72, y, "Failed to render type distribution chart.")
                        y -= 18
                else:
                    p.setFont("Helvetica", 10)
                    p.drawString(72, y, "Type distribution chart not available.")
                    y -= 18

            # ANALYSIS charts (per-type averages) - uses analysis_chart_type
            if inc_analysis:
                per_type_avgs = (summary or {}).get('per_type_averages', {}) or {}
                if analysis_mode == 'single':
                    params_to_draw = [analysis_param]
                else:
                    params_to_draw = ['Flowrate', 'Pressure', 'Temperature']

                if not per_type_avgs:
                    if y < 120:
                        p.showPage()
                        y = height - 72
                    p.setFont("Helvetica-Bold", 11)
                    p.drawString(72, y, "Analysis")
                    y -= 14
                    p.setFont("Helvetica", 10)
                    p.drawString(72, y, "Per-type averages not available for this dataset. Re-upload dataset to compute analysis charts.")
                    y -= 18
                else:
                    for param in params_to_draw:
                        data_dict = per_type_avgs.get(param, {}) or {}
                        if not data_dict:
                            if y < 120:
                                p.showPage()
                                y = height - 72
                            p.setFont("Helvetica-Bold", 11)
                            p.drawString(72, y, f"Analysis - {param}")
                            y -= 14
                            p.setFont("Helvetica", 10)
                            p.drawString(72, y, f"No per-type averages available for {param}.")
                            y -= 18
                            continue

                        # Render analysis chart using analysis_chart_type
                        try:
                            buf_img = io.BytesIO()
                            # make chart with chosen type
                            plt.figure(figsize=(8, 2.8), dpi=100)
                            labels = list(data_dict.keys())
                            vals = [data_dict[k] if data_dict[k] is not None else 0 for k in labels]

                            if analysis_chart_type == 'bar':
                                plt.bar(labels, vals)
                            elif analysis_chart_type == 'pie':
                                # pie needs non-zero values, fall back to bar if all zero
                                if sum(vals) == 0:
                                    plt.bar(labels, vals)
                                else:
                                    plt.pie(vals, labels=labels, autopct='%1.0f%%')
                            elif analysis_chart_type == 'line':
                                plt.plot(labels, vals, marker='o')
                            elif analysis_chart_type == 'hist':
                                plt.hist(vals, bins=min(10, max(1, len(vals))), edgecolor='black')
                            else:
                                plt.bar(labels, vals)

                            plt.title(f'Average {param} by Type')
                            plt.ylabel(param)
                            plt.xticks(rotation=45, ha='right', fontsize=8)
                            plt.tight_layout(pad=0.3)
                            plt.savefig(buf_img, format='png', bbox_inches='tight', pad_inches=0.08)
                            plt.close()
                            buf_img.seek(0)

                            # embed into PDF
                            if y < 200:
                                p.showPage()
                                y = height - 72
                            img = ImageReader(buf_img)
                            img_w = width - 144
                            img_h = img_w * 0.28
                            if img_h > (height - 140):
                                img_h = height - 140
                            p.drawImage(img, 72, y - img_h, width=img_w, height=img_h)
                            y -= (img_h + 12)
                        except Exception:
                            logger.exception("Failed to render analysis chart for %s", param)
                            if y < 120:
                                p.showPage()
                                y = height - 72
                            p.setFont("Helvetica", 10)
                            p.drawString(72, y, f"Failed to draw analysis chart for {param}.")
                            y -= 18

            # PREVIEW rows table (if requested)
            if inc_preview and preview_rows:
                if y < 200:
                    p.showPage()
                    y = height - 72
                p.setFont("Helvetica-Bold", 11)
                p.drawString(72, y, "Preview (provided rows)")
                y -= 18
                p.setFont("Helvetica", 9)
                cols = list(preview_rows[0].keys()) if preview_rows else []
                x = 72
                colw = max(80, (width - 144) // max(1, len(cols)))
                for col in cols:
                    p.drawString(x, y, str(col)[:15])
                    x += colw
                y -= 14
                for row in preview_rows[:8]:
                    x = 72
                    for col in cols:
                        cell = str(row.get(col, ""))[:15]
                        p.drawString(x, y, cell)
                        x += colw
                    y -= 12
                    if y < 72:
                        p.showPage()
                        y = height - 72

            p.showPage()
            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.exception("Failed to generate ad-hoc PDF: %s", e)
            return Response({'detail': 'Failed to generate PDF (server).'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
