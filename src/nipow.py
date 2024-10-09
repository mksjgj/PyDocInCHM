"""
  nipow.py
  这是应用级别的全局代码与全局变量

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0


History
2024-09-04: create
2024-09-18: 定义 Nipow 类, 用于收纳全局变量

"""
import logging
import configparser

class Nipow:
    # 项目名字
    base_proj_name = 'PyDocInCHM'

    # 全局日志实例
    nplogger_name = 'nipow_logger'
    nplogger_filename = fr'.\user\{base_proj_name}.log'

    # 全局ini文件对象
    npinicfg_filename = fr'.\user\{base_proj_name}.ini'


# 设置日志的基本配置
logging.basicConfig(filename=Nipow.nplogger_filename, style='{', level=logging.INFO, datefmt='%H:%M:%S',
                    format='{asctime} {funcName}: {message}')
applog = logging.getLogger(Nipow.nplogger_name)
# applog.addFilter( logging.Filter(name=nplogger_name) )

applog.info('\r\n')
applog.info('First log')


class NpConfigParser(configparser.ConfigParser):
    def update_file(self):
        """ 将ini保存到文件中去 """
        with open('example.ini', 'w') as configfile:
            self.write(configfile)


# 创建一个ConfigParser对象
appini = NpConfigParser()
appini.read(Nipow.npinicfg_filename)


def main():
    applog.info('log from nipow.py')


if __name__ == '__main__':
    main()
