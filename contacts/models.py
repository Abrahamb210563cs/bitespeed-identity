from django.db import models

class Contact(models.Model):
    email = models.EmailField(null=True, blank=True)
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    linkedId = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='secondary_contacts')
    linkPrecedence = models.CharField(max_length=10, choices=[('primary', 'Primary'), ('secondary', 'Secondary')], default='primary')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    deletedAt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} / {self.phoneNumber} ({self.linkPrecedence})"
