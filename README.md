# PyDocInCHM

## 0.关于本文
本文是PyDocInCHM的中文版自述文件。 The English version of this article is [README_en.md](README_en.md)


## 1.概述
PyDocInCHM是一个简单实用的 Python 程序，可以将 Python 官方文档从 HTML 格式转换为 CHM 格式，例如 python-3.11.9-docs-html.zip --> python-3.11.9-docs.chm。  
因为Python官方从3.11起不再提供CHM格式的文档，但是在Windows下CHM使用起来比原始HTML以及EPub都方便、高效，因此我开发了这个程序。  

如果你只是单纯想下载一个生成好的CHM文件，到这[里来](../../../PD-CHM)。  


## 2.技术特点
这是一个"学习作品", 是本人在Python学习过程中开发的第一个有实际用途的程序，在这个作品中我学习使用了如下一些Python编程技术:
* 利用BeautifulSoup、LXML库分析、修改HTML文件
* 调用Winodows下的动态链接库(DLL)
* Python日志功能的使用
* Python操作压缩文件(zip)
* 其它Python基本的文件操作，字符串处理功能

本程序的主入口在 src\html2chm.py， 手工运行请参考 run_script.bat

## 3.学习要求
为了理解，使用本源代码，你需要如下知识准备：
* 了解Microsoft HTML Help Workshop项目中的hhp,hhc,hhx文件结构及内容
* 熟悉HTML基本知识
* 熟悉Python语言

## 4.编译环境及第三方包
### 4.1 Python版本 
因为hha.dll只有32位版本，因此本程序要在32位Python下运行，我使用的是 Python 3.11.9  
当然你也可以不调用hha.dll, 而是安装Microsoft HTML Help Workshop后自己用hhc.exe来编译。  
这样就不再有32bit这个限制了。

### 4.2 第三方包
本程序用到了如下第三方Python包
* BeautifulSoup 4.12.3
* LXML 5.3.0
* Packaging 24.1

## 5.联系作者 
作者： 麦轲(Mykore)  
主页: http://www.mksjgj.com  
邮箱: mksjgj@qq.com  
QQ: 3073365368
