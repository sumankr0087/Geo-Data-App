from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import UploadedFile
from .serializers import UploadedFileSerializer

class FileUploadView(APIView):
    def post(self, request):
        # Handle the file and file type
        file = request.FILES.get("file")
        file_type = request.data.get("file_type")

        if not file or not file_type:
            return Response(
                {"error": "File and file_type are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the UploadedFile object
        uploaded_file = UploadedFile.objects.create(file=file, file_type=file_type)
        serializer = UploadedFileSerializer(uploaded_file)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FileListView(ListAPIView):
    serializer_class = UploadedFileSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return UploadedFile.objects.all()
