"""hhawrap.py
    a python wrapper for the hha.dll API

    注意: hha.dll只有32bit版本,因此本类只能在32位Python下使用

history:
2024-09-20: create, 从 pychm 中 的 chm.py 进行移植, 同时参考 delphi 代码 ukEBookGen.pas


"""

from ctypes import *
from nipow import *

# tow call back function
HhaCallBack = WINFUNCTYPE(c_bool, c_char_p)


def hhacb_log(log_msg):
    """
    HHA CallBack for log
    :param log_msg:
    :return:
    """
    applog.debug(log_msg)
    # print(log_msg)
    return True


def hhacb_prog(prog_msg):
    """
    HHA CallBack for progress
    :param prog_msg:
    :return:  1 to continue, 0 to abort.
    """
    # applog.debug( prog_msg )
    # print(prog_msg)
    return True


class HhaWrap:
    """
    a wrapper for the hha.dll API
    """
    def __init__(self, hha_dll_fn):
        super().__init__()

        import struct
        size = struct.calcsize('P')  # 通过指针的字节数来知道是 32位还是64位系统
        assert size == 4, 'hha.dll只有32bit版本,因此本类只能在32位下使用'

        self.hha_dll_fn = hha_dll_fn
        self.ole32_handle = oledll.LoadLibrary('ole32.dll')
        self.ole32_handle.CoInitialize(0)

        # 这是准备工作的核心, 引出 HHA_CompileHHP
        self.hha_dll = windll.LoadLibrary(hha_dll_fn)
        self.hha_dll.HHA_CompileHHP.argtypes = [c_char_p, HhaCallBack, HhaCallBack, c_void_p]
        self.hha_dll.HHA_CompileHHP.restype = c_bool

    def __del__(self):
        # windll.UnloadLibrary(self.hha_dll)  # 不需要显示释放, python自动处理
        self.ole32_handle.CoUninitialize()
        # oledll.UnloadLibrary(self.ole32_handle) # 不需要显示释放, python自动处理
        # super().__del__()

    def compile_hpp(self, hpp_fn) -> bool:
        """
        编译指定的 chm 项目, *.hpp
        :param hpp_fn: chm 项目文件
        :return:
        """
        null_ptr = c_void_p()
        hpp_fn = hpp_fn.encode('ansi')
        rst = self.hha_dll.HHA_CompileHHP(hpp_fn, HhaCallBack(hhacb_log), HhaCallBack(hhacb_prog), null_ptr)
        return rst

    @staticmethod
    def compile_hhp_ex(hha_dll_fn, hpp_fn) -> bool:
        """
        一次性使用
        :param hha_dll_fn:
        :param hpp_fn:
        :return:
        """
        hha_wrap = HhaWrap(hha_dll_fn)
        return hha_wrap.compile_hpp(hpp_fn)


if __name__ == '__main__':
    HhaWrap.compile_hhp_ex(r'chm_utils\hha.dll', r'PydocCHM\3.11.9\pythondoc.hhp')
