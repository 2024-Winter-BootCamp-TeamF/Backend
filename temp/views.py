from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, viewsets
from .models import Item  # 모델 임포트
from .serializers import ItemSerializer  # 정의한 ItemSerializer import

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

# 모델에 대한 Serializer 작성
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'title', 'description']

# CRUD 기능을 위한 ViewSet 작성
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all() # Item 모델의 모든 객체를 쿼리셋으로 사용
    serializer_class = ItemSerializer # ItemSerializer를 사용
