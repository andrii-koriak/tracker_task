from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Column, Task


def about(request):
    return HttpResponse("<h7>Їбати за карпати</h7>")

def Skeb(request):
    return HttpResponse("<h5>Skebooob</h5>")
def board(request):
    columns = Column.objects.all().order_by('order')
    return render(request, 'trackers/dashboard.html', {'columns': columns})

def add_column(request):
    if request.method == 'POST':
        Column.objects.create(title=request.POST['title'])
    return redirect('board')

def add_task(request, column_id):
    if request.method == 'POST':
        column = get_object_or_404(Column, pk=column_id)
        Task.objects.create(column=column, title=request.POST['title'])
    return redirect('board')
