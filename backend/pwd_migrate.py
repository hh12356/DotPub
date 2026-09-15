"""把存量明文密码一次性哈希。只能跑一次——跑完明文就没了。

跑法：  cd backend && py migrate_passwords.py
幂等：已经以 $argon2id$ 开头的跳过，所以中途挂了直接重跑就行。
"""
import asyncio

from tortoise import Tortoise

from core.security import hash_pwd
from core.setting import TORTOISE_ORM
from models.user import UserAccount


async def main():
    await Tortoise.init(config=TORTOISE_ORM)

    done = 0
    for u in await UserAccount.all():
        if u.user_pwd.startswith("$argon2id$"):     # 幂等 guard
            continue
        u.user_pwd = hash_pwd(u.user_pwd)
        await u.save(update_fields=["user_pwd"])
        done += 1

    left = await UserAccount.filter(user_pwd__not=...).count()   # 见下
    print(f"已迁移 {done} 个用户")               # 只打数量，绝不打密码或哈希
    await Tortoise.close_connections()


asyncio.run(main())