from __future__ import annotations
import json
from django.db import models, transaction
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from .models import Column, Task, Board
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm

# Заглушка
def Skeb(request):
    return HttpResponse("<h5>Skebooob</h5>")

# Регистрация
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаём доску по умолчанию для нового пользователя
            Board.objects.create(owner=user, name="Моя доска")
            login(request, user)
            return redirect('board')
    else:
        form = RegisterForm()
    return render(request, 'trackers/register.html', {'form': form})

# Логин
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('board')
    else:
        form = LoginForm()
    return render(request, 'trackers/login.html', {'form': form})

# Выход
def logout_view(request):
    logout(request)
    return redirect('login')

# Главная доска
@login_required(login_url='login')
def board(request):
    board = Board.objects.filter(owner=request.user).first()
    if not board:
        board = Board.objects.create(owner=request.user, name="Моя доска")
    columns = Column.objects.filter(board=board).prefetch_related("tasks").order_by("position")
    return render(request, "trackers/dashboard.html", {"columns": columns, "board": board})

# Колонки
@login_required(login_url='login')
def add_column(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return redirect("board")
        board = Board.objects.filter(owner=request.user).first()
        if not board:
            board = Board.objects.create(owner=request.user, name="Моя доска")
        with transaction.atomic():
            max_pos = Column.objects.filter(board=board).aggregate(max_pos=models.Max("position"))["max_pos"] or 0
            Column.objects.create(title=title, position=max_pos + 1, board=board)
    return redirect("board")

@login_required(login_url='login')
@require_POST
def delete_column(request, column_id):
    column = get_object_or_404(Column, pk=column_id)
    column.delete()
    return redirect("board")

@login_required(login_url='login')
def edit_column(request, column_id):
    column = get_object_or_404(Column, pk=column_id)
    if request.method == "POST":
        new_title = (request.POST.get("title") or "").strip()
        if new_title:
            column.title = new_title
            column.save()
    return redirect("board")

# Задачи
@login_required(login_url='login')
def add_task(request, column_id: int):
    column = get_object_or_404(Column, id=column_id)
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return redirect("board")
        with transaction.atomic():
            max_pos = Task.objects.select_for_update().filter(column=column).aggregate(max_pos=models.Max("position"))["max_pos"] or 0
            Task.objects.create(column=column, title=title, position=max_pos + 1, created_by=request.user)
    return redirect("board")

@login_required(login_url='login')
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    old_col_id = task.column_id
    old_pos = task.position
    task.delete()
    Task.objects.filter(column_id=old_col_id, position__gt=old_pos).update(position=models.F("position") - 1)
    return redirect("board")

@login_required(login_url='login')
def edit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        new_title = (request.POST.get("title") or "").strip()
        if new_title:
            task.title = new_title
            task.save()
    return redirect("board")

# Drag & drop
@login_required(login_url='login')
@require_POST
def move_task(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        task_id = int(data["task_id"])
        to_column_id = int(data["to_column_id"])
        to_index_0 = int(data["to_index"])
    except Exception:
        return HttpResponseBadRequest("Bad payload")

    with transaction.atomic():
        task = get_object_or_404(Task.objects.select_for_update(), pk=task_id)
        old_col_id = task.column_id
        old_pos = task.position
        new_col_id = to_column_id
        new_pos = max(1, to_index_0 + 1)

        if new_col_id == old_col_id:
            count_in_col = Task.objects.filter(column_id=old_col_id).count()
            new_pos = min(new_pos, count_in_col)
            if new_pos == old_pos:
                return JsonResponse({"ok": True})
            if new_pos < old_pos:
                Task.objects.filter(column_id=old_col_id, position__gte=new_pos, position__lt=old_pos).update(
                    position=models.F("position") + 1
                )
            else:
                Task.objects.filter(column_id=old_col_id, position__gt=old_pos, position__lte=new_pos).update(
                    position=models.F("position") - 1
                )
            task.position = new_pos
            task.updated_at = now()
            task.save(update_fields=["position", "updated_at"])
        else:
            Task.objects.filter(column_id=old_col_id, position__gt=old_pos).update(position=models.F("position") - 1)
            count_in_target = Task.objects.filter(column_id=new_col_id).count()
            new_pos = min(max(1, new_pos), count_in_target + 1)
            Task.objects.filter(column_id=new_col_id, position__gte=new_pos).update(position=models.F("position") + 1)
            task.column_id = new_col_id
            task.position = new_pos
            task.updated_at = now()
            task.save(update_fields=["column", "position", "updated_at"])
    return JsonResponse({"ok": True})
