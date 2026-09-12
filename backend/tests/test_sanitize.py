"""正文清洗的自检，直接跑：  python tests/test_sanitize.py

这是安全路径——清洗一旦失效，任何注册用户都能往文章里塞脚本，
所有读到这篇文章的人都会中招。改过 clean_html 或白名单之后务必跑一遍。

项目里没有 pytest，所以用裸 assert，不引入任何测试框架。
    （注意 assert 在 python -O 下会被去掉，别用 -O 跑这个文件）
"""

import sys
from pathlib import Path

# 允许从 backend/ 目录直接跑，把 backend/ 加进模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apis.article import clean_html


def main():
    # ---------- 危险内容必须被剥掉 ----------
    assert 'onerror' not in clean_html('<img src=x onerror="alert(1)">')
    # <script> 的标签和内容会一起消失
    assert clean_html('<script>alert(1)</script><p>ok</p>') == '<p>ok</p>'
    # 大小写变形挡得住（HTML 属性名不区分大小写，正则方案挡不住这个）
    assert 'onerror' not in clean_html('<IMG SRC=x ONERROR=alert(1)>')
    # javascript: 伪协议
    assert 'javascript:' not in clean_html('<a href="javascript:alert(1)">x</a>')

    # ---------- Quill 的格式必须留住，否则正文列表和对齐全废 ----------
    assert 'class="ql-align-center"' in clean_html('<p class="ql-align-center">居中</p>')
    assert 'data-list="bullet"' in clean_html('<li data-list="bullet">项</li>')
    # 普通正文不能被误伤
    assert clean_html('<p>正常段落</p>') == '<p>正常段落</p>'

    print('clean_html 自检通过')


if __name__ == '__main__':
    main()
