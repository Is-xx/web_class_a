from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """用户"""
    phone = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    user_pic = models.ImageField(upload_to="user_pic", verbose_name="用户头像", blank=True, null=True)

    class Meta:
        db_table = "edu_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
