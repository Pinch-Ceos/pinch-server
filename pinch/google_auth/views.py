from api.models import User
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from django.http import HttpResponse
from oauth2client.contrib.django_util.storage import DjangoORMStorage

# Create your views here.
"""
flow = Flow.from_client_secrets_file(
    'pinch/client_secrets.json',
    scopes=['openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.labels'],
    redirect_uri='http://localhost:3000/redirect')
"""


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
                'https://www.googleapis.com/auth/gmail.labels'])

    flow.run_local_server()

    # code = request.GET.get('code')
    # print("hi", code)
    # flow.fetch_token(code=code)

    creds = flow.credentials

    '''
    service = build('gmail', 'v1', credentials=creds)
    result = service.users().messages().list(maxResults=5, userId='me').execute()
    messages = result.get('messages')
    print(messages)
    '''

    # 인증 정보를 통해, 사용자 정보를 구글에 요청함
    users_service = build('oauth2', 'v2', credentials=creds)
    user_document = users_service.userinfo().get().execute()
    print(user_document)

    email_addr = user_document['email']
    name = user_document['name']

    try:
        # 기존 고객
        user = User.objects.get(email_address=email_addr)

    except User.DoesNotExist:
        # 신규 고객
        user = User.objects.create(
            name=name, email_address=email_addr)
        storage = DjangoORMStorage(
            User, 'email_address', request.user, 'credential')
        storage.put(creds)