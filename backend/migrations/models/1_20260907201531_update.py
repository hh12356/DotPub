from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `useraccount` (
    `user_id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_name` VARCHAR(32) NOT NULL COMMENT '用户名',
    `user_pwd` VARCHAR(32) NOT NULL COMMENT '用户密码',
    `user_phone` VARCHAR(11) NOT NULL COMMENT '用户手机号'
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `useraccount`;"""


MODELS_STATE = (
    "eJztlW1v2jAQx79K5FedxCaSEIJ4R9Gmbdqo1LJp0pgsxzGJ1cRO/bC2ovnuk51AIDwM+q"
    "Zl2svc/86++zl3twA5j0km332TRIww5popMHQWgKGcgKGzS+44ABVFIxqDQlFm/bUkAq05"
    "RlIJhM2Zc5RJ0nFATCQWtFCUMzB0mM4yY+RYKkFZ0pg0o3eaQMUTolIiwND5+avjAMpi8k"
    "Dk8rO4hXNKsngjaZMEpLFJwIpQPRZW+MTUB+ttrowg5pnOWSuieFQpZ6sQWhWSEEYEUsRc"
    "pIQ2hZg867KXtVU5Ny5VsmsxMZkjnam1wiPY2ACEk6spvHk/hRCcgApzZjBTpgyXBUhMCm"
    "89txf2Bn6/N+g4wKa5soRldXVDpwq0jCZTUFodKVR5WNotvPZjC/A4ReIA4WVQi7FUos14"
    "SfQQ5KWhodz8Y8/HDGY6DLzBTPc9P5zpoNetivk79hw9wIywRKVg6PjeAcbfR9fjj6PrC9"
    "97Y87mAuGqfSa14lnJPEMLe3Efn0y9jjkn6BHuz3Q46LqvCX3K2em//CrqjPD3vV400/3Q"
    "RzMd+PPwOY/gukc8guvufQQjlaUZ8fN6xK9mfoTw7T0SMdxSuMf3+W5LuZe3LYihxEI1FZ"
    "r86/U3IoLidNdirJWDOxE1Pi+yDk/ahP+X4HFL8DcR0qR0wjxYC3nNw+B4xBsN7wXBER3v"
    "BcHelrfa5uA1TXUC4dr9H6TrdrvHzNNud/9ANdomXcyZIlVrbxL+fHM12U14LaRFOaZYOU"
    "9ORqU6Q9rlfrgGhjk5l/IuW2d68XX0o417/OXq0sLhUiXCnmIPuHzpZVb+Aa4Ia4s="
)
