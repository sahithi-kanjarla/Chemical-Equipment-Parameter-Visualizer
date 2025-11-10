from rest_framework import serializers
from .models import UploadedDataset

class UploadedDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedDataset
        fields = ['id', 'original_filename', 'csv_file', 'uploaded_at', 'summary']
        read_only_fields = ['id', 'uploaded_at', 'summary']
