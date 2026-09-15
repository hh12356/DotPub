from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` MODIFY COLUMN `user_pwd` VARCHAR(255) NOT NULL COMMENT '用户密码哈希';
        ALTER TABLE `useraccount` MODIFY COLUMN `user_pwd` VARCHAR(255) NOT NULL COMMENT '用户密码哈希';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` MODIFY COLUMN `user_pwd` VARCHAR(32) NOT NULL COMMENT '用户密码';
        ALTER TABLE `useraccount` MODIFY COLUMN `user_pwd` VARCHAR(32) NOT NULL COMMENT '用户密码';"""


MODELS_STATE = (
    "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"
    "GtVWCtAisLKqyQCpz+DzfdHX8="
)
