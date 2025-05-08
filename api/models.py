from django.db import models

class JournalEntry(models.Model):
    draft_text = models.TextField()