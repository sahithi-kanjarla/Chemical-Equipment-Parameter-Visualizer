from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import UploadedDataset

@admin.register(UploadedDataset)
class UploadedDatasetAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'uploaded_at', 'total_count_display')
    readonly_fields = ('uploaded_at', 'summary', 'csv_file')

    def total_count_display(self, obj):
        return obj.summary.get('total_count') if obj.summary else None
    total_count_display.short_description = 'Total Count'
