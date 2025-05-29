# bitespeed/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def root_view(request):
    return HttpResponse("Welcome to Bitespeed API!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('identify/', include('contacts.urls')),  # your existing app routes
    path('', root_view),  # Add this line to handle root URL
]
