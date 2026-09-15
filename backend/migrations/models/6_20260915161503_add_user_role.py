from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` ADD `user_role` VARCHAR(32) NOT NULL COMMENT '用户权限' DEFAULT 'user';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` DROP COLUMN `user_role`;"""


MODELS_STATE = (
    "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"
)
