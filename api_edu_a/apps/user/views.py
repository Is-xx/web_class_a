import re

from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as http_status
from rest_framework_jwt.settings import api_settings

from api_edu_a.libs.geetest import GeetestLib
from api_edu_a.utils import constant
from api_edu_a.utils.random_code import create_random_code
from api_edu_a.utils.send_msg import Message
from user.models import User
from user.serializers import UserModelSerializer
from user.utils import get_user_by_account

pc_geetest_id = "baomi"
pc_geetest_key = "baomi"


class CaptchaAPIView(APIView):
    """滑块验证码"""
    user_id = 0
    status = False
    # pc端获取验证码的方法
    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        user = get_user_by_account(username)
        if user is None:
            return Response({"message": "用户不存在"}, status=http_status.HTTP_400_BAD_REQUEST)
        self.user_id = user.id
        # 验证码的实例化对象
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        self.status = gt.pre_process(self.user_id)
        response_str = gt.get_response_str()
        return Response(response_str)

    # pc端基于前后端分离校验验证码
    def post(self, request, *args, **kwargs):
        """验证验证码"""
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        if self.user_id:
            result = gt.success_validate(challenge, validate, seccode, self.user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        result = {"status": "success"} if result else {"status": "fail"}
        return Response(result)


class MobileCheckAPIView(APIView):
    def get(self, request, *args, **kwargs):
        phone = request.query_params.get('phone')
        # 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return Response({"message": "手机号格式不正确"},
                            status=http_status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'OK'})


class SendMessageAPIView(APIView):
    def get(self, request, *args, **kwargs):
        phone = request.query_params.get('phone')
        # 获取redis连接
        redis_connection = get_redis_connection("sms_code")
        # 判断用户60s内是否发送过验证码
        sms_code = redis_connection.get("sms_%s" % phone)
        if sms_code is not None:
            return Response({"message": "您已经在60s内发送过短信了，请稍等~"},
                            status=http_status.HTTP_400_BAD_REQUEST)
        # 生成随机验证码
        code = create_random_code()
        # 将验证码保存在redis中
        mobile_code = redis_connection.get("mobile_%s" % phone)
        if mobile_code:
            redis_connection.delete("mobile_%s" % phone)
            redis_connection.delete("count_%s" % phone)
        redis_connection.setex('sms_%s' % phone, constant.SMS_EXPIRE_TIME, code)  # 验证码间隔时间
        redis_connection.setex("mobile_%s" % phone, constant.CODE_EXPIRE_TIME, code)  # 验证码有效期
        redis_connection.setex("count_%s" % phone, constant.CODE_EXPIRE_TIME, 0)  # 验证次数有效期
        # 完成短信的发送
        try:
            message = Message(constant.API_KEY)
            message.send_message(phone, code)
        except:
            return Response({"message": "验证码发送失败"},
                            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "短信发送成功"},
                        status=http_status.HTTP_200_OK)


class RegisterAPIView(CreateAPIView):
    """用户名注册"""
    queryset = User.objects.all()
    serializer_class = UserModelSerializer


class PhoneLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        """手机注册"""
        phone = request.data.get('phone')
        code = request.data.get('code')
        user = User.objects.filter(phone=phone).first()
        if user:
            redis_connection = get_redis_connection("sms_code")
            mobile_code = redis_connection.get("mobile_%s" % phone)
            redis_connection.incr("count_%s" % phone)
            count_code = redis_connection.get("count_%s" % phone)
            if int(count_code) > 5:
                return Response({"message": '验证次数过多'},
                                status=http_status.HTTP_400_BAD_REQUEST)
            if mobile_code.decode() != code:
                return Response({"message": '验证码错误'},
                                status=http_status.HTTP_400_BAD_REQUEST)
            redis_connection.delete("mobile_%s" % phone)
            redis_connection.delete("count_%s" % phone)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            user.token = jwt_encode_handler(payload)
            return Response(UserModelSerializer(user).data)
        else:
            return Response({"message": '用户不存在'},
                            status=http_status.HTTP_400_BAD_REQUEST)
