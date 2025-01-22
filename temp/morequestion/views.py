import os
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView
from temp.openaiService import ask_openai, get_embedding  # OpenAI API 호출 함수
from .models import MoreQuestion, MoreUserAnswer
from temp.question.models import Question
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from temp.pinecone.service import get_pinecone_instance, get_pinecone_index
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json

class RegenerateQuestionsAPIView(APIView):
    """
    사용자가 틀린 문제의 주제를 바탕으로 새로운 문제를 생성하는 API
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="틀린 문제의 주제를 바탕으로 새로운 문제를 생성하는 API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "incorrect_question_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of IDs of incorrectly answered questions.",
                )
            },
            required=["incorrect_question_ids"],
        ),
        responses={
            400: openapi.Response(description="Incorrect question IDs are required."),
            500: openapi.Response(description="Internal server error."),
        },
    )
    def post(self, request):
        try:

            # 요청 본문에서 틀린 문제 ID 가져오기
            incorrect_question_ids = request.data.get("incorrect_question_ids")
            if not incorrect_question_ids or not isinstance(incorrect_question_ids, list):
                return Response({
                    "error": "Incorrect question IDs are required and must be a list."
                }, status=status.HTTP_400_BAD_REQUEST)

            # 틀린 문제에서 주제 추출
            incorrect_questions = Question.objects.filter(id__in=incorrect_question_ids)
            if not incorrect_questions.exists():
                return Response({"error": "No questions found for the provided IDs."},
                                status=status.HTTP_404_NOT_FOUND)

            topics = list(set([q.question_topic for q in incorrect_questions if q.question_topic]))
            if not topics:
                return Response({"error": "No topics found in the provided questions."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 파인콘 인스턴스 및 인덱스 가져오기
            pinecone_instance = get_pinecone_instance()
            pinecone_index = get_pinecone_index(pinecone_instance, os.getenv("PINECONE_INDEX_NAME"))

            # 주제를 기반으로 Pinecone에서 연관 데이터 검색
            related_contexts = []
            for topic in topics:
                query_result = pinecone_index.query(
                    namespace="default",
                    top_k=10,
                    include_metadata=True,
                    vector=get_embedding(topic)
                )
                for match in query_result.get("matches", []):
                    related_contexts.append(match["metadata"].get("text", ""))

            # 연관 데이터를 하나의 컨텍스트로 결합
            related_context = "\n".join([ctx.strip() for ctx in related_contexts if ctx])

            # 객관식 문제 생성 프롬프트 작성
            multiple_choice_prompt = (
                "다음은 여러 주제와 관련된 텍스트입니다. 주제를 기반으로 객관식 문제 5개를 생성해 주세요.\n"
                "문제는 한국어로 작성되고, 각 문제에는 선택지 5개와 정답이 포함되어야 합니다.\n"
                "문제 형식은 다음 JSON 배열로 반환해야 합니다:\n\n"
                "[\n"
                "  {\n"
                "    \"type\": \"객관식\",\n"
                "    \"topic\": \"주제\",\n"
                "    \"question\": \"문제 내용\",\n"
                "    \"choices\": [\"선택지 1\", \"선택지 2\", \"선택지 3\", \"선택지 4\", \"선택지 5\"],\n"
                "    \"answer\": \"정답\"\n"
                "  },\n"
                "  ...\n"
                "]\n\n"
                f"주제 목록: {', '.join(topics)}\n\n"
                f"관련 텍스트: {related_context}\n"
            )

            multiple_choice_result = ask_openai(multiple_choice_prompt, max_tokens=4096)
            multiple_choices = json.loads(multiple_choice_result['response'])

            # 생성된 객관식 문제 저장
            for multiple_choice_data in multiple_choices:
               MoreQuestion.objects.create(
                    user=request.user,  # User 객체 전달
                    question_type=multiple_choice_data['type'],
                    question_topic=multiple_choice_data['topic'],
                    question_text=multiple_choice_data['question'],
                    choices=multiple_choice_data.get('choices'),
                    answer=multiple_choice_data['answer']
                )

            return Response({
                "topics": topics,
                "generated_multiple_choices": multiple_choices
            })

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubmitAnswerAPIView(APIView):
    """
    사용자가 문제에 대한 답안을 제출하고, 정답 여부를 확인한 후 결과를 저장하는 API(추가 문제용)
    """

    permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능

    @swagger_auto_schema(
        operation_description="사용자가 문제에 대한 답안을 제출하고, 정답 여부를 확인한 후 결과를 저장하는 API(추가 문제용)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "question_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="The ID of the question to answer."
                ),
                "user_answer": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The answer provided by the user."
                ),
            },
            required=["question_id", "user_answer"],
        ),
        responses={
            200: openapi.Response(
                description="The result of the answer submission.",
                examples={
                    "application/json": {
                        "question_id": 1,
                        "question_type": "객관식",
                        "user_answer": "사용자 답변",
                        "correct_answer": "정답",
                        "is_correct": True,
                        "explanation": "해설 내용 (틀렸을 경우 제공)"
                    }
                }
            ),
            400: openapi.Response(description="Invalid input, missing question_id or user_answer."),
            404: openapi.Response(description="Question not found."),
            500: openapi.Response(description="Internal server error."),
        },
    )
    def post(self, request):
        try:

            # 요청 본문에서 문제 id, 정답 가져오기
            question_id = request.data.get("question_id")
            user_answer = request.data.get("user_answer")

            # 필수 매개변수 확인
            if not question_id or not user_answer:
                return Response({"error": "question_id and user_answer are required."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 문제 찾기
            question = MoreQuestion.objects.filter(id=question_id).first()
            if not question:
                return Response({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

            # 문제 유형 확인
            if question.question_type == "객관식":
                # 객관식 문제 채점
                correct_answer = question.answer
                is_correct = user_answer == correct_answer

            elif question.question_type == "주관식":
                # 주관식 문제 채점 (프롬프팅 사용)
                correct_answer = question.answer

                # 프롬프트 생성
                grading_prompt = (
                    f"다음은 서술형 질문에 대한 사용자의 답변입니다. 답변이 정답과 의미적으로 얼마나 일치하는지 평가하고, "
                    f"\"True\" 또는 \"False\"로 반환하세요.\n\n"
                    f"질문: {question.question_text}\n"
                    f"정답: {correct_answer}\n"
                    f"사용자 답변: {user_answer}\n\n"
                    f"답변이 정답과 일치하는 경우 \"True\", 그렇지 않으면 \"False\"로만 답해주세요."
                )

                # OpenAI API 호출
                grading_result = ask_openai(grading_prompt, max_tokens=100)
                is_correct = grading_result.get("response", "").strip().lower() == "true"


            else:
                # 지원하지 않는 문제 유형
                return Response({"error": f"Unsupported question type: {question.question_type}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # 틀린 경우 해설 제공
            explanation = None
            if not is_correct:
                # 문제에 대한 해설을 생성하기 위한 프롬프트 작성
                explanation_prompt = (
                    f"다음은 문제에 대한 해설을 요청하는 문장입니다:\n\n"
                    f"문제: {question.question_text}\n"
                    f"정답: {correct_answer}\n\n"
                    "이 문제의 해설을 자세히 설명해주세요. 가능한 경우, 문제의 배경이나 풀이 방법을 포함해주세요."
                )
                # OpenAI API 호출하여 해설 받기
                explanation_result = ask_openai(explanation_prompt, max_tokens=1024)
                explanation = explanation_result.get("response", "해설을 생성할 수 없습니다.")

            # 사용자 답안 저장
            MoreUserAnswer.objects.create(
                user=request.user,  # User 객체 전달
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
                explanation=explanation
            )

            # 결과 반환
            return Response({
                "question_id": question_id,
                "question_type": question.question_type,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation
            })

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteMoreQuestionView(APIView):
    """
    사용자가 자신의 추가 질문(MoreQuestion)을 삭제하는 API
    """

    def delete(self, request, question_id):
        try:
            # 본인 소유의 MoreQuestion만 삭제 가능
            question = MoreQuestion.objects.get(id=question_id, user=request.user)
            question.delete()
            return Response({"message": "More question deleted successfully."}, status=status.HTTP_200_OK)
        except MoreQuestion.DoesNotExist:
            return Response({"error": "More question not found or not authorized to delete."}, status=status.HTTP_404_NOT_FOUND)


class DeleteUserAnswerView(APIView):
    """
    특정 사용자가 자신의 요약 데이터를 삭제하는 API
    """

    @swagger_auto_schema(
        operation_description="Delete a summary by ID if the user is authorized",
        responses={
            200: openapi.Response(description="Summary deleted successfully"),
            404: openapi.Response(description="Summary not found or not authorized to delete"),
        }
    )
    def delete(self, request, answer_id):
        try:
            # 본인 소유의 MoreUserAnswer 삭제 가능
            answer = MoreUserAnswer.objects.get(id=answer_id, user=request.user)
            answer.delete()
            return Response({"message": "User answer deleted successfully."}, status=status.HTTP_200_OK)
        except MoreUserAnswer.DoesNotExist:
            return Response({"error": "Answer not found or not authorized to delete."},
                            status=status.HTTP_404_NOT_FOUND)