import os
from http.client import responses
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView
from temp.openaiService import ask_openai, get_embedding  # OpenAI API 호출 함수
from .models import Question, UserAnswer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from temp.pinecone.service import get_pinecone_instance, get_pinecone_index
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class TopicsAndQuestionsRAGView(APIView):
    """
    검색 증강 생성(RAG)을 사용하여 파인콘에서 주제를 추출하고 문제를 생성하는 API
    """
    permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능

    @swagger_auto_schema(
        operation_description="검색 증강 생성(RAG)을 사용하여 파인콘에서 주제를 가져오고 문제를 생성하는 API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "topics": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of topics to summarize (e.g., ['machine learning', 'data science']).",
                )
            },
            required=["topics"],
        ),
        responses={
            400: openapi.Response(description="Topics are required."),
            500: openapi.Response(description="Internal server error."),
        },
    )
    def post(self, request):
        try:
            # 요청 본문에서 topics 가져오기
            topics = request.data.get("topics")
            if not topics or not isinstance(topics, list):
                return Response({
                    "error": "Topics are required and must be a list."
                }, status=status.HTTP_400_BAD_REQUEST)

            pinecone_instance = get_pinecone_instance()
            pinecone_index = get_pinecone_index(pinecone_instance, os.getenv("PINECONE_INDEX_NAME"))

            # 주제를 기반으로 Pinecone에서 연관 데이터 검색
            related_contexts = []
            for topic in topics:
                # Pinecone에서 검색 수행
                query_result = pinecone_index.query(
                    namespace="default",
                    top_k=10,
                    include_metadata=True,
                    vector=get_embedding(topic)  # 토픽에 대한 벡터 생성
                )
                for match in query_result.get("matches", []):
                    related_contexts.append(match["metadata"].get("text", ""))

            # 연관 데이터를 하나의 컨텍스트로 결합
            related_context = "\n".join([ctx.strip() for ctx in related_contexts if ctx])

            # 객관식 생성 위한 OpenAI API 호출
            multiple_choice_prompt = (
                "다음은 여러 주제와 관련된 텍스트입니다. 주제를 기반으로 객관식 문제 7개를 생성해 주세요.\n"
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
                "주의사항:\n"
                "- JSON 배열 형식만 반환하세요.\n"
                "- 각 문제는 텍스트에 포함된 정보만 바탕으로 생성하세요.\n"
                "- JSON 외의 다른 텍스트는 절대 포함하지 마세요.\n\n"
                f"주제 목록: {', '.join(topics)}\n\n"
                f"관련 텍스트: {related_context}\n"
            )

            multiple_choice_result = ask_openai(multiple_choice_prompt, max_tokens=4096)

            # API 응답이 JSON 배열 형식으로 오도록 설정했으므로 바로 파싱
            multiple_choices = json.loads(multiple_choice_result['response'])

            # 확인용 로그
            print("Parsed questions:", multiple_choices)

            # 딕셔너리 형식이 아닌 경우 예외 처리
            if not isinstance(multiple_choices, list):
                raise ValueError("API response is not a valid JSON array.")

            # 데이터 저장
            for multiple_choice_data in multiple_choices:
                Question.objects.create(
                    question_type=multiple_choice_data['type'],
                    question_topic=multiple_choice_data['topic'],
                    question_text=multiple_choice_data['question'],
                    choices=multiple_choice_data.get('choices'),
                    answer=multiple_choice_data['answer']
                )

            # 주관식
            subjective_prompt = (
                "다음은 여러 주제와 관련된 텍스트입니다. 주제를 기반으로 주관식 문제 3개를 생성해 주세요.\n"
                "문제는 한국어로 작성되고, 각 문제에 대해 한 개의 답을 포함해야 합니다.\n"
                "문제 형식은 다음 JSON 배열로 반환해야 합니다:\n\n"
                "[\n"
                "  {\n"
                "    \"type\": \"주관식\",\n"
                "    \"topic\": \"주제\",\n"
                "    \"question\": \"문제 내용\",\n"
                "    \"answer\": \"정답\"\n"
                "  },\n"
                "  ...\n"
                "]\n\n"
                "주의사항:\n"
                "- JSON 배열 형식만 반환하세요.\n"
                "- 각 문제는 텍스트에 포함된 정보만 바탕으로 생성하세요.\n"
                "- JSON 외의 다른 텍스트는 절대 포함하지 마세요.\n\n"
                f"주제 목록: {', '.join(topics)}\n\n"
                f"관련 텍스트: {related_context}\n"
            )

            subjective_result = ask_openai(subjective_prompt, max_tokens=4096)

            # API 응답이 JSON 배열 형식으로 오도록 설정했으므로 바로 파싱
            subjectives = json.loads(subjective_result['response'])

            # 확인용 로그
            print("Parsed questions:", subjectives)

            # 딕셔너리 형식이 아닌 경우 예외 처리
            if not isinstance(subjectives, list):
                raise ValueError("API response is not a valid JSON array.")

            # 데이터 저장
            for subjective_data in subjectives:
                Question.objects.create(
                    question_type=subjective_data['type'],
                    question_topic=subjective_data['topic'],
                    question_text=subjective_data['question'],
                    answer=subjective_data['answer']
                )

            return Response({
                "topics": topics,
                "multiple_choices": multiple_choices,  # 클라이언트에 객관식 반환
                "subjectives": subjectives  # 클라이언트에 주관식 반환
            })

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"}, status=500)


class SubmitAnswerAPIView(APIView):
    """
    사용자가 문제에 대한 답안을 제출하고, 정답 여부를 확인한 후 결과를 저장하는 API
    """

    permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능

    @swagger_auto_schema(
        operation_description="사용자가 문제에 대한 답안을 제출하고, 정답 여부를 확인한 후 결과를 저장하는 API",
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
            question = Question.objects.filter(id=question_id).first()
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

            # 사용자 답안 저장
            UserAnswer.objects.create(
                question=question,
                user_answer=user_answer,
                is_correct=is_correct
            )

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

            # 결과 반환
            return Response({
                "question_id": question_id,
                "question_type": question.question_type,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation if not is_correct else None  # 틀렸을 때만 해설 제공
            })

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                Question.objects.create(
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