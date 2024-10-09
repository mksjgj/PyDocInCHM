"""
    nphtml.py
    nipow html utils 文本处理例程

2024-09-28: created
            将 html_esc_ex 由原来 epub2chm.py 移入


"""
from pathlib import Path
import html
import bs4
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone


def no_cp1252(char):
    try:
        # 尝试将字符编码为cp1252
        char.encode('cp1252')
        return False
    except UnicodeEncodeError:
        return True  # 如果编码失败，捕获异常并返回True

def html_esc_ex(orig_str, esc_html_sym, esc_non_ascii) -> str:
    """
    主要用于: 将所有大于127的字符按html规则进行转义成  &#12345; 形式

    天下霸唱,朱镕基 --> &#22825;&#19979;&#38712;&#21809;,&#26417;&#38229;&#22522;
    要进行这个转换的原因是 EPub是utf-8格式的, 其中有一些特殊字符, cp1512 中不支持, 要转义

    这个算法是不高效的,因为在python内部, 通过 PyUnicode_KIND 已经知道有没有非ascii字符,
    也就是讲,大部分情况下没有必要一个个字符进行验证

    """
    rst = orig_str

    # 执行html标准转义: 处理 <, >, & 等特殊字符, 功能相当于 html.escape, 但在处理 双引号与单引号时有点区别,
    # 主要为了规避 hha.dll 的bug, 连续多个 &#x27; 会让 hha.dll 出错
    if esc_html_sym:
        rst = html.escape(rst, False)  # 只处理 < > 等特殊符号
        rst = rst.replace('"', '&quot;')  # 双引号
        rst = rst.replace("'", '&apos;')  # 单引号, &#x27

    if esc_non_ascii:  # 大于127的字符转义
        str_list = []
        begin = -1
        for i in range(0, len(orig_str)):
            char = rst[i]
            if ord(char) > 127:  # 非ascii字符且不能转换成 cp1252
                if begin > -1:  # 前面有纯ascii的子串
                    str_list.append(rst[begin:i])
                    begin = -1
                str_list.append(f'&#{ord(char)};')  # 十进制
                # rst.append(f'&#x{ord(rst[i]):x};')  # 十六进制
            elif begin == -1:
                begin = i  # 纯ascii的子串开始
        if begin == 0:
            return rst  # 未出现过非ascii字符
        elif begin > 0:  # 剩余未处理的纯ascii的子串
            str_list.append(rst[begin::])
        rst = ''.join(str_list)

    return rst


def output_nested_src(str_list, src, first_ident=1, mid_ident=-1, last_ident=-1):
    """
    输出嵌套结构的html源代码: 使用指定缩进
    如果只有一行,视为first, 如果只有两行, 视为 first 与 last
    """
    if mid_ident == -1:
        mid_ident = first_ident+1
    if last_ident == -1:
        last_ident = first_ident

    src_list = [s.strip() for s in src.splitlines()]
    last_idx = len(src_list) - 1
    for idx, s in enumerate(src_list):
        match idx:
            case 0: ident = first_ident
            case last_idx_ if last_idx_ == last_idx: ident = last_ident
            case _: ident = mid_ident
        str_list.append('  '*ident + s)


def get_direct_text(tag: bs4.Tag) -> str:
    """
    获取标签下的直接文本,不包括子标签内的文本
    """
    rst: str = ''
    for child in tag.children:
        if isinstance(child, bs4.NavigableString):
            rst += ' '.join(child.stripped_strings)  # 各个串之间加个空格
    # return html.escape(rst)
    return rst


def get_tag_text(tag_: bs4.Tag, sep='') -> str:
    return sep.join(tag_.stripped_strings)

def prettify_html(src_fn, dest_fn=None):
    if dest_fn is None:
        dest_fn = src_fn
        dest_fn = dest_fn.replace('.html', '_pret.html')
        # dest_fn = 'r:\\' + os.path.basename(src_fn)
    elif dest_fn == '=':  # 原位替换
        dest_fn = src_fn

    html_src = Path(src_fn).read_text('utf-8')
    soup = BeautifulSoup(html_src, 'html.parser')
    html_src = soup.prettify()  # minimal(default), html, xml
    Path(dest_fn).write_text(html_src, 'utf-8')



def delete(self: bs4.Tag, name=None, attrs={}, recursive=True, string=None, **kwargs) -> int:
    """
    查找并删除下级tag
    动态附加到 bs4.Tag 上
    """
    if tag_ := self.find(name, attrs, recursive, string, **kwargs):
        tag_.decompose()
        return 1
    else:
        return 0

def delete_all(self: bs4.Tag, name=None, attrs={}, recursive=True, string=None, limit=None, **kwargs) -> int:
    """
    查找并删除下级tag
    动态附加到 bs4.Tag 上
    """
    rs = self.find_all(name, attrs, recursive, string, limit, **kwargs)
    cnt = len(rs)
    for tag_ in reversed(rs):  # 倒过来删除可靠点
        tag_.decompose()
    return cnt


def load_soup(src_path: Path, encoding=None, is_html: bool = True) -> BeautifulSoup:
    src_ = src_path.read_text(encoding)
    fmt_ = 'lxml' if is_html else 'lxml-xml'
    return BeautifulSoup(src_, fmt_)


# 动态增加两个方法,猴子方法, 慎用, IDE不能提供代码提示功能
# 应只对第三方代码, 不方便继承的情况下使用
bs4.Tag.delete = delete
bs4.Tag.delete_all = delete_all


def get_utc_ts():
    """
    获取当前时间, 以带时区的格式显示
    :return:
    """
    # 获取当前的UTC时间
    utc_now = datetime.now(timezone.utc)

    # 创建一个+8时区的对象
    # tz_china = timezone(timedelta(hours=8))

    # 转换为+8时区的时间
    # local_time = utc_now.astimezone(tz_china)
    # formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S %z')

    # 将时间格式化为字符串
    return utc_now.strftime('%Y-%m-%d %H:%M:%S %z')



def main():
    prettify_html(r'D:\DevPy\PycProj\PyDocInCHM\PydocCHM\library\text.html')
    # prettify_html(r'D:\DevPy\PycProj\PyDocInCHM\PythondocsCHM\glossary.html', '=')

    # html = '<a href="glossary.html#term-0"><strong>&gt;&gt;&gt;</strong></a>'
    # soup = BeautifulSoup(html, 'html.parser')
    #
    # print(soup.a.string)

if __name__ == '__main__':
    main()
