# -*- coding:utf-8 -*-


# 字符串预处理模块，为分析器TimeNormalizer提供相应的字符串预处理服务
import re

NUM_MAP = {"零": 0, "0": 0, "〇": 0,
           "一": 1, "1": 1, "壹": 1,
           "二": 2, "2": 2, "两": 2, "贰": 2,
           "三": 3, "3": 3, "叁": 3,
           "四": 4, "4": 4, "肆": 4,
           "五": 5, "5": 5, "伍": 5,
           "六": 6, "6": 6, "陆": 6,
           "七": 7, "7": 7, "天": 7, "日": 7, "末": 7, "柒": 7,
           "八": 8, "8": 8, "捌": 8,
           "九": 9, "9": 9, "玖": 9, }


class Preprocessor:
    # 删除一字符串中所有匹配某一规则字串 可用于清理一个字符串中的空白符和语气助词
    @staticmethod
    def del_keyword(str_in, rules):
        pattern = re.compile(rules)
        return pattern.sub('', str_in)

    # 不完整的中文数字，比如 “五万二”
    @staticmethod
    def abbreviation_match(pattern, str_target, unit, unit_num):
        def split_replace(match):
            str_in = match.group()
            s = str_in.split(unit)
            num = 0
            if len(s) == 2:
                num += Preprocessor.word_to_num(s[0]) * unit_num * 10 + Preprocessor.word_to_num(s[1]) * unit_num
            return str(num)

        return pattern.sub(split_replace, str_target)

    # 替换单位：百，千，万
    @staticmethod
    def replace_unit(pattern, str_target, unit, unit_num):
        def replace_unit(match):
            str_in = match.group()
            s = str_in.split(unit)
            num = 0
            len_s = len(s)
            if len_s == 1:
                hundred = int(s[0])
                num += hundred * unit_num
            elif len_s == 2:
                hundred = int(s[0])
                num += hundred * unit_num
                num += int(s[1])
            return str(num)

        return pattern.sub(replace_unit, str_target)

    # 将字符串中所有的用汉字表示的数字转化为用阿拉伯数字表示的数字
    @staticmethod
    def num_translate(str_target):
        # 不完整的中文数字，比如 “五万二”
        pattern = re.compile(r"[一二两三四五六七八九123456789]万[一二两三四五六七八九123456789](?!(千|百|十))")
        str_target = Preprocessor.abbreviation_match(pattern, str_target, "万", 1000)
        pattern = re.compile(r"[一二两三四五六七八九123456789]千[一二两三四五六七八九123456789](?!(百|十))")
        str_target = Preprocessor.abbreviation_match(pattern, str_target, "千", 100)
        pattern = re.compile(r"[一二两三四五六七八九123456789]百[一二两三四五六七八九123456789](?!十)")
        str_target = Preprocessor.abbreviation_match(pattern, str_target, "百", 10)

        # 完整的中文数字，周
        def replace_num(match):
            res = Preprocessor.word_to_num(match.group())
            return str(res)

        pattern = re.compile(r"[零一二两三四五六七八九]")
        str_target = pattern.sub(replace_num, str_target)
        pattern = re.compile(r"(?<=[周|星期])[末天日]")
        str_target = pattern.sub(replace_num, str_target)

        # 替换单位十
        def replace_unit_ten(match):
            str_in = match.group()
            s = str_in.split("十")
            num = 0
            len_s = len(s)
            if len_s == 0:
                num += 10
            elif len_s == 1:
                ten = int(s[0])
                if ten == 0:
                    num += 10
                else:
                    num += ten * 10
            elif len_s == 2:
                if s[0] == "":
                    num += 10
                else:
                    ten = int(s[0])
                    if ten == 0:
                        num += 10
                    else:
                        num += ten * 10
                if len(s[1]) > 0:
                    num += int(s[1])
            return str(num)

        pattern = re.compile(r"(?<![周|星期])0?[0-9]?十[0-9]?")
        str_target = pattern.sub(replace_unit_ten, str_target)

        # 替换单位：百，千，万
        pattern = re.compile(r"0?[1-9]百[0-9]?[0-9]?")
        str_target = Preprocessor.replace_unit(pattern, str_target, "百", 100)
        pattern = re.compile(r"0?[1-9]千[0-9]?[0-9]?[0-9]?")
        str_target = Preprocessor.replace_unit(pattern, str_target, "千", 1000)
        pattern = re.compile(r"[0-9]+万[0-9]?[0-9]?[0-9]?[0-9]?")
        str_target = Preprocessor.replace_unit(pattern, str_target, "万", 10000)

        return str_target

    @staticmethod
    def word_to_num(str_in):
        res = NUM_MAP.get(str_in)
        if res is None:
            return -1
        return res
