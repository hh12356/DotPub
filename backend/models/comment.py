from tortoise.models import Model
from tortoise import fields

class Comment(Model):
    cmt_id = fields.IntField(pk=True)
    cmt_pub_datetime = fields.DatetimeField(auto_now_add=True,description="评论发布时间")
    cmt_content = fields.TextField(description="评论内容")

    cmt_user = fields.ForeignKeyField(
        "models.UserAccount",
        related_name="comments",
        description="评论作者id"
    )
    cmt_art = fields.ForeignKeyField(
        "models.Article",
        related_name="comments",
        description="评论文章id"
    )