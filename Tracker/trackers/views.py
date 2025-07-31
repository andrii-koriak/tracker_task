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
    columns = Column.objects.all().order_by("position").prefetch_related("tasks")
    return render(request, "trackers/dashboard.html", {"columns": columns})


# -------------------- КОЛОНКИ --------------------

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


@require_POST
def delete_column(request, column_id):
    column = get_object_or_404(Column, pk=column_id)
    column.delete()
    return redirect("board")


def edit_column(request, column_id):
    column = get_object_or_404(Column, pk=column_id)

    if request.method == "POST":
        new_title = (request.POST.get("title") or "").strip()
        if new_title:
            with transaction.atomic():
                column = Column.objects.select_for_update().get(pk=column_id)
                column.title = new_title
                column.save()
    return redirect("board")


# -------------------- ЗАДАЧІ --------------------

def add_task(request, column_id: int):
    column = get_object_or_404(Column, id=column_id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return redirect("board")

        with transaction.atomic():
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
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return redirect("board")


def edit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == "POST":
        new_title = (request.POST.get("title") or "").strip()
        if new_title:
            with transaction.atomic():
                task = Task.objects.select_for_update().get(pk=task_id)
                task.title = new_title
                task.save()
    return redirect("board")


# Drag and drop

@require_POST
def move_task(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        task_id = int(data["task_id"])
        to_column_id = int(data["to_column_id"])
        to_index_0 = int(data["to_index"])  # 0-based
    except Exception:
        return HttpResponseBadRequest("Bad payload")

    with transaction.atomic():
        task = get_object_or_404(Task.objects.select_for_update(), pk=task_id)

        old_col_id = task.column_id
        old_pos = task.position
        new_col_id = to_column_id
        new_pos = max(1, to_index_0 + 1)  # 1-based

        if new_col_id == old_col_id:
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

            count_in_target = Task.objects.filter(column_id=new_col_id).count()
            new_pos = min(max(1, new_pos), count_in_target + 1)

            Task.objects.filter(column_id=new_col_id, position__gte=new_pos).update(
                position=models.F("position") + 1
            )

            task.column_id = new_col_id
            task.position = new_pos
            task.updated_at = now()
            task.save(update_fields=["column", "position", "updated_at"])

    return JsonResponse({"ok": True})
