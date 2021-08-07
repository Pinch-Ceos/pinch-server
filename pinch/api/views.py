from google_auth.utils import login_decorator, user_login_decorator, login_decorator_viewset
from .models import Subscription, User, Bookmark, Credentials
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, mixins
from .serializers import SubscriptionSerializer, BookmarkSerializer
import base64
from tqdm import tqdm
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@user_login_decorator
def user_info(request):
    user = User.objects.get(id=request.user.id)

    if request.method == 'GET':
        sub_list = list()
        subscriptions = Subscription.objects.filter(user=user)
        subscription_num = subscriptions.count()
        bookmark_num = Bookmark.objects.filter(user=user).count()
        for sub in subscriptions:
            dic = d = {'id': sub.id, 'name': sub.name,
                       'email_address': sub.email_address}
            sub_list.append(dic)

        return JsonResponse({
            'user_name': user.name,
            'user_email_address': user.email_address,
            'profile_picture': user.profile_picture,
            'subscriptions': sub_list,
            'subscription_num': subscription_num,
            'bookmark_num': bookmark_num,
            'read_num': user.read_num,
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    if request.method == 'DELETE':
        User.objects.get(id=request.user.id).delete()
        return JsonResponse({
            'message': "deleted",
        }, json_dumps_params={'ensure_ascii': False}, status=204)


@login_decorator
def email_senders(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()
    service = build('gmail', 'v1', credentials=creds)

    # get list of email_address that user subscribes
    subscriptions = Subscription.objects.filter(
        user=request.user.id).values_list('email_address', flat=True)
    subscriptions = list(subscriptions)

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
        try:
            txt = sender = None
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
            if (email_address not in subscriptions) and (d not in email_senders):
                email_senders.append(d)
        except:
            pass
    return JsonResponse(email_senders, status=200, safe=False)


def email_response(messages, service, bookmarks):
    email_list = list()

    if messages == None:
        return email_list

    progress = tqdm(messages, total=len(messages), desc='뉴스레터를 가져오기')

    for msg in progress:
        try:
            txt = sender = subject = date = image = None
            txt = service.users().messages().get(
                userId='me', id=msg['id']).execute()

            payload = txt['payload']
            headers = payload['headers']
            snippet = txt['snippet']
            labels = txt["labelIds"]

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
            # TO-DO 다른 데이터 있는것도 살펴보기
            parts = payload.get('parts', None)
            if not parts:
                data = payload['body']['data']

            else:
                for p in parts:
                    if p['mimeType'] == 'text/html':
                        data = p['body']['data']
                        break

            data = data.replace("-", "+").replace("_", "/")
            data = base64.b64decode(data)
            bs = BeautifulSoup(data, "html.parser")
            images = bs.find_all('img')

            for img in images:
                if img.has_attr('src') and (img['src'].endswith('.png') or img['src'].endswith('.jpg') or img['src'].endswith('.gif')):
                    image = img['src']
                    break

            bookmark_id = None
            if msg['id'] in bookmarks:
                bookmark_id = bookmarks[msg['id']]

            d = {
                'id': msg['id'],
                'name': name,
                'email_address': email_address,
                'datetime': date,
                'subject': subject,
                'snippet': snippet,
                'image': image,
                'read': "UNREAD" not in labels,
                'bookmark_id': bookmark_id
            }

            email_list.append(d)
        except Exception as e:
            print(e)

    return email_list


@ login_decorator
def email_list(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()

    service = build('gmail', 'v1', credentials=creds)

    subscription = request.GET.get("subscription", None)
    search = request.GET.get("search", None)
    unread = request.GET.get("unread", None)

    email_list = []

    q = ""
    if subscription:
        # get list of email_address that user subscribes
        subscriptions = Subscription.objects.filter(
            user=request.user.id).values_list('email_address', flat=True)
        subscriptions = list(subscriptions)
        if subscription not in subscriptions:
            JsonResponse({'message': "wrong subscription name"},
                         status=404, safe=False)

        q += "from:{} ".format(subscription)
    else:
        q += "{"
        subscriptions = Subscription.objects.filter(
            user=user).values_list('email_address', flat=True)
        if not subscriptions:
            size = 0
            return JsonResponse(
                {'num_of_email': size,
                 'email_list': email_list
                 },
                status=200, safe=False)

        for sub in subscriptions:
            q += "from:{} ".format(sub)
        q += "}"

    if search:
        q += '"{}"'.format(search)

    if unread == 'True':
        q += "label:UNREAD "

    result = service.users().messages().list(maxResults=500,
                                             userId='me', q=q).execute()

    messages = result.get('messages')
    size = len(messages)

    if messages:
        # pagination logic
        # TO-DO : 100개 이상이면 추가로 불러오기
        bookmarks = Bookmark.objects.filter(
            user=request.user.id).values_list('email_id', 'id')
        bookmarks = dict(bookmarks)

        paginator = Paginator(messages, 12)
        page = request.GET.get('page')
        messages = paginator.page(page)
        email_list = email_response(messages, service, bookmarks)

    return JsonResponse(
        {'num_of_email': size,
         'email_list': email_list
         },
        status=200, safe=False)


@ login_decorator
def email_bookmark(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()

    service = build('gmail', 'v1', credentials=creds)

    ids = Bookmark.objects.filter(
        user=request.user.id).values_list('id', 'email_id')

    messages = list()
    for id in ids:
        messages.append(
            {
                'bookmark_id': id[0],
                'id': id[1],
            }
        )
    email_list = []
    if messages:
        # pagination logic
        paginator = Paginator(messages, 12)
        page = request.GET.get('page')
        messages = paginator.page(page)

        bookmarks = Bookmark.objects.filter(
            user=request.user.id).values_list('email_id', 'id')
        bookmarks = dict(bookmarks)

        email_list = email_response(messages, service, bookmarks)

    return JsonResponse(email_list, status=200, safe=False)


@ login_decorator
def email_detail_info(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()

    bookmarks = Bookmark.objects.filter(
        user=request.user.id).values_list('email_id', 'id')
    bookmarks = dict(bookmarks)

    service = build('gmail', 'v1', credentials=creds)

    email_id = request.GET.get("email_id")

    txt = service.users().messages().get(
        userId='me', id=email_id).execute()

    payload = txt['payload']
    headers = payload['headers']
    # parse the sender
    for d in headers:
        if d['name'] == 'From':
            sender = d['value']
        if d['name'] == 'Subject':
            subject = d['value']

    i = sender.rfind("<")
    name = sender[:i-1:]
    name = name.replace('"', '')
    name = name.replace("\\", '')\

    bookmark_id = None
    if email_id in bookmarks:
        bookmark_id = bookmarks[email_id]

    return JsonResponse({
        'name': name,
        'subject': subject,
        'bookmark_id': bookmark_id,
    }, json_dumps_params={'ensure_ascii': False}, status=200)


@ login_decorator
def email_detail(request):
    user = User.objects.get(id=request.user.id)
    storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
    creds = storage.get()

    service = build('gmail', 'v1', credentials=creds)

    email_id = request.GET.get("email_id")

    txt = service.users().messages().get(
        userId='me', id=email_id).execute()

    labels = txt["labelIds"]
    payload = txt['payload']

    # data 로직 잘 살펴보기
    parts = payload.get('parts', None)
    if not parts:
        data = payload['body']['data']

    else:
        for p in parts:
            if p['mimeType'] == 'text/html':
                data = p['body']['data']
                break

    data = data.replace("-", "+").replace("_", "/")
    data = base64.b64decode(data)

    if "UNREAD" in labels:
        # read 되게 바꾸는 로직
        service.users().messages().modify(
            userId='me', id=email_id, body={'removeLabelIds': ['UNREAD']}).execute()
        user.read_num += 1
        user.save()

    return HttpResponse(data)


class SubscriptionViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

    @ login_decorator_viewset
    def create(self, request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        for data in request.data:
            try:
                subscription, created = Subscription.objects.get_or_create(
                    email_address=data["email_address"])
                subscription.name = data["name"]
                subscription.user.add(user)
                subscription.save()
            except:
                pass

        sub_list = list()
        subscriptions = Subscription.objects.filter(user=request.user.id)
        for sub in subscriptions:
            dic = d = {'id': sub.id, 'name': sub.name,
                       'email_address': sub.email_address}
            sub_list.append(dic)
        return JsonResponse({
            'subscriptions': sub_list,
        }, json_dumps_params={'ensure_ascii': False}, status=201)

    @ login_decorator_viewset
    def destroy(self, request, *args, **kwargs):
        subscription = self.get_object()
        subscription.user.remove(request.user.id)
        return JsonResponse({
            'message': "deleted",
        }, json_dumps_params={'ensure_ascii': False}, status=204)


class BookmarkViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()

    @ login_decorator_viewset
    def create(self, request, *args, **kwargs):
        self.request.data.update({"user": request.user.id})
        return super().create(request, *args, **kwargs)

    @ login_decorator_viewset
    def destroy(self, request, *args, **kwargs):
        self.request.data.update({"user": request.user.id})
        return super().destroy(request, *args, **kwargs)
