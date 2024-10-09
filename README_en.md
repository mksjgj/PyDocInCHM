# PyDocInCHM

## 0.About this readme
This article is a readme for PyDocInCHM. 它的中文版为[README.md](README.md)

## 1. Overview

PyDocInCHM is a simple and practical Python program that can convert the official Python documentation from HTML format to CHM format, for example, `python-3.11.9-docs-html.zip --> python-3.11.9-docs.chm`.   
Since Python.org stopped providing CHM format documentation starting from version 3.11, and using CHM is more convenient and efficient than raw HTML or EPub on Windows, I developed this program.  
The comments in this program are mainly in Chinese, and I believe machine translation should be sufficient for you to understand them. If you feel that some translations need to be confirmed, no problem, please contact me according to the contact information at the end of this file, but I can only provide some assistance with English translation.  
  
If you just want to download a generated CHM file, go [here](../../../PD-CHM)

## 2. Technical Features

This is a 'learning work', the first practical program I developed during my Python learning. In this work, I learned to use the following Python programming techniques:  
- Using the BeautifulSoup library to analyze and modify HTML files
- Calling dynamic link libraries (dll) on Windows
- Using Python logging functionality
- Python operations on compressed files (zip)
- Other basic file operations and string processing functions in Python  

The main entrance of this program is in src\html2chm.py, please refer to run_script.bat for manual execution

## 3. Learning Requirements

To understand and use this source code, you need the following knowledge:
- Understanding the structure and content of hhp, hhc and hhx files in the Microsoft HTML Help Workshop project
- Familiarity with basic HTML knowledge
- Familiarity with the Python language

## 4. Compilation Environment and Third-party Packages

### 4.1 Python Version

Since hha.dll is only available in 32-bit version, this program needs to run under 32-bit Python, and I used Python 3.11.9. Of course, you can also avoid calling hha.dll by installing Microsoft HTML Help Workshop and using hhc.exe to compile, which eliminates the 32-bit limitation.

### 4.2 Third-party Packages

This program uses the following third-party Python packages:

- BeautifulSoup 4.12.3
- LXML 5.3.0
- Packaging 24.1

## 5. Contact Author MyKore
- Author: MyKore 
- home page: http://www.mksjgj.com
- Email: mksjgj@qq.com
- QQ: 3073365368
