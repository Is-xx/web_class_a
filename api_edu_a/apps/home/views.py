from rest_framework.generics import ListAPIView

from api_edu_a.utils.constant import BANNER_LENGTH
from home.models import Banner, Navigation
from home.serializers import BannerModelSerializer, NavigationSerializer


class BannerListAPIView(ListAPIView):
    queryset = Banner.objects.filter(is_show=True, is_delete=False).order_by('orders')[:BANNER_LENGTH]
    serializer_class = BannerModelSerializer


class NavigationListAPIViewH(ListAPIView):
    queryset = Navigation.objects.filter(is_show=True, is_delete=False, position=1).order_by('orders')
    serializer_class = NavigationSerializer


class NavigationListAPIViewF(ListAPIView):
    queryset = Navigation.objects.filter(is_show=True, is_delete=False, position=2).order_by('orders')
    serializer_class = NavigationSerializer
