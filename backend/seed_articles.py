"""一次性种子脚本：把 seeds/ 下的技术文章写进 DotPub 库。

    cd backend
    python seed_articles.py           # 写入
    python seed_articles.py --clean   # 先删掉同名旧文章再写（重跑用）

正文走的是 apis.article.clean_html，和 POST /article 同一个白名单，
种子数据和线上写入路径产出的格式是一致的。
"""
import asyncio
import random
import re
import sys
from datetime import datetime, timedelta

from tortoise import Tortoise

from apis.article import clean_html
from core.setting import TORTOISE_ORM
from models.article import Article
from models.interaction import ArticleLike, ArticleStar
from models.user import UserAccount

from seeds.part1_net_frontend import ARTICLES as PART1
from seeds.part2_backend_db import ARTICLES as PART2
from seeds.part3_sec_ops import ARTICLES as PART3

ARTICLES = PART1 + PART2 + PART3


def tidy(html: str) -> str:
    """去掉 </code></pre> 前面那个换行。

    HTML 只忽略 <pre> 开标签后紧跟的第一个换行，<pre><code> 后面的和结尾的
    都不忽略；正文是 white-space: pre，结尾那个换行会渲染成代码块底部多一行
    空白（加了灰底之后特别明显）。
    """
    return re.sub(r"\s+</code></pre>", "</code></pre>", html)


def stamp(rng, pub, now):
    """点赞/收藏只能发生在文章发布之后，取个随机时刻；最近几篇会被 now 截断。"""
    return min(pub + timedelta(minutes=rng.randint(30, 3000)), now)

# art_title 是 VARCHAR(32)，超了 MySQL 严格模式会直接报错，提前拦
for _a in ARTICLES:
    assert len(_a["title"]) <= 32, f"标题超 32 字符：{_a['title']}"


async def main():
    await Tortoise.init(config=TORTOISE_ORM)

    titles = [a["title"] for a in ARTICLES]
    if "--clean" in sys.argv:
        removed = await Article.filter(art_title__in=titles).delete()
        print(f"先删掉同名旧文章 {removed} 篇\n")

    # 作者分散挂到已有账号，首页才不像一个人刷屏
    # zzz_test 是测试号；yuan 名下的文章够多了（已有 2 篇），不再分新的
    users = await UserAccount.exclude(user_name__in=["zzz_test", "yuan"]).order_by("user_id")
    if not users:
        raise SystemExit("库里没有可用账号，先注册一个再跑")
    # 下面要按「作者之外的人」抽样，1 个人连 randint(2, 1) 都过不去
    assert len(users) >= 3, f"可用账号只有 {len(users)} 个，凑不出互动记录"

    now = datetime.now()
    total = len(ARTICLES)
    created = []
    for i, item in enumerate(ARTICLES):
        author = users[i % len(users)]
        # auto_now_add 只在值为 None 时才自动填（tortoise/fields/data.py:489），
        # 显式传的时间戳会被保留。不传的话十几篇时间戳一模一样，
        # Latest 按时间排序就退化成随机了。
        pub = now - timedelta(days=3 * (total - i), hours=(i * 7) % 24)
        art = await Article.create(
            art_title=item["title"],
            art_content=clean_html(tidy(item["content"])),
            art_author_id=author.user_id,
            art_pub_datetime=pub,
        )
        created.append((art, pub))
        print(f"{art.art_id:>4}  {author.user_name:<8} {item['title']}")

    print(f"\n共写入 {total} 篇，作者 {len(users)} 人")

    # 收藏的人必须是点过赞的人，这样「点赞比收藏多」是结构上成立的，
    # 不用靠调概率。固定种子，--clean 重跑分布一致
    rng = random.Random(20260913)
    likes, stars = [], []
    for art, pub in created:
        others = [u for u in users if u.user_id != art.art_author_id]
        likers = rng.sample(others, rng.randint(2, len(others)))
        starrers = rng.sample(likers, rng.randint(1, max(1, len(likers) // 2)))
        for u in likers:
            likes.append(ArticleLike(
                user_id=u.user_id, art_id=art.art_id, created_at=stamp(rng, pub, now)))
        for u in starrers:
            stars.append(ArticleStar(
                user_id=u.user_id, art_id=art.art_id, created_at=stamp(rng, pub, now)))

    await ArticleLike.bulk_create(likes)
    await ArticleStar.bulk_create(stars)
    print(f"点赞 {len(likes)} 条，收藏 {len(stars)} 条")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
