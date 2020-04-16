# -*- coding:utf-8 -*-


class StrUtil:
    # 字符串是否为空
    @staticmethod
    def is_empty(str_in):
        return str_in is None or len(StrUtil.trim(str_in)) == 0

    # 去除空格和换行符
    @staticmethod
    def trim(str_in):
        if len(str_in) == 0:
            return ''
        if str_in[len(str_in) - 1:] == '\n':
            return StrUtil.trim(str_in[:len(str_in) - 1])
        if str_in[len(str_in) - 1:] == '\r':
            return StrUtil.trim(str_in[:len(str_in) - 1])
        if str_in[:1] == ' ':
            return StrUtil.trim(str_in[1:])
        elif str_in[-1:] == '':
            return StrUtil.trim(str_in[:-1])
        else:
            return str_in
