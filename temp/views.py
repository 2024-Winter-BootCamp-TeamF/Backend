from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response

def hello_view(request):
    return JsonResponse({"message": "hello"})