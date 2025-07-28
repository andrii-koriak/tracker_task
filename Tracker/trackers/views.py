from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, '')


def about(request):
    return HttpResponse("<h7>Їбати за карпати</h7>")

def Skeb(request):
    return HttpResponse("<h5>Skebooob</h5>")