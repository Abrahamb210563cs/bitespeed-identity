from django.urls import path
from .views import identify_contact

urlpatterns = [
    path('', identify_contact, name='identify_contact'),  # ✅ fixed path
]
