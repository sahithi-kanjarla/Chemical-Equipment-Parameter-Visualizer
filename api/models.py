from django.db import models

# Create your models here.
from django.db import models

class UploadedDataset(models.Model):
    """
    Stores uploaded CSV file metadata and a JSON summary.
    We keep file in media/uploads/ and store computed summary in JSONField.
    """
    original_filename = models.CharField(max_length=255)
    csv_file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # summary structure example:
    # {
    #   "total_count": 10,
    #   "averages": {"Flowrate": 12.3, "Pressure": 45.6, "Temperature": 78.9},
    #   "type_distribution": {"Pump": 5, "Compressor": 3, "HeatExchanger": 2}
    # }
    summary = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_at:%Y-%m-%d %H:%M:%S})"
