"""
Admin configuration for the photobooth app.

Registers core models with the Django admin site so administrators can
create and manage events, themes, booths and photos.  Customisations such
as list display and search fields help improve the usability of the admin.
"""

from django.contrib import admin

from .models import Theme, Event, Booth, Photo


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    """Admin interface for themes."""

    list_display = ("name", "primary_color", "secondary_color", "font_family")
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for events."""

    list_display = ("name", "slug", "active", "created_at", "requires_consent")
    list_filter = ("active", "theme")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    """Admin interface for booths."""

    list_display = ("name", "identifier", "location", "event", "active", "last_seen")
    list_filter = ("active", "event")
    search_fields = ("name", "identifier", "location")


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface for photos."""

    list_display = ("guid", "event", "booth", "email", "created_at")
    list_filter = ("event", "booth")
    search_fields = ("guid", "email")

    actions = ["export_as_csv", "export_as_zip"]

    def export_as_csv(self, request, queryset):
        """Export selected photos metadata as a CSV file."""
        import csv
        from django.http import HttpResponse
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="photos.csv"'
        writer = csv.writer(response)
        writer.writerow(["guid", "event", "booth", "email", "created_at", "image_url"])
        for photo in queryset:
            writer.writerow([
                str(photo.guid),
                photo.event.name if photo.event else '',
                photo.booth.name if photo.booth else '',
                photo.email or '',
                photo.created_at.isoformat(),
                photo.image.url,
            ])
        return response
    export_as_csv.short_description = "Export selected photos as CSV"

    def export_as_zip(self, request, queryset):
        """Export selected photos as a ZIP archive."""
        import io
        import zipfile
        from django.http import HttpResponse
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zipf:
            for photo in queryset:
                if photo.image and photo.image.path:
                    file_path = photo.image.path
                    file_name = file_path.split('/')[-1]
                    try:
                        with open(file_path, 'rb') as f:
                            zipf.writestr(file_name, f.read())
                    except Exception:
                        continue
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="photos.zip"'
        return response
    export_as_zip.short_description = "Export selected photos as ZIP"