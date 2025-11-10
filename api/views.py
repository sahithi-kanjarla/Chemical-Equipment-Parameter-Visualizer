from django.shortcuts import render

import io
import pandas as pd
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedDataset
from .serializers import UploadedDatasetSerializer

# small health-check already in place; keep or redefine
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

@require_GET
def api_root(request):
    return JsonResponse({
        "status": "ok",
        "message": "API root is working."
    })

class UploadCSVView(APIView):
    """
    POST /api/upload/
    multipart/form-data with field 'file' (CSV)
    Returns created object id and the computed summary.
    """
    permission_classes = [permissions.IsAuthenticated]  # require auth
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"detail": "No file provided in 'file' field."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Basic filename
        filename = uploaded_file.name

        try:
            # Read CSV into pandas (in-memory)
            # Use read_csv on uploaded_file (it is file-like)
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            return Response({"detail": f"Failed to read CSV: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

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

        # Save file contents to model (store original bytes)
        # Need to rewind file to read bytes if pandas consumed it
        if hasattr(uploaded_file, 'read'):
            uploaded_file.seek(0)

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
        return Response({'id': obj.id, 'summary': summary, 'object': serializer.data},
                        status=status.HTTP_201_CREATED)


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
    Returns summary JSON for a given upload id.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        obj = get_object_or_404(UploadedDataset, pk=pk)
        return Response(obj.summary)

