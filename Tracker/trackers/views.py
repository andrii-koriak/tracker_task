from __future__ import annotations
import json
from django.db import models, transaction
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from .models import Column, Task



def about(request):
    return HttpResponse("<h7>Їбати за карпати</h7>")

def Skeb(request):
    return HttpResponse("<h5>Skebooob</h5>")

def board(request):
    # Колонки по position; задачи внутри колонок уже отсортированы по Meta.ordering
    columns = Column.objects.all().order_by("position").prefetch_related("tasks")
    return render(request, "trackers/dashboard.html", {"columns": columns})

def add_column(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return redirect("board")

        with transaction.atomic():
            max_pos = Column.objects.select_for_update().aggregate(
                max_pos=models.Max("position")
            )["max_pos"] or 0

            Column.objects.create(
                title=title,
                position=max_pos + 1,
            )

    return redirect("board")

def add_task(request, column_id: int):
    column = get_object_or_404(Column, id=column_id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return redirect("board")

        with transaction.atomic():
            # блокируем задачи колонки, чтобы исключить гонки при одновременных добавлениях
            max_pos = (
                Task.objects.select_for_update()
                .filter(column=column)
                .aggregate(max_pos=models.Max("position"))
            )["max_pos"] or 0

            Task.objects.create(
                column=column,
                title=title,
                position=max_pos + 1,
            )

    return redirect("board")

@require_POST
def move_task(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        task_id = int(data["task_id"])
        to_column_id = int(data["to_column_id"])
        to_index_0 = int(data["to_index"])  # индекс в списке DOM (0-based)
    except Exception:
        return HttpResponseBadRequest("Bad payload")

    with transaction.atomic():
        # блокируем перемещаемую задачу
        task = get_object_or_404(Task.objects.select_for_update(), pk=task_id)

        old_col_id = task.column_id
        old_pos = task.position
        new_col_id = to_column_id
        new_pos = max(1, to_index_0 + 1)  # в БД позиции 1-based

        if new_col_id == old_col_id:
            # Перемещение внутри одной колонки
            count_in_col = Task.objects.filter(column_id=old_col_id).count()
            new_pos = min(new_pos, count_in_col)

            if new_pos == old_pos:
                return JsonResponse({"ok": True})

            if new_pos < old_pos:
                Task.objects.filter(
                    column_id=old_col_id,
                    position__gte=new_pos,
                    position__lt=old_pos,
                ).update(position=models.F("position") + 1)
            else:
                Task.objects.filter(
                    column_id=old_col_id,
                    position__gt=old_pos,
                    position__lte=new_pos,
                ).update(position=models.F("position") - 1)

            task.position = new_pos
            task.updated_at = now()
            task.save(update_fields=["position", "updated_at"])

        else:

            Task.objects.filter(column_id=old_col_id, position__gt=old_pos).update(
                position=models.F("position") - 1
            )

            # 2) Вычислить корректную позицию в целевой колонке
            count_in_target = Task.objects.filter(column_id=new_col_id).count()
            new_pos = min(max(1, new_pos), count_in_target + 1)

            # 3) Освободить место в целевой колонке
            Task.objects.filter(column_id=new_col_id, position__gte=new_pos).update(
                position=models.F("position") + 1
            )

            # 4) Перенести задачу
            task.column_id = new_col_id
            task.position = new_pos
            task.updated_at = now()
            task.save(update_fields=["column", "position", "updated_at"])

    return JsonResponse({"ok": True})
