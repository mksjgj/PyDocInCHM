"""npchmutil.py
    nipow CHM utils

    关于CHM中对cp1252的支持:
    <title>的文字不要转义(即写成 &#1234;形式),能正常支持 cp1252 所有字符, 转义之后"搜索"页显示的主题不正常
    hhc文件中的目录名字不要转义,能正常支持 cp1252 所有字符, 转义之后"目录"页显示不正常
    但是其它地方的要转义, 否则显示不正常, 特别是正文, 不转义显示不正常, 尽管是cp1252字符

    &#8217; 形状类似单引号(’)
    &#8211; 短破折号(–)
    &#8212; 长破折号(—)

2024-09-28: created
            将 ChmHhcItem, ChmHhk 由原来 epub2chm.py 移入


"""
import os
from typing import Self
from nphtml import *


class ChmHhcItem:
    """
    本类代表一个 CHM 的目录文件 *.hhc 中的一个目录条目,
    ref: Html2Chm.gen_hhc_file

    """
    def __init__(self, level, name, local):
        super().__init__()
        self.level = level  # 层级, 为其父条目层级加1
        self.Name = name    # 名字
        self.Local = local  # 指向的文件
        self.Children = list()  # 下级目录条目

    def add_child(self, name, local) -> Self:
        """增加下级目录条目"""
        ch_item = ChmHhcItem(level=self.level + 1, name=name, local=local)
        self.Children.append(ch_item)
        return ch_item

    def find_child(self, str_, by_name=True) -> Self:
        for ch_item in self.Children:
            match by_name:
                case True:
                    rst = ch_item.Name == str_
                case _:
                    rst = ch_item.Local == str_
            if rst:
                return ch_item
        return None

    def output_src(self, lines, ident) -> None:
        """
        输出本目录条目在 hhc 文件中的表现形式
        lines: a list
        """
        # ident = '  ' * self.level
        if self.Name:
            # 目录上没有非cp1252字符,因此可以不转义, chm viewer对 &#1234; 形式表示的字符支持不好
            itm_name = html_esc_ex(self.Name, True, False)
            this_item = f'''<LI> <OBJECT type="text/sitemap"> 
                    <param name="Name" value="{itm_name}"> 
                    <param name="Local" value="{self.Local}"> 
                </OBJECT>'''
            output_nested_src(lines, this_item, ident)
        if self.Children:
            output_nested_src(lines, '<UL>', ident)
            for ch_itm in self.Children:
                ch_itm.output_src(lines, ident+1)
            output_nested_src(lines, '</UL>', ident)


