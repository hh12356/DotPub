from tortoise.models import Model
from tortoise import fields

class UserAccount(Model):
    user_id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=32,description="用户名")
    user_pwd = fields.CharField(max_length=32,description="用户密码")
    user_phone = fields.CharField(max_length=11,description="用户手机号")














