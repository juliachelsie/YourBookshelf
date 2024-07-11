from django.shortcuts import render


def index(request):
    """ A view to return index.html """
    return render(request, 'home/index.html')
