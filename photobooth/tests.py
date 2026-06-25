from django.test import TestCase, Client
from django.urls import reverse
from .models import Event, Photo
import base64
from PIL import Image
import io


class PhotoBoothTestCase(TestCase):
    """Basic tests for the photobooth workflow."""

    def setUp(self) -> None:
        self.client = Client()
        self.event = Event.objects.create(name="Test Event", slug="test-event")

    def _make_base64_image(self) -> str:
        """Create a small red JPEG image encoded as a data URL."""
        img = Image.new("RGB", (10, 10), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        data = base64.b64encode(buffer.getvalue()).decode()
        return "data:image/jpeg;base64," + data

    def test_index_redirects_or_lists(self) -> None:
        response = self.client.get("/")
        # If only one active event, we should redirect to its capture page.
        # Otherwise, we get a list of events.  In this test there is one event.
        if Event.objects.filter(active=True).count() == 1:
            self.assertEqual(response.status_code, 302)
        else:
            self.assertEqual(response.status_code, 200)

    def test_save_photo_creates_photo(self) -> None:
        image_data = self._make_base64_image()
        url = f"/{self.event.slug}/save/"
        response = self.client.post(url, {"image": image_data})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        # Ensure a Photo object was created
        self.assertEqual(Photo.objects.count(), 1)

# Create your tests here.
