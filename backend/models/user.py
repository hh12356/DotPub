from tortoise.models import Model
from tortoise import fields

class UserAccount(Model):
    user_id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=32,description="用户名")
    user_pwd = fields.CharField(max_length=255,description="用户密码哈希")
    user_phone = fields.CharField(max_length=11,description="用户手机号")
    user_bio = fields.CharField(max_length=100, default="", description="用户简介")
    user_join_date = fields.DatetimeField(null=True, auto_now_add=True, description="加入时间")

    articles = fields.ReverseRelation["Article"]













