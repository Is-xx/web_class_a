import re

from django.contrib.auth.hashers import make_password
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_jwt.settings import api_settings

from user.models import User
from user.utils import get_user_by_account


class UserModelSerializer(ModelSerializer):
    token = serializers.CharField(max_length=1024, read_only=True, help_text="用户token")
    code = serializers.CharField(write_only=True, help_text="手机验证码")

    class Meta:
        model = User
        fields = ('phone', 'password', 'id', 'username', 'token', 'code')
        extra_kwargs = {
            "phone": {
                "write_only": True,
            },
            "password": {
                "write_only": True,
            },
            "username": {
                "read_only": True,
            },
            "id": {
                "read_only": True,
            },
        }

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        sms_code = attrs.get('code')
        # 验证手机号是否被注册
        try:
            user = get_user_by_account(phone)
        except User.DoesNotExist:
            user = None
        if user:
            raise serializers.ValidationError("当前手机号已经被注册")
        # 检验密码的格式
        if len(password) > 20 or len(password) < 6:
            raise serializers.ValidationError('密码长度不符合')

        redis_connection = get_redis_connection("sms_code")
        mobile_code = redis_connection.get("mobile_%s" % phone)
        # 为了防止暴力破解  可以设置一个手机号只能验证n次  累加
        redis_connection.incr("count_%s" % phone)
        count_code = redis_connection.get("count_%s" % phone)
        if int(count_code) > 5:
            raise serializers.ValidationError('验证次数过多')
        # 校验验证码是否一致
        if mobile_code.decode() != sms_code:
            raise serializers.ValidationError("验证码不一致")
        # 验证通过后将redis的验证码的删除
        redis_connection.delete("mobile_%s" % phone)
        redis_connection.delete("count_%s" % phone)
        return attrs

    def create(self, validated_data):
        """重定义creat"""
        # 获取密码  对密码进行加密
        password = validated_data.get("password")
        hash_password = make_password(password)
        # 处理用户名的默认值
        username = validated_data.get("phone")
        # 保存数据
        user = User.objects.create(
            phone=username,
            username=username,
            password=hash_password
        )
        # 为注册的用户手动生成token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        user.token = jwt_encode_handler(payload)
        return user
