from tortoise.models import Model
from tortoise import fields

class Article(Model):
    art_id = fields.IntField(pk=True)
    art_title = fields.CharField(max_length=32,description="文章标题")
    art_pub_datetime = fields.DatetimeField(auto_now_add=True,description="文章发布时间")
    art_content = fields.TextField(description="文章内容")

    art_author = fields.ForeignKeyField(
        "models.UserAccount",
        related_name="articles",
        description="文章作者id"
    )


