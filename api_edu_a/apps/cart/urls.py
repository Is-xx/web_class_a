from django.urls import path

from cart import views

urlpatterns = [
    path("option/", views.CartViewSet.as_view({"post": "add_cart", "get": "list_cart", 'put': 'change_select', 'delete': 'delete_course', 'patch': 'change_expire'})),
    path('options/', views.CartOptionViewSet.as_view({'put': 'select_all', 'get': 'check_select'})),
    path('order/', views.CartOptionViewSet.as_view({'get': 'get_select_course'})),
]
