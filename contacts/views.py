import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Contact
from django.utils.timezone import now

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

    # Find all contacts matching email or phoneNumber (including secondary)
    contacts = Contact.objects.filter(
        models.Q(email=email) | models.Q(phoneNumber=phoneNumber),
        deletedAt__isnull=True
    ).order_by('createdAt')

    if not contacts.exists():
        # Create new primary contact
        new_contact = Contact.objects.create(
            email=email,
            phoneNumber=phoneNumber,
            linkPrecedence='primary'
        )
        response = {
            "contact": {
                "primaryContatctId": new_contact.id,
                "emails": [email] if email else [],
                "phoneNumbers": [phoneNumber] if phoneNumber else [],
                "secondaryContactIds": []
            }
        }
        return JsonResponse(response)

    # Find primary contact id: the oldest contact or the one with linkPrecedence='primary'
    primary_contact = contacts.filter(linkPrecedence='primary').first()
    if not primary_contact:
        primary_contact = contacts.order_by('createdAt').first()

    # Collect all contacts linked to the same primary contact
    linked_contacts = Contact.objects.filter(
        models.Q(id=primary_contact.id) | models.Q(linkedId=primary_contact.id),
        deletedAt__isnull=True
    ).order_by('createdAt')

    # Gather emails and phone numbers
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

    # Check if incoming data has new email or phoneNumber not in the set
    new_email = email and email not in emails
    new_phone = phoneNumber and phoneNumber not in phoneNumbers

    if (new_email or new_phone):
        # Create new secondary contact linked to primary
        Contact.objects.create(
            email=email if new_email else None,
            phoneNumber=phoneNumber if new_phone else None,
            linkedId=primary_contact,
            linkPrecedence='secondary'
        )
        # Refresh linked contacts
        linked_contacts = Contact.objects.filter(
            models.Q(id=primary_contact.id) | models.Q(linkedId=primary_contact.id),
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

    # Place primary contact's email and phone first in lists if they exist
    if primary_contact.email and primary_contact.email in emails:
        emails.remove(primary_contact.email)
        emails = [primary_contact.email] + emails
    if primary_contact.phoneNumber and primary_contact.phoneNumber in phoneNumbers:
        phoneNumbers.remove(primary_contact.phoneNumber)
        phoneNumbers = [primary_contact.phoneNumber] + phoneNumbers

    response = {
        "contact": {
            "primaryContatctId": primary_contact.id,
            "emails": emails,
            "phoneNumbers": phoneNumbers,
            "secondaryContactIds": secondary_ids
        }
    }

    return JsonResponse(response)
