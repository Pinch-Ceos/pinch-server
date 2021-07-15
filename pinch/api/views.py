from google_auth.utils import login_decorator
from .models import Subscription, User, Bookmark, Credentials
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, mixins
from .serializers import SubscriptionSerializer, BookmarkSerializer
import base64
from tqdm import tqdm


@login_decorator
def email_senders(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()
    print(creds)
    service = build('gmail', 'v1', credentials=creds)

    today = datetime.today() + timedelta(1)
    lastweek = today - timedelta(9)
    query = "before: {0} after: {1}".format(
        today.strftime('%Y/%m/%d'), lastweek.strftime('%Y/%m/%d'))

    # get list of emails
    result = service.users().messages().list(
        userId='me', q=query).execute()
    messages = result.get('messages')
    email_senders = list()

    if messages == None:
        return JsonResponse(email_senders, status=200, safe=False)

    for msg in messages:
        txt = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata').execute()
        headers = txt['payload']['headers']

        # parse the sender
        for d in headers:
            if d['name'] == 'From':
                sender = d['value']

        i = sender.rfind("<")
        name = sender[:i-1:]
        name = name.replace('"', '')
        name = name.replace("\\", '')
        email_address = sender[i+1:len(sender)-1:]
        # save the sender info in dic
        d = {'name': name, 'email_address': email_address}
        if d not in email_senders:
            email_senders.append(d)
    return JsonResponse(email_senders, status=200, safe=False)


def attach_label(user_id):
    user = User.objects.get(id=user_id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    time = user.last_email_time
    label_id = user.label_id
    creds = storage.get()

    # get list of email_address that user subscribes
    subscriptions = Subscription.objects.filter(
        user=user_id).values_list('email_address', flat=True)
    subscriptions = list(subscriptions)

    service = build('gmail', 'v1', credentials=creds)

    # new user
    if not time:
        result = service.users().messages().list(maxResults=500, userId='me').execute()
    else:
        # 여기 테스트 해보기
        today = datetime.today() + timedelta(1)
        query = "before: {0} after: {1}".format(
            today.strftime('%Y/%m/%d'), time.strftime('%Y/%m/%d'))
        # now DB에 업데이트
        user.last_email_time = datetime.now()
        user.save()

        # get unfiltered email
        result = service.users().messages().list(
            userId='me', q=query).execute()

    messages = result.get('messages')
    # 라벨 없을 때 로직 만들기
    if not messages:
        return service
    progress = tqdm(messages, total=len(result), desc='필터링')
    for msg in progress:
        try:
            txt = service.users().messages().get(
                userId='me', id=msg['id'], format='metadata').execute()
            headers = txt['payload']['headers']
            sender = None
            for d in headers:
                if d['name'] == 'From':
                    sender = d['value']

            i = sender.rfind("<")
            email_address = sender[i+1:len(sender)-1:]

            if email_address in subscriptions:
                r = service.users().messages().modify(userId='me', id=msg['id'], body={
                    'addLabelIds': [label_id]
                }).execute()
                txt = service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata').execute()
        except:
            pass

    return service


@ login_decorator
def email(request):
    service = attach_label(request.user.id)
    subscription = request.GET.get("subscription")
    print(subscription)
    # subscription이 구독한 곳인지 확인하는 로직 추가

    email_list = list()

    if not subscription:
        result = service.users().messages().list(
            userId='me', q='label:pinch').execute()
    else:
        result = service.users().messages().list(
            userId='me', q="label:pinch from:{}".format(subscription)).execute()

    messages = result.get('messages')
    if messages == None:
        return JsonResponse(email_list, status=200, safe=False)

    progress = tqdm(messages, total=len(result), desc='뉴스레터를 가져오기')

    for msg in progress:
        try:
            txt = service.users().messages().get(
                userId='me', id=msg['id']).execute()

            payload = txt['payload']
            headers = payload['headers']
            snippet = txt['snippet']

            # parse the sender
            for d in headers:
                if d['name'] == 'From':
                    sender = d['value']
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'Date':
                    date = d['value']

            i = sender.rfind("<")
            name = sender[:i-1:]
            name = name.replace('"', '')
            name = name.replace("\\", '')
            email_address = sender[i+1:len(sender)-1:]

            # data 로직 잘 살펴보기
            data = payload['body']['data']
            data = data.replace("-", "+").replace("_", "/")
            data = base64.b64decode(data)
            d = {
                'name': name,
                'email_address': email_address,
                'datetime': date,
                'subject': subject,
                'snippet': snippet,
                # 'body': str(data)
            }
            email_list.append(d)
        except:
            pass

    return JsonResponse(email_list, status=200, safe=False)


class SubscriptionViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()


class BookmarkViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()
