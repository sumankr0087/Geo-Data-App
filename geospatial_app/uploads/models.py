from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    file_type = models.CharField(
        max_length=50,
        choices=[("GeoJSON", "GeoJSON"), ("KML", "KML"), ("TIFF", "TIFF")]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.file_type})"
