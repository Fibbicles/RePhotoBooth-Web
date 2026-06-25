"""
URL configuration for rephotobooth project photobooth app.

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
"""
URL configuration for the photobooth app.

This module defines the routing for the core photobooth flows.  Guests start
at the index page which lists available events.  Each event has a slug which
is used to load its capture page.  Photos are identified by their GUIDs.
"""
from django.urls import path

from . import views

# The main routes for the photobooth application.  The index page shows
# active events.  A capture session is started using the event slug.  When a
# photo is saved it is redirected to the photo detail page by its GUID.
urlpatterns = [
    # List active events or redirect if only one
    path("", views.index, name="photobooth-index"),
    # Capture page for a specific event
    path("<slug:slug>/", views.capture, name="photobooth-capture"),
    # Save a captured image via POST; slug identifies the event
    path("<slug:slug>/save/", views.save_photo, name="photobooth-save"),
    # Display a saved photo by GUID
    path("photo/<uuid:guid>/", views.photo_detail, name="photo-detail"),
    # Send photo via email
    path("photo/<uuid:guid>/email/", views.send_photo_email, name="photo-email"),
    # Print a photo
    path("photo/<uuid:guid>/print/", views.print_photo, name="photo-print"),
    # Gallery for staff to browse event photos
    path("<slug:slug>/gallery/", views.gallery, name="photobooth-gallery"),
    # Analytics dashboard
    path("analytics/", views.analytics, name="photobooth-analytics"),
]
