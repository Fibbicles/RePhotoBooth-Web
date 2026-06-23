# views.py
import base64
import uuid
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path


def photobooth(request):
    return render(request, "photobooth.html")


@csrf_exempt
def save_photo(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    image_data = request.POST.get("image")

    if not image_data:
        return JsonResponse({"error": "No image provided"}, status=400)

    header, encoded = image_data.split(",", 1)
    image_bytes = base64.b64decode(encoded)

    filename = f"{uuid.uuid4()}.png"
    save_dir = Path(settings.MEDIA_ROOT) / "photobooth"
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / filename
    file_path.write_bytes(image_bytes)

    return JsonResponse({
        "success": True,
        "file": f"{settings.MEDIA_URL}photobooth/{filename}"
    })