class ChmHhk:
    """
    代表CHM中的索引文件, *.hhk, 由EPub中的 genindex-all.xhtml 解析而来
    """
    @staticmethod
    def _output_base_li(file, base_li, ident):
        """
        一个基本关键字条目, 下有一个或多个出处:
            <li> <a href="library/cmd.html#index-0">in a command interpreter</a></li>
            <li><a href="library/fnmatch.html#index-2">in glob-style wildcards</a>,<a href="library/glob.html#index-1">[1]</a></li>

        :param file:
        :param base_li: 基本list item, 即它下面没有<ul>...</ul>
        :param ident:
        :return:
        """
        taga_list = base_li.find_all('a', recursive=False)  # 下面的anchor标签
        match len(taga_list):
            case 0:
                pass  # do noting, 一般不会出这种情况
            case 1:  # 只有一个a标签
                taga = taga_list[0]
                kw = get_tag_text(taga)
                assert len(kw) > 0, 'kw 不能为空, base_li:' + str(base_li)  # 为空会导致 hha.dll 出错
                kw = html_esc_ex(kw, True, False)
                src = f'''<LI> <OBJECT type="text/sitemap">
                        <param name="Keyword" value="{kw}">
                        <param name="Local" value="{taga['href']}">
                    </OBJECT>'''
                output_nested_src(file, src, ident)
            case _:  # 下有多个a标签
                kw = get_tag_text(base_li.a)  # 第一个a标签的文本作为关键字
                assert len(kw) > 0, 'kw 不能为空, base_li:' + str(base_li)  # 为空导致 hha.dll 出错
                kw = html_esc_ex(kw, True, False)
                part_kw = f'''<LI> <OBJECT type="text/sitemap">
                                <param name="Keyword" value="{kw}">'''
                output_nested_src(file, part_kw, ident, ident, ident + 1)
                for idx, taga in enumerate(taga_list):
                    a_src = f'''<param name="Name" value="[{idx}] {taga['href']}">
                                <param name="Local" value="{taga['href']}">'''
                    output_nested_src(file, a_src, ident + 1, ident + 1, ident + 1)
                output_nested_src(file, '</OBJECT>', ident)

    @staticmethod
    def _output_hhk_index(kw_li: bs4.Tag, file, ident):
        """
        hhk文件中一个关键字根据它出处的多少有多种情况, 详见笔记
        kw_li: genindex-all.xhtml 中table单元格内的顶层 li, 对应一个关键字
        """
        if kw_li.ul is not None:  # 有多个引用点,即有下级 <ul>...</ul>
            if kw_li.a is not None:  # 关键字本身带有一个链接, 即它下面有一个 a 标签, 如关键字 ", (comma)" 的情况, 大部分是不带的.
                ChmHhk._output_base_li(file, kw_li, ident)
            else:  # 下面没有 a 标签, 直接用的普通文本,即关键字本身点击不会跳转
                kw = get_direct_text(kw_li)  # 关键字文本
                assert len(kw) > 0  # 不能为空, 否则 hha.dll 出错
                kw = html_esc_ex(kw, True, False)
                part_kw = f'''<LI> <OBJECT type="text/sitemap">  
                            <param name="Keyword" value="{kw}">
                            <param name="See Also" value="{kw}">
                        </OBJECT>'''
                output_nested_src(file, part_kw, ident)
            # 下面的ul及其li, 一个li就是一个出处, 但有时一个li下有多个链接
            output_nested_src(file, '<UL>', ident)
            li_list = kw_li.ul.find_all('li', recursive=False)  # 这个关键字下的引用条目
            for base_li in li_list:
                ChmHhk._output_base_li(file, base_li, ident + 1)
            output_nested_src(file, '</UL>', ident)
        else:  # 有些关键字只有一个引用点, 因此 下面没有ul标签了
            ChmHhk._output_base_li(file, kw_li, ident)

    @staticmethod
    def gen_hhk_file(chm_src_dir, page_charset):
        """
        根据指定的 genindex-all.html 文件生成对应的 chm 的 hhk
        """
        # 取得 关键字 条目
        src_list = []
        output_nested_src(src_list, '<UL>', 0)
        soup = load_soup(Path(chm_src_dir, 'genindex-all.html'), 'utf-8', True)

        # 关键字索引按首字母分成28组，每组一个表格: Symbols、_、A ~ Z
        idx_tab = soup.body.find_all('table', {'class': 'indextable genindextable'})
        # print(len(idx_tab))
        for tab in idx_tab:
            for tr in tab.find_all('tr'):  # 每个表格内只有一行
                for td in tr.find_all('td'):  # 每行有两栏（列），
                    # 每栏内是一个<ul>...</ul>, 内有多个li, 每个li是一个关键字及其出处(引用点，一般有多个，放在一个ul内)
                    for li in td.ul.find_all('li', recursive=False):
                        # print(get_direct_text(li))
                        ChmHhk._output_hhk_index(li, src_list, 1)
        output_nested_src(src_list, '</UL>', 0)

        # 生成 pythondoc.hhk 文件
        hhk_src = Path(r'chm_utils\pythondoc.hhk').read_text(page_charset)
        hhk_src = hhk_src.format('\n'.join(src_list))
        hhk_fn = os.path.join(chm_src_dir, r'pythondoc.hhk')
        Path(hhk_fn).write_text(hhk_src, page_charset)
