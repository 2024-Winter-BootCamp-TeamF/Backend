from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from .bots import translate_bot

class TranslateAPIView(APIView):
    def post(self, request):
        data = request.data
        message = data.get('message', '')
        translated_message = translate_bot(message)
        return Response({"translated_message": translated_message})
