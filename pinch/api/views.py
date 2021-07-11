from google_auth.utils import login_decorator
from .models import User
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from googleapiclient.discovery import build
from datetime import date, timedelta
from django.http import HttpResponse, JsonResponse


@login_decorator
def email_senders(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(User, 'id', user.id, 'credential')

    creds = storage.get()
    service = build('gmail', 'v1', credentials=creds)

    today = date.today() + timedelta(1)
    lastweek = today - timedelta(9)
    query = "before: {0} after: {1}".format(
        today.strftime('%Y/%m/%d'), lastweek.strftime('%Y/%m/%d'))

    result = service.users().messages().list(
        userId='me', q=query).execute()
    messages = result.get('messages')
    email_senders = list()

    for msg in messages:
        txt = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata').execute()
        headers = txt['payload']['headers']

        for d in headers:
            if d['name'] == 'From':
                sender = d['value']

        sender.encode('utf8')
        i = sender.rfind("<")
        name = sender[:i-1:]
        name = name.replace('"', '')
        name = name.replace("\\", '')
        email_address = sender[i+1:len(sender)-1:]
        d = {'name': name, 'email_address': email_address}
        if d not in email_senders:
            email_senders.append(d)
    return JsonResponse(email_senders, status=200, safe=False)
