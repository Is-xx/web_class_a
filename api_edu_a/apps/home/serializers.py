from rest_framework.serializers import ModelSerializer

from home.models import Banner, Navigation


class BannerModelSerializer(ModelSerializer):
    """轮播图"""
    class Meta:
        model = Banner
        fields = ('img', 'link', 'title')


class NavigationSerializer(ModelSerializer):
    """导航栏"""
    class Meta:
        model = Navigation
        fields = ('title', 'link', 'is_site')
