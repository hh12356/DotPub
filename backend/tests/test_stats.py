"""看板趋势的两个纯函数自检，直接跑：  python tests/test_stats.py

横轴算错一天（13 天、或者顺序反了），图表不会报错，只会默默画错——
所以这里盯住三件事：天数、顺序、没数据的天补 0。

和 test_sanitize.py 一样用裸 assert，项目里没有 pytest。
    （assert 在 python -O 下会被去掉，别用 -O 跑这个文件）
"""

import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apis.admin import _series, _trend_axis


def main():
    axis = _trend_axis(date(2026, 9, 18), 14)

    # ---------- 横轴：天数、顺序、两端 ----------
    assert len(axis) == 14
    assert axis == sorted(axis), '横轴必须从早到晚，反了折线就是倒着画的'
    assert axis[0] == date(2026, 9, 5), '往前数 13 天才是 14 个点'
    assert axis[-1] == date(2026, 9, 18), '最后一个点必须是今天'

    # ---------- 补 0：没数据的天空着，不是被跳过 ----------
    assert _series(axis, Counter()) == [0] * 14
    # 数据落的位置要对（今天有 3 条 → 只有最后一位是 3）
    assert _series(axis, Counter({date(2026, 9, 18): 3})) == [0] * 13 + [3]
    assert _series(axis, Counter({date(2026, 9, 5): 2, date(2026, 9, 18): 1}))[0] == 2

    print('趋势横轴自检通过')


if __name__ == '__main__':
    main()
