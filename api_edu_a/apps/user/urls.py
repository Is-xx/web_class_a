from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

from user import views

urlpatterns = [
    path('login/', obtain_jwt_token),
    path('captcha/', views.CaptchaAPIView.as_view()),
    path('register/', views.RegisterAPIView.as_view()),
    path('phone/', views.MobileCheckAPIView.as_view()),
    path('send/', views.SendMessageAPIView.as_view()),
    path('phone_login/', views.PhoneLoginAPIView.as_view()),
]