from django.db import models
from oauth2client.contrib.django_util.models import CredentialsField
# Create your models here.

'''
log(생성 시각, 수정 시각)를 위해 모든 모델에서 사용하는 Base model
'''


class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


'''
사용자
'''


class User(Base):
    name = models.CharField(max_length=100)
    email_address = models.CharField(max_length=254, unique=True)
    read_num = models.IntegerField(default=0)
    profile_picture = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.email_address


class Credentials(Base):
    id = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE)
    credential = CredentialsField()


'''
뉴스
'''


class Subscription(Base):
    user = models.ManyToManyField(User)
    name = models.CharField(max_length=100)
    email_address = models.CharField(max_length=254, unique=True)

    def __str__(self):
        return self.email_address


'''
사용자가 구독한 뉴스를 연결해주는 매개 테이블
'''


class UserSubscription(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    def __str__(self):
        return '{}->{}'.format(self.user.email_address, self.subscription.email_address)


'''
사용자가 북마크한 이메일 정보
'''


class Bookmark(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return '{}->{}'.format(self.user.email_address, self.email_id)
