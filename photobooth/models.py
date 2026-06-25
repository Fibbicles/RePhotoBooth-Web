"""
Models for the photobooth application.

This module defines the core data structures used by the Re‑Photo Booth
platform.  Photos are associated with events and booths, and the event
controls visual branding.  Themes allow reuse of colour palettes and fonts
across multiple events.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse

try:
    # Optional import of segno for generating QR codes.  If not available,
    # photos can still be stored but QR codes will not be generated.  A
    # future migration can add a dependency when installed.
    import segno
except ImportError:  # pragma: no cover – optional dependency
    segno = None  # type: ignore


class Theme(models.Model):
    """Defines a collection of visual properties for events.

    Themes help ensure consistent styling across different events.  Colours
    should be provided as hexadecimal strings (e.g., ``#ff0000``).  The
    ``font_family`` field should contain a CSS font family declaration.
    """

    name = models.CharField(max_length=50, unique=True)
    primary_color = models.CharField(max_length=7, default="#FFFFFF")
    secondary_color = models.CharField(max_length=7, default="#000000")
    font_family = models.CharField(max_length=100, default="system-ui, sans-serif")

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    """Represents a photobooth event.

    Events encapsulate branding and configuration.  Each event can have
    associated assets such as a logo, background image and frame overlay.
    The ``active`` flag allows organisers to enable or disable events
    without deleting them.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="events/logos/", blank=True, null=True)
    background_image = models.ImageField(upload_to="events/backgrounds/", blank=True, null=True)
    overlay_frame = models.ImageField(upload_to="events/overlays/", blank=True, null=True)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional sponsorship and marketing consent
    sponsor_logo = models.ImageField(upload_to="events/sponsors/", blank=True, null=True)
    requires_consent = models.BooleanField(default=False)
    consent_text = models.CharField(
        max_length=200,
        blank=True,
        default="I consent to the use of my image for marketing purposes."
    )

    def __str__(self) -> str:
        return self.name


class Booth(models.Model):
    """Represents a deployed photobooth device.

    Each booth has a unique identifier used to authenticate API requests.
    Configuration such as location and per‑booth settings are stored in
    the ``config`` JSON field.  ``last_seen`` records the last time the
    booth communicated with the server.
    """

    identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    config = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


def photo_upload_to(instance: "Photo", filename: str) -> str:
    """Compute upload path for photo images.

    Images are stored under ``photos/<event_slug>/<yyyymmdd>/<uuid>.jpg``.
    """
    event_slug = instance.event.slug if instance.event else "unknown"
    date_str = instance.created_at.strftime("%Y%m%d") if instance.created_at else datetime.now().strftime("%Y%m%d")
    ext = Path(filename).suffix or ".jpg"
    return f"photos/{event_slug}/{date_str}/{instance.guid}{ext}"


class Photo(models.Model):
    """Captured photo associated with an event and booth.

    The raw image is stored in the ``image`` field.  The optional
    ``qr_code`` field holds a generated QR code image pointing to
    ``get_absolute_url()``.  If the application cannot generate a QR
    code (e.g., missing dependency), this field can remain blank.
    """

    guid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="photos")
    booth = models.ForeignKey(Booth, on_delete=models.SET_NULL, null=True, blank=True, related_name="photos")
    image = models.ImageField(upload_to=photo_upload_to)
    qr_code = models.ImageField(upload_to="photos/qr/", blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Photo {self.guid}"

    def get_absolute_url(self) -> str:
        """Return the URL where the photo can be downloaded or viewed."""
        return reverse("photo-detail", args=[str(self.guid)])

    def generate_qr_code(self, force: bool = False) -> None:
        """Generate and store a QR code image for this photo.

        If a QR code is already present and ``force`` is False, the method
        returns immediately.  The QR code encodes the absolute URL of the
        photo (as provided by ``get_absolute_url``).  Requires the
        ``segno`` library.
        """
        if self.qr_code and not force:
            return
        if segno is None:
            return
        uri = self.get_absolute_url()
        qr = segno.make(uri, error='h')
        buffer = bytearray()
        qr.save(buffer, kind='png', scale=4)  # type: ignore[attr-defined]
        filename = f"{self.guid}.png"
        self.qr_code.save(filename, ContentFile(buffer), save=False)
        self.save(update_fields=["qr_code"])