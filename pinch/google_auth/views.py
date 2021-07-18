from api.models import User, Credentials, Subscription, Bookmark
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from django.http import HttpResponse, JsonResponse
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from pinch.settings import JWT_SECRET
import jwt

# Create your views here.

# flow = Flow.from_client_secrets_file(
#     'pinch/client_secrets.json',
#     scopes=['openid',
#             'https://www.googleapis.com/auth/userinfo.email',
#             'https://www.googleapis.com/auth/userinfo.profile',
#             'https://www.googleapis.com/auth/gmail.readonly',
#             'https://www.googleapis.com/auth/gmail.labels',
#             'https://www.googleapis.com/auth/gmail.modify'],
#     redirect_uri='http://localhost:3000/redirect')


'''
    로그인 요청
    -------
    로그인 요청이 들어오면, 인증 uri를 사용자에게 전송
'''


def google_login(request):
    auth_uri = flow.authorization_url()
    return HttpResponse(auth_uri[0])


'''
로그인 후 받은 인가코드를 통해 oauth 인증
'''


def google_callback(request):

    # 테스트 용 코드
    flow = InstalledAppFlow.from_client_secrets_file(
        'pinch/client_secrets_.json',
        scopes=['openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.labels',
                'https://www.googleapis.com/auth/gmail.modify'])

    flow.run_local_server()

    # code = request.POST.get('code')
    # print("hi", code)
    # flow.fetch_token(code=code)

    creds = flow.credentials

    # 인증 정보를 통해, 사용자 정보를 구글에 요청함
    users_service = build('oauth2', 'v2', credentials=creds)
    user_document = users_service.userinfo().get().execute()

    email_addr = user_document['email']
    name = user_document['name']

    try:
        # 기존 고객
        user = User.objects.get(email_address=email_addr)
        # jwt 발급
        token = jwt.encode({'id': user.id},
                           JWT_SECRET, algorithm='HS256')
        sub_list = list()
        subscriptions = Subscription.objects.filter(user=user)
        subscription_num = subscriptions.count()
        bookmark_num = Bookmark.objects.filter(user=user).count()

        for sub in subscriptions:
            dic = d = {'id': sub.id, 'name': sub.name,
                       'email_address': sub.email_address}
            sub_list.append(dic)

        return JsonResponse({
            'token': token,
            'user_name': name,
            'user_email_address': email_addr,
            'subscriptions': sub_list,
            'subscription_num': subscription_num,
            'bookmark_num': bookmark_num
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except User.DoesNotExist:
        # 신규 고객

        service = build('gmail', 'v1', credentials=creds)
        result = service.users().labels().create(userId='me', body={
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
            'name': 'pinch',
        }).execute()
        print(result)

        user = User.objects.create(
            name=name, email_address=email_addr, label_id=result["id"])
        storage = DjangoORMStorage(Credentials, 'id', user, 'credential')
        storage.put(creds)

        # jwt 발급
        token = jwt.encode({'id': user.id},
                           JWT_SECRET, algorithm='HS256')
        return JsonResponse({
            'token': token,
            'user_name': name,
            'user_email_address': email_addr
        }, json_dumps_params={'ensure_ascii': False}, status=200)
