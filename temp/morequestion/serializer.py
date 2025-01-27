from rest_framework import serializers
from .models import MoreUserAnswer, MoreQuestion

class WrongAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text')  # 질문 텍스트
    choices = serializers.JSONField(source='question.choices', required=False)  # 객관식 선택지
    correct_answer = serializers.CharField(source='question.answer')  # 정답 추가

    class Meta:
        model = MoreUserAnswer
        fields = ['id', 'question_text', 'choices', 'user_answer', 'correct_answer', 'is_correct', 'explanation']

class AllQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoreQuestion
        fields = ['id', 'question_type', 'question_topic', 'question_text', 'choices', 'answer', 'is_answer', 'created_at']
