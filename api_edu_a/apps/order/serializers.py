from datetime import datetime

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from course.models import Course, CourseExpire
from order.models import Order, OrderDetail


class OrderModelSerializer(ModelSerializer):
    """订单序列化器"""
    class Meta:
        model = Order
        fields = ("id", "order_number", "pay_type")

        # 基本约束
        extra_kwargs = {
            "id": {"read_only": True},
            "order_number": {"read_only": True},
            "pay_type": {"write_only": True},
        }

    # 全局钩子
    def validate(self, attrs):
        """对数据进行校验"""
        pay_type = attrs.get("pay_type")
        try:
            Order.pay_choices[pay_type]
        except Order.DoesNotExist:
            raise serializers.ValidationError("您当前选择的支付方式不允许~")
        return attrs

    def create(self, validated_data):
        """
        创建订单
        创建订单详情
        """
        # 获取当前订单所需的课程数据
        redis_connection = get_redis_connection("cart")
        pipeline = redis_connection.pipeline()
        # 获取到当前登录的用户对象
        user_id = self.context['request'].user.id
        # 生成唯一的订单号  时间戳  用户ID
        order_number = datetime.now().strftime("%Y%m%d%H%M%S") + "%06d" % user_id
        # 订单的生成
        order = Order.objects.create(
            order_title="罗小黑线上授课订单",
            total_price=0,
            real_price=0,
            order_number=order_number,
            order_status=0,
            pay_type=validated_data.get("pay_type"),
            credit=0,
            coupon=0,
            order_desc="每天学习 真不错！！！",
            user_id=user_id,
        )
        cart_list = redis_connection.hgetall("cart_%s" % user_id)
        select_list = redis_connection.smembers("selected_%s" % user_id)
        # 生成订单详情
        """
        1. 获取购物车中所有被勾选的商品
        2. 判断商品是否在已勾选的列表中
        3. 判断课程的状态是否正常  不正常直接抛出异常
        4. 判断商品的有效期  根据有效期计算商品优惠后的价格
        5. 生成订单详情。
        6. 计算订单的总价  原价
        """
        for course_id_byte, expire_id_byte in cart_list.items():
            course_id = int(course_id_byte)
            expire_id = int(expire_id_byte)
            # 判断商品是否被勾选
            if course_id_byte in select_list:
                # 获取课程的所有信息
                try:
                    course = Course.objects.get(is_delete=False, is_show=True, pk=course_id)
                except Course.DoesNotExist:
                    raise serializers.ValidationError("对不起，您所购买的商品不存在")
                # 如果课程的有效期id大于0，则需要重新计算商品的价格，id不大于0则是永久有效
                origin_price = course.price
                expire_text = "永久有效"
                final_price = course.real_price()
                if expire_id > 0:
                    course_expire = CourseExpire.objects.get(pk=expire_id)
                    # 获取有效期对应的原价
                    origin_price = course_expire.price
                    expire_text = course_expire.expire_text
                    temp = course.price
                    course.price = origin_price
                    final_price = course.real_price()
                    course.price = temp
                try:
                    OrderDetail.objects.create(
                        order=order,
                        course=course,
                        expire=expire_id,
                        price=origin_price,
                        real_price=final_price,
                        discount_name=course.discount_name,
                    )
                except:
                    raise serializers.ValidationError("订单生成失败")
                # 计算订单的总价  原价
                order.total_price += float(origin_price)
                order.real_price += float(final_price)
                # 如果商品已经成功生成了订单  需要将该商品从购物车中移除
                pipeline.hdel("cart_%s" % user_id, course_id)
                pipeline.srem("selected_%s" % user_id, course_id)
        pipeline.execute()
        order.save()
        return order
