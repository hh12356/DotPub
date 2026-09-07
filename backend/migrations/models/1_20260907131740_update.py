from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `useraccount` (
    `user_name` VARCHAR(32) NOT NULL PRIMARY KEY COMMENT '用户名',
    `user_pwd` VARCHAR(32) NOT NULL COMMENT '用户密码'
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `useraccount`;"""


MODELS_STATE = (
    "eJzdlVtv2jAUgP+K5adWYlMIBFDeKNq0ThtILZsmjcpyHBOsJnbqy9qK8d8nO4EECB1I1d"
    "j2mHPzOd+5ZAkzEdNUvf2iqBwSIgzXMARLyHFGYQia1C0AcZ5XSivQOEqdvVFU4pphpLTE"
    "xMac41TRFoAxVUSyXDPBYQi4SVMrFERpyXhSiQxnD4YiLRKqF1TCEHy/awHIeEyfqFp/5v"
    "dozmgabyVtk0DuowWgUyP9nDvVaIHle+dgX40QEanJ+J5T/qwXgm+8lJZWmlBOJdY0rpVj"
    "sy2LX4uKzGEItDR0k3JcCWI6xybVtfIjVMkgQuPJFN2+myIE94DBmekH/mBmen6nPzNB1y"
    "tK2QdIBLfwGdeW1hJm+AmllCd6AUPQ8VfFuxWewso+8XV4M/owvLno+Jc2tpCYFN0dlxrf"
    "qVYuBNa4COJ6stOE/DE+uQelz+u0YC2oelDN4es1ISK9mekPvPb5WmGXYV4uw2Y7IkzuH7"
    "GM0Z5G+OKQ7b4q87NdCeY4cThthTb/8lAMqWRk0XRCSs2L1wNXNmc5HKxhWq+5bh5W1jSm"
    "rLh79TEtl/5PH4rDgHanMbEpvPHb3X530Ol1By0AXZobSf+FAb0eT39zCH5QqWxKJ9yBms"
    "vffAaOR7y18H4QHLHxfhAcXHmns9QrynapTiBcmv+HdNuedwTdtucdpOt023SJ4JoWq71N"
    "+OPtZNxMuOayQzlmRIOfIGVK/4O0V4fhWhg2cqbUQ1pnevF5+G0X9+jT5MrBEUon0kVxAa"
    "7O/TNb/QL4uob9"
)
