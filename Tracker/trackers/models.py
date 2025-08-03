
from django.db import models

class Column(models.Model):
    title = models.CharField(max_length=200)
    position = models.PositiveIntegerField()
    class Meta:
        ordering = ["position", "id"]

class Task(models.Model):
    column = models.ForeignKey(Column, related_name="tasks", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["column", "position"], name="uniq_task_column_position")
        ]
