from django.db import models

class JournalEntry(models.Model):
    draft_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)