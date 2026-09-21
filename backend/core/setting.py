import os
from pathlib import Path

def _load_env(path: Path = Path(__file__).resolve().parent.parent / ".env"):
    """把 backend/.env 里的 KEY=VALUE 塞进 os.environ。文件不存在就静默跳过
    ——线上是平台注入环境变量，本来就没有这个文件。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        # setdefault：真实环境变量优先。这样线上平台注入的值总是赢过 .env，
        # 同一份代码在本地和线上行为一致。
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env()

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")

# 不带默认值：环境变量缺失时在启动瞬间就崩，而不是静默用一个公开值跑起来
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

TORTOISE_ORM = {
    'connections': {
        'default': {
            # 'engine': 'tortoise.backends.asyncpg',  PostgreSQL
            'engine': 'tortoise.backends.mysql',  # MySQL or Mariadb
            'credentials': {
                'host': os.environ.get("DB_HOST", "127.0.0.1"),
                'port': 3306,
                'user': os.environ.get("DB_USER", "root"),
                # 和 SECRET_KEY 同样的道理：这两个值不能进仓库
                'password': os.environ["DB_PASSWORD"],
                'database': 'DotPub',
                'minsize': 1,
                'maxsize': 5,
                'charset': 'utf8mb4',
                "echo": False
            }
        },
    },
    'apps': {
        'models': {
            'models': ['models.user', "aerich.models","models.article","models.comment","models.interaction"],
            'default_connection': 'default',
        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}
