from rest_framework import serializers

class SummaryRequestSerializer(serializers.Serializer):
    text = serializers.CharField()  # 요약할 텍스트
    user_id = serializers.IntegerField()  # 사용자 ID
    topic = serializers.CharField()  # 요약 주제
