from django.db import models
from django.contrib.auth.models import AbstractUser


# Пользователь
class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


# Доска
class Board(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boards")
    name = models.CharField(max_length=255, default="Моя доска")

    def __str__(self):
        return f"{self.name} ({self.owner.email})"


# Колонка
class Column(models.Model):
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="columns",
        blank=True
    )
    title = models.CharField(max_length=200)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.title} ({self.board.name if self.board else 'Без доски'})"


# Задача
class Task(models.Model):
    column = models.ForeignKey(Column, related_name="tasks", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["column", "position"], name="uniq_task_column_position")
        ]

    def __str__(self):
        return self.title
