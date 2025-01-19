"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # temp 앱의 기본 API
    path('api/', include('temp.urls')),

    # temp.pdf 관련 API, test 디렉터리와 url이 같아 뒤에 /pdf 추가
    path('api/pdf/', include('temp.pdf.urls')),

    # Swagger UI
    path('docs/', include('swagger.urls')),

    # User
    path('api/user/', include('user.urls')),

    path("api/pinecone/", include("temp.pinecone.urls")),
  
    # 문제
    path('api/question/', include('temp.question.urls')),
  
    path('api/langchain/', include('temp.langchain.urls')), 
  
    path('', include('django_prometheus.urls')),

]
