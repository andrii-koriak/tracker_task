from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Board, Column

@receiver(post_save, sender=User)
def create_user_board(sender, instance, created, **kwargs):
    if created:
        board = Board.objects.create(owner=instance, name=f"Доска {instance.username or instance.email}")
        Column.objects.create(board=board, title="To Do", position=1)
        Column.objects.create(board=board, title="In Progress", position=2)
        Column.objects.create(board=board, title="Done", position=3)