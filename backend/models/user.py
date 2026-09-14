from tortoise.models import Model
from tortoise import fields

class UserAccount(Model):
    user_id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=32,description="用户名")
    user_pwd = fields.CharField(max_length=32,description="用户密码")
    user_phone = fields.CharField(max_length=11,description="用户手机号")
    # default="" 必须给：注册接口不传 user_bio，NOT NULL 又没默认值会在严格模式下报 1364
    user_bio = fields.CharField(max_length=100, default="", description="用户简介")
    # null=True 必须给：auto_now_add 只在应用层填值，数据库层面没有默认值可用，
    # 给已有数据的表加 NOT NULL 的 DATETIME 列会被严格模式拒绝(1067)
    user_join_date = fields.DatetimeField(null=True, auto_now_add=True, description="加入时间")

    articles = fields.ReverseRelation["Article"]













