"""
URL configuration for rephotobooth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Root URL configuration for the Re‑Photo Booth project.  The photobooth app
# handles nearly all user‑facing routes.  The admin interface is available
# under the /admin/ prefix.  During development we also serve media files
# directly from the filesystem.
urlpatterns = [
    # Frontend photobooth application
    path('admin/', admin.site.urls),
    path("", include("photobooth.urls")),
    # Django admin for managing events, themes, booths and photos
]

# In development only, serve uploaded media and static files directly.  In
# production these should be served by the web server (e.g., nginx).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
