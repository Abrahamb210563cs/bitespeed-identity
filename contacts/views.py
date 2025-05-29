import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Contact

@csrf_exempt
def identify_contact(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    email = data.get('email')
    phoneNumber = data.get('phoneNumber')

    if not email and not phoneNumber:
        return HttpResponseBadRequest('At least email or phoneNumber must be provided')

    contacts = Contact.objects.filter(
        Q(email=email) | Q(phoneNumber=phoneNumber),
        deletedAt__isnull=True
    ).order_by('createdAt')

    if not contacts.exists():
        new_contact = Contact.objects.create(
            email=email,
            phoneNumber=phoneNumber,
            linkPrecedence='primary'
        )
        response = {
            "contact": {
                "primaryContactId": new_contact.id,
                "emails": [email] if email else [],
                "phoneNumbers": [phoneNumber] if phoneNumber else [],
                "secondaryContactIds": []
            }
        }
        return JsonResponse(response)

    primary_contact = contacts.filter(linkPrecedence='primary').first()
    if not primary_contact:
        primary_contact = contacts.order_by('createdAt').first()

    linked_contacts = Contact.objects.filter(
        Q(id=primary_contact.id) | Q(linkedId=primary_contact.id),
        deletedAt__isnull=True
    ).order_by('createdAt')

    emails = set()
    phoneNumbers = set()
    secondary_ids = []

    for c in linked_contacts:
        if c.email:
            emails.add(c.email)
        if c.phoneNumber:
            phoneNumbers.add(c.phoneNumber)
        if c.linkPrecedence == 'secondary':
            secondary_ids.append(c.id)

    new_email = email and email not in emails
    new_phone = phoneNumber and phoneNumber not in phoneNumbers

    if new_email or new_phone:
        Contact.objects.create(
            email=email if new_email else None,
            phoneNumber=phoneNumber if new_phone else None,
            linkedId=primary_contact,
            linkPrecedence='secondary'
        )
        linked_contacts = Contact.objects.filter(
            Q(id=primary_contact.id) | Q(linkedId=primary_contact.id),
            deletedAt__isnull=True
        ).order_by('createdAt')

        emails = set()
        phoneNumbers = set()
        secondary_ids = []
        for c in linked_contacts:
            if c.email:
                emails.add(c.email)
            if c.phoneNumber:
                phoneNumbers.add(c.phoneNumber)
            if c.linkPrecedence == 'secondary':
                secondary_ids.append(c.id)

    emails = list(emails)
    phoneNumbers = list(phoneNumbers)

    if primary_contact.email and primary_contact.email in emails:
        emails.remove(primary_contact.email)
        emails = [primary_contact.email] + emails
    if primary_contact.phoneNumber and primary_contact.phoneNumber in phoneNumbers:
        phoneNumbers.remove(primary_contact.phoneNumber)
        phoneNumbers = [primary_contact.phoneNumber] + phoneNumbers

    response = {
        "contact": {
            "primaryContactId": primary_contact.id,
            "emails": emails,
            "phoneNumbers": phoneNumbers,
            "secondaryContactIds": secondary_ids
        }
    }

    return JsonResponse(response)
