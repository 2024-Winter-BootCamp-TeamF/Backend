from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Item

def hello_view(request):
    return JsonResponse({"message": "hello"})

# Create
def item_create(request):
    if request.method == "POST":
        title = request.POST.get['title']
        description = request.POST.get['description']
        Item.objects.create(title=title, description=description)
        return redirect('item_list')
    return render(request, 'temp/item_form.html')

# Read (전체 조회)
def item_list(request):
    items = Item.objects.all()
    return render(request, 'temp/item_list.html', {'items': items})

# Update
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        item.title = request.POST['title']
        item.description = request.POST['description']
        item.save()
        return redirect('item_list')
    return render(request, 'temp/item_form.html', {'item': item})

# Delete
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect('item_list')
    return render(request, 'temp/item_form.html', {'item': item})
