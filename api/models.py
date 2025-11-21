# api/models.py
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save
import os


class UploadedDataset(models.Model):
    """
    Stores uploaded CSV file metadata and a JSON summary.

    Fields:
      - user: owner of the upload (optional during initial migration; make non-nullable later if desired)
      - original_filename: original uploaded filename
      - csv_file: FileField stored under MEDIA_ROOT/uploads/
      - uploaded_at: timestamp of upload
      - summary: JSON summary computed after upload (counts, averages, per-type avgs, preview rows, etc.)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploads',
        null=True,  # keep nullable initially if adding to an existing DB; remove later to enforce ownership
        blank=True
    )
    original_filename = models.CharField(max_length=255)
    csv_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    summary = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Uploaded Dataset"
        verbose_name_plural = "Uploaded Datasets"

    def __str__(self):
        user_part = f" - {self.user}" if self.user else ""
        return f"{self.original_filename}{user_part} ({self.uploaded_at:%Y-%m-%d %H:%M:%S})"

    @property
    def csv_local_path(self):
        """
        Return the local filesystem path to the uploaded file when available.
        This is useful for tooling that will transform local paths into served URLs.
        """
        try:
            # If the storage is local FileSystemStorage, .path exists
            return self.csv_file.path
        except Exception:
            # Fall back to the storage name (relative path in storage)
            return self.csv_file.name if self.csv_file else None


# -------------------------
# File cleanup signals
# -------------------------
# When a model instance is deleted, remove the file from storage as well.
@receiver(post_delete, sender=UploadedDataset)
def delete_file_on_record_delete(sender, instance, **kwargs):
    """
    Delete the underlying file when the UploadedDataset record is deleted.
    """
    file = instance.csv_file
    try:
        if file and file.name:
            # file.delete() will remove from storage
            file.delete(save=False)
    except Exception:
        # never raise here; log in production if desired
        pass


# If a new file is uploaded to replace the old one, delete the old file
@receiver(pre_save, sender=UploadedDataset)
def delete_file_on_change(sender, instance, **kwargs):
    """
    If updating an existing UploadedDataset with a new file, remove the old file to avoid orphan files.
    """
    if not instance.pk:
        return  # new instance, nothing to do

    try:
        old = UploadedDataset.objects.filter(pk=instance.pk).first()
    except Exception:
        old = None

    if not old:
        return

    old_file = old.csv_file
    new_file = instance.csv_file

    try:
        # If file changed (and old existed), delete old
        if old_file and old_file.name and new_file and old_file.name != new_file.name:
            old_file.delete(save=False)
    except Exception:
        # ignore failures here to avoid blocking save
        pass
