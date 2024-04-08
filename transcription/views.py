from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os, json
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

from .models import Transcription
from .serializers import TranscriptionSerializer
from .utils import get_file_url, get_result_url, get_transcription_text




class TranscriptionView(APIView):
    def get(self, request, pk):
        try:
            transcription = Transcription.objects.get(pk=pk)
            serializer = TranscriptionSerializer(transcription)
            transcription_data = serializer.data
            data = {
                "id": transcription_data["id"],
                "file": transcription_data["file"],
                "file_url": transcription_data["file_url"],
                "full_transcript": transcription_data["transcription_text"]['transcription']['full_transcript'],
                "transcript_time": transcription_data.get('sync_map').get('fragments'),
                "created_at": transcription_data["created_at"],
                "updated_at": transcription_data["updated_at"],
            }
            return Response(data, status=status.HTTP_200_OK)
        except Transcription.DoesNotExist:
            transcription = None
            return Response({"error": "Transcription not found"}, status=status.HTTP_404_NOT_FOUND)


class ProcessFileView(APIView):
    def post(self, request, *args, **kwargs):
        files = request.FILES

        file = files.get('file')
        if not file:
            return Response({"error": "File is missing!"}, status = status.HTTP_400_BAD_REQUEST)
        
        file_url = get_file_url(file, file.name)
        if not file_url:
            return Response({"error": "Failed to generate File url"}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        result_url = get_result_url(file_url)
        if not result_url:
            return Response({"error": "Failed to generate Result url"}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        transcription_text = get_transcription_text(result_url)
        if not transcription_text:
            return Response({"error": "Failed to generate Transcription text"}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        transcription_serializer = TranscriptionSerializer(
            data={
                'file':file, 
                'file_url': file_url,
                'result_url': result_url,
                'transcription_text': transcription_text
            }
        )
        if transcription_serializer.is_valid():
            transcription = transcription_serializer.save()
            config_string = u"task_language=eng|is_text_type=plain|os_task_file_format=json"
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = os.path.abspath(transcription.file.path)

            full_transcription = transcription.transcription_text["transcription"]["utterances"]
            transcription_file_path = os.path.join(settings.MEDIA_ROOT, 'transcriptions', f'{transcription.id}_transcription.txt')

            os.makedirs(os.path.dirname(transcription_file_path), exist_ok=True)

            with open(transcription_file_path, 'w') as file:
                for transcript in full_transcription:
                    file.write(transcript["text"] + '\n')

            task.text_file_path_absolute = os.path.abspath(transcription_file_path)
            task.sync_map_file_path_absolute = os.path.join(settings.MEDIA_ROOT, 'fragments', f"{transcription.id}_syncmap.json")
            ExecuteTask(task).execute()
            task.output_sync_map_file()

            fragment_file_path = os.path.join(settings.MEDIA_ROOT, 'fragments', f"{transcription.id}_syncmap.json")
            os.makedirs(os.path.dirname(fragment_file_path), exist_ok=True)

            with open(fragment_file_path, "r") as syncmap_file:
                syncmap_data = json.load(syncmap_file)

            transcription.sync_map = syncmap_data

            data = {
                "id": transcription_serializer.data['id'],
                "file": transcription_serializer.data['file'],
                "file_url": transcription_serializer.data['file_url'],
                "full_transcript": transcription_serializer.data['transcription_text']['transcription']['full_transcript'],
                "transcript_time": transcription_serializer.data['sync_map']['fragments'],
                "created_at": transcription_serializer.data['created_at'],
                "updated_at": transcription_serializer.data['updated_at'],
            }
            return Response(data, status=status.HTTP_200_OK) 
        
        return Response(transcription_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
