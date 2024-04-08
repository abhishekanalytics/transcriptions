from django.db import models

class Transcription(models.Model):
    file = models.FileField(null=False, blank=False, upload_to='uploads/')
    file_url = models.URLField(null=False, blank=False)
    result_url = models.URLField(null=False, blank=False)
    transcription_text = models.JSONField(null=False, blank=False)
    sync_map = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
