from tortoise.models import Model
from tortoise import fields


class ArticleLike(Model):
    user = fields.ForeignKeyField('models.UserAccount', related_name='like_records')
    art = fields.ForeignKeyField('models.Article', related_name='like_records')
    created_at = fields.DatetimeField(auto_now_add=True,description="点赞时间")

    class Meta:
        unique_together = (('user', 'art'),)


class ArticleStar(Model):
    user = fields.ForeignKeyField('models.UserAccount', related_name='star_records')
    art = fields.ForeignKeyField('models.Article', related_name='star_records')
    created_at = fields.DatetimeField(auto_now_add=True,description="收藏时间")

    class Meta:
        unique_together = (('user', 'art'),)