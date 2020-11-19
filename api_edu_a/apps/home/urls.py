from django.urls import path

from home import views

urlpatterns = [
    path('banner/', views.BannerListAPIView.as_view()),
    path('navigation_h/', views.NavigationListAPIViewH.as_view()),
    path('navigation_f/', views.NavigationListAPIViewF.as_view()),
]
