from django.urls import path
from .views import UploadAllToPineconeView, ListAllIndexesView, ListIDsInIndexView, FetchDataByIDView

urlpatterns = [
    path("upload/", UploadAllToPineconeView.as_view(), name="upload-to-pinecone"),
    # 인덱스 목록 조회
    path("list-all-indexes/", ListAllIndexesView.as_view(), name="list-all-indexes"),
    # 특정 인덱스의 모든 ID 조회
    path("list-ids-in-index/{index_name}/", ListIDsInIndexView.as_view(), name="list-ids-in-index"),
    # 특정 ID로 데이터 조회
    path("fetch-data-by-id/{index_name}/{doc_id}/", FetchDataByIDView.as_view(), name="fetch-data-by-id"),
]
