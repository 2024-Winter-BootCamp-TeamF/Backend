import redis
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView
from temp.openaiService import ask_openai  # OpenAI API 호출 함수
from .models import Question, UserAnswer
from rest_framework import status

# Redis 연결 설정
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

class TopicsAndQuestionsRAGView(APIView):
    """
    검색 증강 생성(RAG)을 사용하여 PDF 페이지에서 주제를 추출하고 문제를 생성하는 API
    """

    def get(self, request, file_id, page_number):
        try:
            if not file_id or not page_number:
                return Response({"error": "file_id and page_number are required."}, status=400)

            # Redis에서 해당 페이지 데이터 가져오기
            redis_key = f"pdf:{file_id}:page:{page_number}"
            page_data = redis_client.get(redis_key)
            if not page_data:
                return Response({"error": "Page not found in Redis."}, status=404)

            # JSON 문자열을 Python dict로 변환
            page_content = json.loads(page_data)

            # 텍스트 필드 확인 및 추출
            text_field = page_content.get("text")
            if isinstance(text_field, dict):
                text = json.dumps(text_field)  # dict를 문자열로 변환
            elif isinstance(text_field, str):
                text = text_field.strip()
            else:
                return Response({"error": "Invalid text field format."}, status=400)

            if not text:
                return Response({"error": "Page content is empty."}, status=400)

            # OpenAI API를 사용하여 주제 추출
            topic_prompt = (
                "다음 텍스트는 PDF 문서의 일부입니다. "
                "텍스트의 주요 주제 또는 핵심 키워드를 3~5개로 요약해 주세요. "
                "가장 중요한 주제를 맨 첫 번째에 배치해 주세요. "
                "챕터와 같은 단을 뜻하는 단어는 제외해 주세요. "
                "간단하고 명확한 키워드만 반환하세요.\n\n"
                f"텍스트: {text}"
            )
            topic_result = ask_openai(topic_prompt, max_tokens=100)

            if not topic_result["success"]:
                return Response({"error": f"OpenAI API error during topic extraction: {topic_result['error']}"}, status=500)

            # 추출된 주제
            topics = topic_result["response"]

            if not topics:
                return Response({"error": "No topics extracted from the text."}, status=400)

            # 주제를 기반으로 Redis에서 연관 데이터 검색
            related_contexts = []
            for topic in topics.split(', '):  # 추출된 주제마다 검색 수행
                search_key_pattern = f"*{topic}*"
                for key in redis_client.scan_iter(search_key_pattern):
                    data = redis_client.get(key)
                    if data:
                        related_contexts.append(json.loads(data).get("text", ""))

            # 연관 데이터를 하나의 컨텍스트로 결합
            related_context = "\n".join([ctx.strip() for ctx in related_contexts if ctx])

            # 문제 생성을 위한 OpenAI API 호출
            question_prompt = (
                "다음은 주요 주제와 관련된 텍스트입니다. 주제를 기반으로 객관식 문제 6개, 서술형 문제 4개 만들어 주세요. "
                "문제는 한국어로 내고, 주제와 관련된 설명은 하지 마세요. "
                "모든 문제는 JSON 배열 형식으로 반환해 주세요. 각 문제는 아래와 같은 형식을 따라야 합니다:\n\n"
                "{\n"
                "  'type': '객관식', '주관식',\n"
                "  'question': '문제 내용',\n"
                "  'choices': ['선택지 1', '선택지 2', '선택지 3', '선택지 4', '선택지 5'] (객관식만),\n"
                "  'answer': '정답'\n"
                "}\n\n"
                f"주제 목록: {topics}\n\n"
                f"관련 텍스트: {related_context}"
            )

            question_result = ask_openai(question_prompt, max_tokens=4096)

            questions = json.loads(question_result['response'])

            # 문제 저장
            for question_data in questions:
                Question.objects.create(
                    question_type=question_data['type'],
                    question_text=question_data['question'],
                    choices=question_data.get('choices'),
                    answer=question_data['answer']
                )

            return Response({
                "topics": topics,
                "questions": questions  # 클라이언트에 문제 반환
            })

        except redis.exceptions.RedisError as e:
            return Response({"error": f"Redis error: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"}, status=500)


class SubmitAnswerAPIView(APIView):
    """
    사용자가 문제에 대한 답안을 제출하고, 정답 여부를 확인한 후 결과를 저장하는 API
    """

    def get(self, request, question_id, user_answer):
        try:

            if not question_id or not user_answer:
                return Response({"error": "question_id and user_answer are required."}, status=status.HTTP_400_BAD_REQUEST)

            # 문제 찾기
            question = Question.objects.filter(id=question_id).first()
            if not question:
                return Response({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

            # 정답 확인
            correct_answer = question.answer
            is_correct = user_answer == correct_answer

            # 사용자 답안 저장
            UserAnswer.objects.create(
                question=question,
                user_answer=user_answer,
                is_correct=is_correct
            )

            # 결과 반환
            return Response({
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
