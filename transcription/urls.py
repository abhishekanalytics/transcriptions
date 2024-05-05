from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProcessFileView.as_view(), name='process_file'),
    path('<int:pk>/', views.TranscriptionView.as_view(), name='transcription')
]
