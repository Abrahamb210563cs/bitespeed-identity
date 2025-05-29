from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phoneNumber', 'linkPrecedence', 'linkedId', 'createdAt')
    list_filter = ('linkPrecedence',)
    search_fields = ('email', 'phoneNumber')
