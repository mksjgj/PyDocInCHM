"""
  html2chm.py
  Python从3.11起不再随 Windows安装包提供文档的 CHM 版本, 本脚本的目标是将html格式修改打包成chm格式

  1.参照之前的chm版本(反编译后)
  2.之前的 epub2chm.py 是用epub版本来转换, 但效果不好, 还是直接从 html版本来

升级策略:
  对比html文档, 确定 改动部分, 再调整代码



History
2024-09-27: created
2024-10-04: 从html直接转换来的版本基本OK, 看看一些地方要不要再加目录

"""
import os.path
import re
import shutil
import zipfile
# import glob
from npchmutil import *
from hhawrap import *
from packaging.version import Version
from nipow import *


class Html2Chm:
    CHM_UTILS = 'chm_utils'  # 这是chm相关资源
    CHM_DIR: str = 'PydocCHM'  # 这是chm的源及默认目的目录, 按版本存放, 形如: PydocCHM\3.11.1,  PydocCHM\3.9.12
    PAGE_CS: str = 'cp1252'  # chm中的正文页面的字符集 page charset

    def __init__(self, html_zip: str, chm_fn: str = ''):
        applog.info(f'src_zip = {html_zip}')
        super().__init__()
        self.src_zip = html_zip  # source, 如: R:\python-3.11.9-docs-html.zip
        self._get_doc_ver()     # 当前处理的文档对应的python版本
        self.dest_chm = chm_fn   # target, 如: R:\python3119.chm
        if self.dest_chm == '':
            ph = Path(self.CHM_DIR, f'python-{self.doc_ver}-docs.chm').resolve()
            self.dest_chm = str(ph)  # 默认chm都输出到 PydocCHM 下
        self.handled_html = {}  # 已经处理了的html文件

    def _get_doc_ver(self):
        """从源html文件名(如 python-3.11.9-docs-html.zip)中提取文档版本号"""
        stm = Path(self.src_zip).stem
        m = re.match(r'python-(\d+\.\d+\.\d+)-docs', stm, re.I)
        assert m is not None, "只接受原始的html文件, 如 'python-3.11.9-docs-html.zip' "
        self.doc_ver = Version(m.group(1))  # 当前处理的文档对应的python版本, e.g.: 3.11.9
        self.doc_root = os.path.join(self.CHM_DIR, str(self.doc_ver))  # 当前版本文档的根目录, 如: PydocCHM\3.11.9


    def cvt_fn_href(self, src: str, to_href=True):
        """
        在 filename 与 href 之间转换:
            filename: 指的是 PydocCHM 下的文件的相对路径, 它们相对于项目根目录(PyDocInCHM)的, 主要用在文件操作中, 如: 打开, 复制, 删除等,
                如: PydocCHM\3.11.9\whatsnew\index.html
            href: 指的是 chm 文件中对文件的引用, 它们是相对于本版本的根目录(如: ...PyDocInCHM\PydocCHM\3.11.9, 也就是 doc_root)的,
                如: whatsnew/index.html, 主要用在 ChmHhcItem.Local 中
        :param src: 源, 是一个文件名(filename)或一个超引用(href), 由 to_ref的值决定
        :param to_href:
        :return:
        """
        if to_href:  # file name to href
            return os.path.relpath(src, self.doc_root).replace('\\', '/')
        else:  # href to file name, 如果src中有#也能正常处理,会被当成文件名的一部分
            return os.path.join(self.doc_root, src).replace('/', os.path.sep)

    def upack_html_zip(self):
        """
        Python发布的html文档zip包,根目录下还包有一个目录,名字与zip包名字一样,即:
          python-3.11.9-docs-html.zip\python-3.11.9-docs-html\*.*
          因此不能使用 extractall

        """
        # 先删除目录及其所有内容, 重新创建目录, 相当于清空工作目录
        shutil.rmtree(self.doc_root, ignore_errors=True)
        os.makedirs(self.doc_root, exist_ok=True)

        # with zipfile.ZipFile(self.src_html, 'r') as zip_ref:
        #     zip_ref.extract(r'python-3.11.9-docs-html/*.*', self.WORK_DIR)

        sub_dir = Path(self.src_zip).stem + '/'  # zip中套的子目录, 目前是与文件名相同的
        sub_dir = sub_dir.lower()  # 变成小写
        sub_dir_len = len(sub_dir)
        with zipfile.ZipFile(self.src_zip, 'r') as zip_ref:  # 打开zip
            for zip_info in zip_ref.infolist():  # 遍历ZIP文件中的每个文件和目录
                old_path = zip_info.filename  # zip中item的名字
                if len(old_path) > sub_dir_len and old_path.startswith(sub_dir):  # 检查文件或目录是否在指定的子目录中
                    # 去掉前面多嵌套的部分, 例如: 由 python-3.11.9-docs-html/genindex.html  变成 genindex.html
                    zip_info.filename = old_path[sub_dir_len:]
                    zip_ref.extract(zip_info, self.doc_root)  # 提取文件或目录到指定位置

    def adjust_files(self):
        """
        原始 python-3.11.09-docs-html.zip 解压后有一些制作chm不再需要的垃圾(大多是 Sphinx 相关的), 要删除
        同时拷入需要的文件

        最后更新日期 2024-09-27, base on python-3.11.09.docs-html.zip
            _sources  这是个目录
            _static\*.js
            _static\glossary.json 为 search.html 所使用,
            _static\opensearch.xml
            .buildinfo
            objects.inv
            search.html
            searchindex.js

        """
        shutil.rmtree(Path(self.doc_root, '_sources'), ignore_errors=True)  # 删除

        for js_file in Path(self.doc_root, r'_static').glob('*.js'):  # 删除所有 js 文件
            js_file.unlink()

        for fn in [r'_static\glossary.json', r'_static\opensearch.xml', '.buildinfo', 'objects.inv', 'search.html',
                   'searchindex.js']:  # 其它零散文件
            Path(self.doc_root, fn).unlink(True)

        shutil.copy(Path(self.CHM_UTILS, 'Fts_stop_list.stp'), self.doc_root)  # 复制 Fts_stop_list.stp

        about_chm = Path(self.CHM_UTILS, 'about this CHM.htm').read_text('utf-8')
        about_chm = about_chm.format(get_utc_ts(), os.path.basename(self.src_zip))
        Path(self.doc_root, 'about this CHM.htm').write_text(about_chm, 'utf-8')


    def add_desc_fr_list(self, prt_chap: ChmHhcItem, prt_fn: str, ignore_no_list=True):
        """
        给父目录增加子目录, 子条目来自各父条目对应html文件内的 toctree-l1 或者 sphinxsidebarwrapper
        :param prt_chap: 父条目(chm中的目录条目)
        :param prt_fn: 父条目对应的 html 文件, 如: PydocCHM\3.11.9\whatsnew\index.html

        :param ignore_no_list
        :return:
        """
        bm_host_href = ''  # 书签所在文件的引用, 如: whatsnew/3.11.html

        def add_bm_chap(start_hhc: ChmHhcItem, start_ul: bs4.Tag):
            """
            将 sphinxsidebarwrapper 中代表页内书签的 ul 转换成 chm中的章节目录的下级目录
            :param start_hhc: chm 的目录条目
            :param start_ul: bs4.Tag, html中对应的 ul
            :return:
            """
            for li in start_ul.find_all('li', recursive=False):
                tag_a = li.find('a', class_='reference internal')
                href_ = bm_host_href + tag_a.get('href')  # 如: whatsnew/3.11.html#summary-release-highlights
                tit = get_tag_text(tag_a)
                sub_hhc = start_hhc.add_child(tit, href_)
                if li.ul:  # 还有下级
                    add_bm_chap(sub_hhc, li.ul)

        prt_ph = Path(prt_fn)
        soup = load_soup(prt_ph, 'utf-8', True)
        peer_dir = os.path.dirname(prt_fn)  # 当前 父条目 对应的文件所在目录, e.g.: PydocCHM\3.11.9\whatsnew
        if toctree := soup.body.find('div', class_='toctree-wrapper compound'):  # 有指向其它文件的纲要列表
            for tag_li in toctree.find_all('li', class_="toctree-l1"):
                href = tag_li.find('a').get('href')  # e.g.: 一般指向同目录下的文件, 如: 3.11.html
                ch_fn = os.path.join(peer_dir, href)   # e.g.: PydocCHM\3.11.9\whatsnew\3.11.html, 指向文件
                href = self.cvt_fn_href(ch_fn, True)  # 位于父条目所在目录 e.g.: whatsnew/3.11.html
                ch_chap = prt_chap.add_child(get_tag_text(tag_li.a), href)
                if '#' not in href:  # 只有指向文件的 toctree-l1 条目才有可能有下级
                    self.add_desc_fr_list(ch_chap, ch_fn, ignore_no_list)
        elif ssb_wrapper := soup.body.find('div', class_='sphinxsidebarwrapper'):  # 构建文内书签构成的子章节
            # 找到页内书签列表总标题, 有些页面没有
            if a := ssb_wrapper.find('a', class_='reference internal', href="#"):  # 这是 总标题, 如 "What’s New In Python 3.11"
                bm_host_href = prt_chap.Local  # 如: whatsnew/3.11.html, 注意, 这个值在add_sub_chap的递归过程中是不变的
                if (start_ul := a.find_next_sibling()) and start_ul.name == 'ul':
                    add_bm_chap(prt_chap, start_ul)  # 以总标题的直接下级ul作为 prt_chap 目录的下级
                elif (start_ul := a.parent.parent) and start_ul.name == 'ul':  # 如果没有下级ul, c-api\sys.html 是这种情况
                    add_bm_chap(prt_chap, start_ul)  # 如果总标题下没有ul则以它所在的ul为起点
        elif not ignore_no_list:
            raise LookupError(f'no toctree-wrapper or sphinxsidebarwrapper found in {prt_fn}')

        self.html_comm_adjust(soup, prt_ph, True)

    def add_l1_gloss_sub(self, l1_gl: ChmHhcItem, gl_ph: Path):
        """
        增加 glossary.html 下的子目录条目
        :param l1_gl: glossary 对应的 level 1 菜单
        :param gl_ph: 就是 PydocCHM\3.11.9\glossary.html
        :return:
        """
        for char in range(64, 91):  # 增加术语分组节点: @,A ~~ Z, 作为 level 2 目录
            l1_gl.add_child(chr(char), '')

        soup = load_soup(gl_ph, 'utf-8', True)
        for dt in soup.find_all('dt'):  # 每个dt是一个术语
            # tit =  dt.code.span.string
            href = dt.a['href']
            dt.a.decompose()  # 不再需要这个a标签
            tit = ''.join(dt.stripped_strings)
            # tit = tit[:len(tit)-1]  # 最后一个字符是 ¶, 不要

            # 根据首字母查找所属的group, 找不到的都放第一组, '@'组
            first_let = tit.strip(' _').upper()[0]
            if not (group_item := l1_gl.find_child(first_let)):
                group_item = l1_gl.Children[0]
            group_item.add_child(tit, l1_gl.Local + href)

        # 分组节点的href设为与第一个子节点相同
        for group_item in l1_gl.Children:
            if group_item.Children:
                group_item.Local = group_item.Children[0].Local

        self.html_comm_adjust(soup, gl_ph, True)

    def add_l1_pymod_sub(self, l1_pymod: ChmHhcItem, pymod_ph: Path):
        """
        给 py-modindex.html 对应的一级章节 增加下级菜单, 即按首字母的分组菜单
        :param l1_pymod: py-modindex.html 对应的一级目录
        :param pymod_ph: PydocCHM\3.11.9\py-modindex.html
        :return:
        """
        soup = load_soup(pymod_ph, 'utf-8', True)
        soup.delete('div', class_='modindex-jumpbox')  # 有了目录条目,这个不要了

        tab_it = soup.find('table', class_='indextable modindextable')
        l1_grp = l2_grp = None  # ChmHhcItem
        pymod_href = self.cvt_fn_href(str(pymod_ph), True)
        for tr in tab_it.find_all('tr', recursive=False):  # 逐行处理
            if tr.has_attr('class') and tr['class'][0] == 'cap':  # 开始一个新的一级分组, 按首字母
                l1_grp = l1_pymod.add_child(get_tag_text(tr).upper(), pymod_href+'#'+tr['id'])  # 一级分组
            elif tag_code := tr.find('code', class_="xref"):  # 一个模块
                if tag_a := tag_code.find_parent('a'): href = tag_a.get('href')
                else: href = ''
                # assert tag_a is not None, get_tag_text(tag_code)
                if tr.has_attr('class') and (tr['class'][0]).startswith('cg-'):  # 二级分组成员, 子模块
                    l2_grp.add_child(get_tag_text(tag_code), href)
                else:
                    l2_grp = l1_grp.add_child(get_tag_text(tag_code), href)  # 一级分组成员, 同时也可以作为二级分组

        self.html_comm_adjust(soup, pymod_ph, True)

    def html_comm_adjust(self, soup: BeautifulSoup, dest_ph, rec_path: bool):
        """
        对html页面进行公共的处理
        :param soup:
        :param dest_ph:
        :param rec_path: 要不要记录当前文件为已经处理
        :return:
        """
        # if self.seg_debug:
        #     return
        applog.info(f'{dest_ph=}')

        head = soup.head
        new_tag = soup.new_tag('meta', attrs={'http-equiv': "X-UA-Compatible", 'content': "IE=edge"})
        head.insert(0, new_tag)

        for link_ss in head.find_all('link', rel='stylesheet'):  # 3个, 去掉 stylesheet 中的查询串
            href = link_ss['href']
            if (ipos := href.find('?')) != -1:
                link_ss['href'] = href[:ipos]

        head.delete_all('script')  # 8 个
        head.delete_all('link', rel='search')  # 2个

        # 将title中的多余的 '— Python 3.11.9 documentation' 去掉
        tit = head.title.string.rsplit('—', 1)[0].strip()
        head.title.string = tit

        body = soup.body
        body.delete('div', class_='mobile-nav')  # 1个
        body.delete_all('div', class_='related', role="navigation")  # 2个
        if wrap_ := body.find('div', class_='bodywrapper'):  # 脱掉 <div class="bodywrapper">
            wrap_.unwrap()
        body.delete('div', class_='sphinxsidebar')  # 1个
        body.delete('div', class_='footer')  # 1个
        body.delete_all('a', class_="headerlink")  # 各级标题后面的锚点,个数不定,显示为 ¶

        html_src = str(soup)
        html_src = re.sub(r'<meta *charset *= *"utf-8" */>', f'<meta charset="{Html2Chm.PAGE_CS}" />',
                          html_src, count=1, flags=re.I)

        # 转义非ascii字符, 但 <title> 不转义, ref: npchmutil.py
        html_src = html_esc_ex(html_src, False, True)
        pos_1 = html_src.find('<title>')
        pos_2 = html_src.find('</title>')
        tit = html_esc_ex(tit, True, False)
        src_ = html_src[:pos_1] + '<title>' + tit + html_src[pos_2:]
        dest_ph.write_text(src_, Html2Chm.PAGE_CS)

        if rec_path:
            self.handled_html[self.cvt_fn_href(dest_ph, True)] = None  # 只需要保存 文件名

    def adjust_remains_html(self):
        """ 对剩下的html页面执行公共调整 """
        p = Path(self.doc_root).resolve()
        for ph in p.rglob('*.html'):
            rel_fn = str(ph.relative_to(p)).replace(os.sep, '/')
            if rel_fn not in self.handled_html:
                soup = load_soup(ph, 'utf-8', True)
                self.html_comm_adjust(soup, ph, False)

    def gen_hhp_file(self) -> str:
        """
        根据模板生成 CHM 的 *.hhp 文件
        hpp中其实没有必要将所有文件列出来, 如果是被已有html引用了的文件, 会被自动包进来

        """

        # print(root_chap_dict)
        # 生成hpp文件
        hpp_src = Path(Html2Chm.CHM_UTILS, 'pythondoc.hhp').read_text(Html2Chm.PAGE_CS)  # hhp模板
        hhp_files = []

        len_ = len(self.doc_root) + 1  # 去掉开头的 'PydocCHM\3.11.9'
        hhp_files += [str(f)[len_:] for f in Path(self.doc_root, '_images').rglob('*.*')]
        hhp_files += [str(f)[len_:] for f in Path(self.doc_root, '_static').rglob('*.*')]

        hhp_files += self.handled_html.keys()

        hpp_src = hpp_src.format(self.dest_chm, self.doc_ver.__str__(), '\n'.join(hhp_files))
        hpp_fn = os.path.join(self.doc_root, 'pythondoc.hhp')
        Path(hpp_fn).write_text(hpp_src, Html2Chm.PAGE_CS)

        return hpp_fn

    def gen_hhc_file(self):
        """
        本chm文档的根目录,共15条,即 15个根章节(level 1 chap),根据 index.html 整理,参考了之前的chm版本及Delphi CHM文档的结构,
        第1章是文档总图, 它下面没有子章节; 对应 index.html
        第2~11章 各自对应一个子目录, 目录下有一个index.html, 这个index.html作为本章节的总纲,
            以这个文件开始,构建下级子菜单:
                如果它内含一个 <div class="toctree-wrapper compound">,则本文件主要用作提纲, 其下<li class="toctree-l1"> 作为下级目录,
                    这些<li class="toctree-l1">一般也是指向另外一个文件的
                如果它内含一个 sphinxsidebarwrapper,则本文件主要是展现具体内容的, sphinxsidebarwrapper中列出了本内容文件的书签,
                    这些就是chm文件的最细目录条目了

        distributing/index.html 已无具体内容, 不设目录

        第12章  术语表, 目录其实是按首字母分组而已
        第13章  模块表, 目录也是按首字母分组而已
        第14章, 'Project information'本身没有对应的文件, 归集了一些 补充性质的文件

        基于 python-3.11.9-docs-html
        :return:
        """
        self.handled_html.clear()  # 已经处理了的html文件
        ultra_root = ChmHhcItem(level=0, name='', local='')

        def add_l1_chap(chap_info_str, def_add_sub) -> ChmHhcItem:  # 增加顶层(level 1)目录
            name_, local_ = chap_info_str.split('=', 1)
            applog.debug(f'{local_}')
            l1_chap_ = ultra_root.add_child(name_, local_)
            if def_add_sub:  # 执行默认的增加下级操作
                fn = self.cvt_fn_href(l1_chap_.Local, False)
                self.add_desc_fr_list(l1_chap_, fn)
            return l1_chap_

        add_l1_chap(r'Python documentation total map=index.html', False)  # 1,第一章
        add_l1_chap(r"What’s new=whatsnew/index.html", True)  # 2
        add_l1_chap(r'Setup and usage=using/index.html', True)  # 3
        add_l1_chap(r'Tutorial=tutorial/index.html', True)  # 4
        add_l1_chap(r'Language reference=reference/index.html', True)  # 5
        add_l1_chap(r'Library reference=library/index.html', True)  # 6
        add_l1_chap(r'Installing modules=installing/index.html', True)  # 7
        add_l1_chap(r'Extending and embedding=extending/index.html', True)  # 8
        add_l1_chap(r'Python/C API=c-api/index.html', True)  # 9
        add_l1_chap(r'HOWTOs=howto/index.html', True)  # 10
        add_l1_chap(r'FAQs=faq/index.html', True)  # 11

        l1_chap = add_l1_chap(r'Glossary=glossary.html', False)  # 12
        self.add_l1_gloss_sub(l1_chap, Path(self.doc_root, l1_chap.Local))

        l1_chap = add_l1_chap(r'Global module index=py-modindex.html', False)  # 13
        self.add_l1_pymod_sub(l1_chap, Path(self.doc_root, l1_chap.Local))

        # 下面这几个文件性质相近, 且使用频率不高, 归在一起, 原 python31010.chm 是分开的
        l1_chap = add_l1_chap(r'Project information=', False)  # 14,  使用 index.html 中的分组名字
        l1_chap.add_child('About the documentation', 'about.html')  # 较为简单,无需再增加下级目录

        l2_chap = l1_chap.add_child('History and license', 'license.html')  # 有 sphinxsidebarwrapper
        self.add_desc_fr_list(l2_chap, self.cvt_fn_href('license.html', False))

        l1_chap.add_child('Copyright', 'copyright.html')  # 有 sphinxsidebarwrapper, 但无本文的bookmark

        l2_chap = l1_chap.add_child('Reporting issues', 'bugs.html')  # 有 sphinxsidebarwrapper
        self.add_desc_fr_list(l2_chap, self.cvt_fn_href('bugs.html', False))

        add_l1_chap('about this CHM=about this CHM.htm', False)  # 加上CHM说明

        # 目录列表写入 *.hhc 文件
        src_list = []
        ultra_root.output_src(src_list, 0)
        hhc_src = Path(self.CHM_UTILS, 'pythondoc.hhc').read_text(self.PAGE_CS)  # hhc模板
        hhc_src = hhc_src.format('\n'.join(src_list))
        Path(self.doc_root, 'pythondoc.hhc').write_text(hhc_src, self.PAGE_CS)

    def convert(self):
        # self.upack_html_zip()
        # 删除无用文件
        self.adjust_files()

        # hpp_fn = self.gen_hhp_file()
        # ChmHhc.gen_hhc_file(self)
        # ChmHhk.gen_hhk_file(self)
        #
        # self.trans_xhtml()
        # HhaWrap.compile_hhp_ex('hha.dll', hpp_fn)

def main():
    applog.setLevel(logging.WARNING)  #
    h2c = Html2Chm(
        # r'F:\DevKit\Python\Core Package\V3.11.X\V3.11.09\python-3.11.9-docs-html.zip'
        # r'F:\DevKit\Python\Core Package\V3.11.X\V3.11.10\python-3.11.10-docs-html.zip'
    )
    h2c.seg_debug = False  # 分段调试

    h2c.upack_html_zip()

    h2c.adjust_files()

    h2c.gen_hhc_file()
    # with Path(r'user\adjusted.txt').open('tw') as f:
    #     for line in h2c.handled_html:
    #         f.write(line+'\n')

    ChmHhk.gen_hhk_file(h2c.doc_root, h2c.PAGE_CS)
    # shutil.copy(r'chm_utils\pythondoc_empty.hhk', r'PydocCHM\3.11.9\pythondoc.hhk')

    # with Path(r'user\adjusted.txt').open('tr') as f:
    #     h2c.handled_html[f.readline()] = None
    h2c.adjust_remains_html()

    hpp_fn = h2c.gen_hhp_file()
    HhaWrap.compile_hhp_ex(r'chm_utils\hha.dll', hpp_fn)


if __name__ == '__main__':
    main()
