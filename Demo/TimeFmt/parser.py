# -*- coding:utf-8 -*-


import codecs
import re
import time

from TimeFmt.time_transformer import TimeTransformer
from TimeFmt.preprocessor import Preprocessor
from TimeFmt.time_normalizer import TimeNormalizer


class Parser:
    time_base = None
    patterns = None
    target = None
    time_token = list()
    is_prefer_future = True
    file_path = "D:\\PyProject\\Demo\\TimeFmt\\time_re"

    def __init__(self, prefer_future=True):
        # 是否关闭未来倾向
        self.is_prefer_future = prefer_future
        if self.patterns is None:
            self.read()

    def read(self):
        f = codecs.open(self.file_path, 'r', 'utf-8')
        str_in = f.read()
        self.patterns = re.compile(str_in)

    def pre_process(self):
        str_target = self.target
        # 清理空白字符
        str_target = Preprocessor.del_keyword(str_target, r"\\s+")
        # 清理语气助词
        str_target = Preprocessor.del_keyword(str_target, "[的]+")
        # 大写数字转换
        str_target = Preprocessor.num_translate(str_target)
        # TODO 处理大小写标点符号
        self.target = str_target

    def time_ex(self):
        str_target = self.target
        it = re.finditer(self.patterns, str_target)
        end = -1
        match_count = 0
        str_map_arr = dict()
        if str_target.find('至') != -1 or str_target.find('到') != -1 or str_target.find('间') != -1 or str_target.find(
                '、') != -1:  # 时间区间
            for m in it:
                start = m.start()
                if end == start:
                    match_count -= 1
                    str_map_arr[match_count] = str_map_arr[match_count] + m.group()
                else:
                    str_map_arr[match_count] = m.group()
                end = m.end()
                match_count += 1
        else:  # 时间点
            str_map_arr[match_count] = str_target
            match_count += 1
        print(str_map_arr)
        print(match_count)

        # 时间上下文： 前一个识别出来的时间会是下一个时间的上下文，
        # 用于处理：周六3点到5点这样的多个时间的识别，第二个5点应识别到是周六的。
        for i in range(match_count):
            clean_record = False
            if i == 0:
                clean_record = True
            time_unit = TimeNormalizer(str_map_arr[i], self.time_base, clean_record)
            if time_unit.time != -28800000:
                self.time_token.append(time_unit)

    # 从句子中提取出时间词，并转换为特定格式，包含时间推算等
    def parse(self, str_target, time_base=None):
        # 清除上次存储的结果
        if len(self.time_token) > 0:
            self.time_token.clear()
        self.target = str_target
        if time_base is None:
            self.time_base = TimeTransformer(time.time())
        else:
            self.time_base = TimeTransformer(time_base)

        self.pre_process()
        self.time_ex()
        return self.time_token
