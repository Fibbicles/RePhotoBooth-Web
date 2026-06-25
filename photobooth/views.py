"""
Views for the photobooth app.

These views implement the core capture flow.  Guests select an event,
start the booth, capture photos and view their results.  Photos are
associated with events and saved to the database.
"""

import base64
import os
import uuid
from typing import Optional

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
try:
    import cups  # type: ignore
except ImportError:  # pragma: no cover – optional dependency
    cups = None

from .models import Event, Photo, Booth


def index(request: HttpRequest) -> HttpResponse:
    """List active events and prompt the user to choose one.

    If only one active event exists, redirect directly to the event's
    capture page.  Otherwise a simple list of events is rendered.
    """
    events = Event.objects.filter(active=True).order_by("name")
    if events.count() == 1:
        return redirect('photobooth-capture', slug=events.first().slug)
    return render(request, 'photobooth/event_list.html', {"events": events})


def capture(request: HttpRequest, slug: str) -> HttpResponse:
    """Render the capture page for a given event.

    The event slug identifies which branding assets to load.  The
    template uses JavaScript to access the camera and handle the capture
    flow.  A CSRF token is provided automatically by Django when using
    POST forms (the JS fetch request includes the CSRF token header).
    """
    event = get_object_or_404(Event, slug=slug, active=True)
    return render(request, 'photobooth/booth.html', {"event": event})


@require_http_methods(["POST"])
@csrf_exempt  # The fetch request may not send CSRF tokens; consider using a token in production
def save_photo(request: HttpRequest, slug: str) -> JsonResponse:
    """Save a captured photo for the given event.

    Expects a base64 data URL in the ``image`` POST parameter.  Creates a
    ``Photo`` instance and stores the uploaded image.  Returns JSON with
    a success flag and a URL where the guest can view their photo.
    """
    image_data = request.POST.get("image")
    if not image_data:
        return JsonResponse({"error": "No image provided"}, status=400)
    # decode base64 data URL
    try:
        header, encoded = image_data.split(",", 1)
    except ValueError:
        return JsonResponse({"error": "Invalid image data"}, status=400)
    try:
        image_bytes = base64.b64decode(encoded)
    except Exception:
        return JsonResponse({"error": "Could not decode image"}, status=400)
    event = get_object_or_404(Event, slug=slug, active=True)
    # Determine booth if provided via header (future expansion)
    booth_identifier = request.headers.get('X-Booth-Identifier')
    booth: Optional[Booth] = None
    if booth_identifier:
        try:
            booth_uuid = uuid.UUID(booth_identifier)
            booth = Booth.objects.filter(identifier=booth_uuid).first()
        except ValueError:
            booth = None
    # Save Photo object
    photo = Photo(event=event, booth=booth)
    # Generate a temporary filename – the Photo model's upload_to function uses the guid
    filename = f"{photo.guid}.jpg"
    photo.image.save(filename, content=ContentFile(image_bytes), save=False)
    photo.save()
    # Optionally generate QR code
    try:
        photo.generate_qr_code()
    except Exception:
        pass
    return JsonResponse({
        "success": True,
        "photo_url": request.build_absolute_uri(photo.get_absolute_url()),
        "guid": str(photo.guid),
    })


def photo_detail(request: HttpRequest, guid: uuid.UUID) -> HttpResponse:
    """Display a single photo.

    If the photo does not exist, a 404 is raised.  This view could be
    extended to include social sharing buttons, download links or a
    QR code display.
    """
    photo = get_object_or_404(Photo, guid=guid)
    return render(request, 'photobooth/photo_detail.html', {"photo": photo})


@require_http_methods(["POST"])
@csrf_exempt  # The photo detail page uses fetch to post email without CSRF token
def send_photo_email(request: HttpRequest, guid: uuid.UUID) -> JsonResponse:
    """Accept an email address and send the photo to the user.

    Updates the ``email`` field on the ``Photo`` instance and sends an
    email with the photo attached.  A JSON response indicates success
    or failure.  Errors are returned with appropriate status codes.
    """
    email = request.POST.get("email")
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)
    photo = get_object_or_404(Photo, guid=guid)
    # Update email on the Photo record
    photo.email = email
    photo.save(update_fields=["email"])
    # Compose the email
    subject = f"Your photo from {photo.event.name if photo.event else 'Re‑Photo Booth'}"
    body = """Thank you for using the Re‑Photo Booth! Your photo is attached and can also be downloaded via the link below.

Download link: {url}

Enjoy your memories!""".format(url=request.build_absolute_uri(photo.get_absolute_url()))
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
        to=[email],
    )
    # Attach the photo file
    try:
        if photo.image and photo.image.path:
            message.attach_file(photo.image.path)
    except Exception:
        pass
    # Send the email.  Fail silently to avoid raising if SMTP is misconfigured.
    try:
        message.send(fail_silently=True)
    except Exception:
        return JsonResponse({"error": "Failed to send email"}, status=500)
    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@csrf_exempt
def print_photo(request: HttpRequest, guid: uuid.UUID) -> JsonResponse:
    """Send a print job for the specified photo.

    If CUPS support is available and a printer is configured, the photo
    will be sent to the printer.  Otherwise an error response is
    returned.  The name of the printer can be specified via the
    ``PHOTOBOOTH_PRINTER`` environment variable or the Django setting
    ``PHOTOBOOTH_PRINTER``.  This route is protected by staff_member
    permissions on the front‑end; CSRF is exempted to allow fetch
    requests.
    """
    if cups is None:
        return JsonResponse({"error": "Printing not supported"}, status=501)
    photo = get_object_or_404(Photo, guid=guid)
    printer_name = getattr(settings, 'PHOTOBOOTH_PRINTER', None) or os.environ.get('PHOTOBOOTH_PRINTER')
    if not printer_name:
        return JsonResponse({"error": "No printer configured"}, status=500)
    try:
        conn = cups.Connection()
        # Ensure the file is saved to disk
        file_path = photo.image.path
        job_id = conn.printFile(printer_name, file_path, f"Photo {photo.guid}", {})
    except Exception as exc:
        return JsonResponse({"error": f"Failed to print: {exc}"}, status=500)
    return JsonResponse({"success": True})


from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count

@staff_member_required
def gallery(request: HttpRequest, slug: str) -> HttpResponse:
    """Display a gallery of photos for a given event.

    Staff users can browse all photos associated with an event.  A simple
    search box filters by email (if provided).  Thumbnails link to the
    detailed view.  Bulk deletion/export functionality could be added in
    the future.
    """
    event = get_object_or_404(Event, slug=slug)
    photos = event.photos.all()
    query = request.GET.get("q")
    if query:
        photos = photos.filter(email__icontains=query)
    return render(request, 'photobooth/gallery.html', {
        "event": event,
        "photos": photos,
        "query": query or "",
    })


@staff_member_required
def analytics(request: HttpRequest) -> HttpResponse:
    """Display simple analytics about events and photos.

    The analytics dashboard shows the total number of photos taken,
    active events and the top events by photo count.  Future
    enhancements could include charts and per‑booth statistics.
    """
    total_photos = Photo.objects.count()
    total_events = Event.objects.filter(active=True).count()
    top_events = (
        Event.objects.annotate(num_photos=Count('photos'))
        .filter(num_photos__gt=0)
        .order_by('-num_photos')[:5]
    )
    return render(request, 'photobooth/analytics.html', {
        'total_photos': total_photos,
        'total_events': total_events,
        'top_events': top_events,
    })