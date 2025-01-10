from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .openaiService import ask_openai

def hello_view(request):
    return JsonResponse({"message": "hello"})

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class OpenAIView(APIView):
    @swagger_auto_schema(
        operation_description="Send a prompt to OpenAI and get a response",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'prompt': openapi.Schema(type=openapi.TYPE_STRING, description='User input prompt'),
            },
            required=['prompt']
        ),
        responses={
            200: openapi.Response(description="Successful response", examples={"application/json": {"response": "Your response"}}),
            400: openapi.Response(description="Bad Request"),
            500: openapi.Response(description="Internal Server Error"),
        }
    )
    def post(self, request):
        prompt = request.data.get("prompt")
        if not prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        openai_response = ask_openai(prompt)
        if openai_response.get("success"):
            return Response({"response": openai_response["response"]}, status=status.HTTP_200_OK)
        else:
            return Response({"error": openai_response["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
