import os
import uuid
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def tinymce_image_upload(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file"}, status=400)

    upload = request.FILES["file"]
    filename = f"{uuid.uuid4()}_{upload.name}"

    upload_path = os.path.join(settings.MEDIA_ROOT, "uploads", filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)

    with open(upload_path, "wb+") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    file_url = f"{settings.MEDIA_URL}uploads/{filename}"

    return JsonResponse({"location": file_url})
