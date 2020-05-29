# -*- coding:utf-8 -*-


import re
from TimeFmt.time_transformer import TimeTransformer
from TimeFmt.fuzzy_time_enum import FuzzyTimeEnum


class TimePoint:
    unit = [-1, -1, -1, -1, -1, -1]

    def clean(self):
        for i in range(len(self.unit)):
            self.unit[i] = -1

    def __copy__(self):
        res = TimePoint()
        for i in range(len(self.unit)):
            res.unit[i] = self.unit[i]
        return res


class TimeNormalizer:
    time_expression = None
    time_norm = ""
    time_full = None
    time_origin = None
    time = ""
    is_all_day_time = True
    time_base = TimeTransformer
    _tp = TimePoint

    # 时间表达式单元构造方法 该方法作为时间表达式单元的入口，将时间表达式字符串传入
    def __init__(self, exp_time: str, time_base: TimeTransformer, clean_tp: bool):
        self.time_expression = exp_time
        self.time_base = time_base
        self._tp = TimePoint()
        if clean_tp:
            self._tp.clean()
        self.time_normalization()

    # 格式化时间
    def time_normalization(self):
        self.normal_year()
        self.normal_month()
        self.normal_day()
        self.normal_month_fuzzyday()

        self.normal_base_related()
        self.normal_cur_related()
        self.normal_hour()
        self.normal_minute()
        self.normal_second()
        self.normal_total()

        time_grid = self.time_base.get_time_list()
        t_unit_p = 5
        tmp = self._tp.unit[t_unit_p]
        for i in range(len(self._tp.unit)):
            if type(self._tp.unit[i]) == FuzzyTimeEnum:
                tt = self._tp.unit[i].value
                self._tp.unit[i] = tt
        while t_unit_p >= 0 > tmp:
            t_unit_p -= 1
            tmp = self._tp.unit[t_unit_p]
        for i in range(t_unit_p):
            if self._tp.unit[i] < 0:
                self._tp.unit[i] = time_grid[i]
        res_tmp = dict()
        zero_temp = self._tp.unit[0]
        res_tmp[0] = zero_temp
        if 10 <= zero_temp < 100:
            res_tmp[0] = 1900 + zero_temp
        if 0 < zero_temp < 10:
            res_tmp[0] = 2000 + zero_temp
        for i in range(1, 6):
            res_tmp[i] = self._tp.unit[i]

        # figure out the final time
        time_unit = ["年", "月", "日", "时", "分", "秒"]
        time_normal = ""
        for i in range(6):
            if not res_tmp[i] == -1:
                if res_tmp[i] < 10:
                    time_normal += '0' + str(res_tmp[i]) + time_unit[i]
                else:
                    time_normal += str(res_tmp[i]) + time_unit[i]
                if i == 1 or i == 2:
                    self.time += "-"
                elif i == 3:
                    self.time += " "
                elif i == 4 or i == 5:
                    self.time += ":"
                if res_tmp[i] < 10:
                    self.time += '0' + str(res_tmp[i])
                else:
                    self.time += str(res_tmp[i])
            else:
                if i == 0 or i == 3 or i == 4 or i == 5:
                    time_normal += '00' + time_unit[i]
                    if i == 3:
                        self.time += " "
                    elif i == 4 or i == 5:
                        self.time += ":"
                    self.time += '00'
                elif i == 1 or i == 2:
                    time_normal += '01' + time_unit[i]
                    self.time += "-"
                    self.time += '01'
        self.time_norm = time_normal
        self.time_full = self._tp.__copy__()

    # 格式化年份
    def normal_year(self):
        # 只有两位数的年份
        pattern = re.compile(r"[0-9]{2}(?=年)")
        m = re.search(pattern, self.time_expression)
        if m is not None:
            temp_unit = int(m.group())
            if 0 <= temp_unit <= 100:
                if temp_unit < 30:
                    # 30 以下表示 2000 年以后
                    temp_unit += 2000
                else:
                    # 否则表示 1900年以后
                    temp_unit += 1900
            self._tp.unit[0] = temp_unit

        # 如果有3位数和4位数的年份，则覆盖原来2位数识别出的年份
        pattern = re.compile(r"[0-9]?[0-9]{3}(?=年)")
        m = re.search(pattern, self.time_expression)
        if m is not None:
            self._tp.unit[0] = int(m.group())

    # 格式化月份
    def normal_month(self):
        pattern = re.compile(r"((10)|(11)|(12)|([1-9]))(?=月)")
        m = re.search(pattern, self.time_expression)
        if m is not None:
            self._tp.unit[1] = int(m.group())

    # 月-日 兼容模糊写法
    # 该方法识别时间表达式单元的月、日字段
    def normal_month_fuzzyday(self):
        pattern = re.compile(r"((10)|(11)|(12)|([1-9]))(月|\\.|\\-)([0-3][0-9]|[1-9])")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            str_in = match.group()
            p = re.compile(r"(月|\\.|\\-)")
            m = re.search(p, str_in)
            if m is not None:
                start = m.start()
                month = str_in[:start]
                date = str_in[start+1:]
                self._tp.unit[1] = int(month)
                self._tp.unit[2] = int(date)

    # 日 - 规范化方法
    def normal_day(self):
        pattern = re.compile(r"((?<!\d))([0-3][0-9]|[1-9])(?=[日|号])")
        m = re.search(pattern, self.time_expression)
        if m is not None:
            self._tp.unit[2] = int(m.group())

    # 时 - 规范化方法
    def normal_hour(self):
        pattern = re.compile(r"(?<![周|星期])([0-2]?[0-9])(?=[点|时])")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            self._tp.unit[3] = int(match.group())
            self.is_all_day_time = False

        # 对关键字：早（包含早上 / 早晨 / 早间），上午，中午, 午间, 下午, 午后, 晚上, 傍晚, 晚间, 晚, pm, PM的正确时间计算
        # 1.中午/午间0-10点视为12-22点
        # 2.下午/午后0-11点视为12-23点
        # 3.晚上/傍晚/晚间/晚1-11点视为13-23点，12点视为0点 4.0-11点pm/PM视为12-23点

        # 下面三次调用的子函数1
        def sub_func1(p, hour_time):
            m_s1 = re.search(p, self.time_expression)
            if m_s1 is not None:
                if self._tp.unit[3] == -1:
                    self._tp.unit[3] = hour_time
                self.is_all_day_time = False

        pattern = re.compile(r"凌晨")
        sub_func1(pattern, FuzzyTimeEnum.day_break)

        pattern = re.compile(r"早上|早晨|早间|晨间|今早|明早")
        sub_func1(pattern, FuzzyTimeEnum.early_morning)

        pattern = re.compile(r"上午")
        sub_func1(pattern, FuzzyTimeEnum.morning)

        # 下面三次调用的子函数2
        def sub_func2(p, hour_time):
            m_s2 = re.search(p, self.time_expression)
            if m_s2 is not None:
                temp_unit = self._tp.unit[3]
                if 0 <= temp_unit <= 10:
                    temp_unit += 12
                if temp_unit == 1:
                    temp_unit = hour_time
                self._tp.unit[3] = temp_unit
                self.is_all_day_time = False

        pattern = re.compile(r"(中午)|(午间)")
        sub_func2(pattern, FuzzyTimeEnum.noon)

        pattern = re.compile(r"(下午)|(午后)|(pm)|(PM)")
        sub_func2(pattern, FuzzyTimeEnum.afternoon)

        pattern = re.compile(r"晚上|夜间|夜里|今晚|明晚|晚")
        sub_func2(pattern, FuzzyTimeEnum.night)

        # 对关键字上旬/中旬/下旬的计算
        def sub_func3(p, day_time):
            m_s1 = re.search(p, self.time_expression)
            if m_s1 is not None:
                if self._tp.unit[2] == -1:
                    self._tp.unit[2] = day_time
                self.is_all_day_time = False
                
        pattern = re.compile(r"上旬")
        sub_func3(pattern, 1)

        pattern = re.compile(r"中旬")
        sub_func3(pattern, 15)

        pattern = re.compile(r"下旬")
        sub_func3(pattern, 28)

    # 分 - 规范化方法
    def normal_minute(self):
        pattern = re.compile(r"([0-5]?[0-9](?=分(?!钟)))|((?<=((?<!小)[点时]))[0-5]?[0-9](?!刻))")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            str_in = match.group()
            if not str_in == "":
                self._tp.unit[4] = int(str_in)
                self.is_all_day_time = False

        # 时刻处理子函数
        def quarter(p, q):
            m = re.search(p, self.time_expression)
            if m is not None:
                self._tp.unit[4] = q * 15
                self.is_all_day_time = False

        pattern = re.compile(r"(?<=[点时])[1一]刻(?!钟)")
        quarter(pattern, 1)
        pattern = re.compile(r"(?<=[点时])半")
        quarter(pattern, 2)
        pattern = re.compile(r"(?<=[点时])[3三]刻(?!钟)")
        quarter(pattern, 3)

    # 秒 - 规范化方法
    def normal_second(self):
        pattern = re.compile(r"([0-5]?[0-9](?=秒))|((?<=分)[0-5]?[0-9])")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            self._tp.unit[5] = int(match.group())
            self.is_all_day_time = False

    # 特殊形式的规范化方法
    def normal_total(self):
        pattern = re.compile(r"(?<![周|星期])([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split(":")
            self._tp.unit[3] = int(tmp_parser[0])
            self._tp.unit[4] = int(tmp_parser[1])
            self._tp.unit[5] = int(tmp_parser[2])
        else:
            pattern = re.compile(r"(?<![周|星期])([0-2]?[0-9]):[0-5]?[0-9]")
            match = re.search(pattern, self.time_expression)
            if match is not None:
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                self._tp.unit[3] = int(tmp_parser[0])
                self._tp.unit[4] = int(tmp_parser[1])
        self.is_all_day_time = False

        # 增加了:固定形式时间表达式的 中午,午间,下午,午后,晚上,傍晚,晚间,晚,pm,PM 的正确时间计算，规约同上
        def sub_func1(p, hour_time, edge):
            m = re.search(p, self.time_expression)
            if m is not None:
                t_unit = self._tp.unit[3]
                if 0 <= t_unit <= edge:
                    t_unit += 12
                if t_unit == -1:
                    t_unit = hour_time
                self._tp.unit[3] = t_unit
                self.is_all_day_time = False

        pattern = re.compile(r"(中午)|(午间)")
        sub_func1(pattern, FuzzyTimeEnum.noon, 10)
        pattern = re.compile(r"(下午)|(午后)|(pm)|(PM)")
        sub_func1(pattern, FuzzyTimeEnum.afternoon, 11)

        pattern = re.compile(r"晚")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            temp_unit = self._tp.unit[3]
            if 1 <= temp_unit <= 11:
                temp_unit += 12
            elif temp_unit == 12:
                temp_unit = 0
            if temp_unit == -1:
                # 增加对没有明确时间点，只写了“中午 / 午间”这种情况的处理
                temp_unit = FuzzyTimeEnum.night
            self._tp.unit[3] = temp_unit
            self.is_all_day_time = False

        def sub_func2(p, sp):
            m = re.search(p, self.time_expression)
            if m is not None:
                t_parser = m.group().split(sp)
                self._tp.unit[0] = int(t_parser[0])
                self._tp.unit[1] = int(t_parser[1])
                self._tp.unit[2] = int(t_parser[2])

        pattern = re.compile(r"[0-9]?[0-9]?[0-9]{2}-((10)|(11)|(12)|([1-9]))-((?<!\\d))([0-3][0-9]|[1-9])")
        sub_func2(pattern, "-")

        pattern = re.compile(r"((10)|(11)|(12)|([1-9]))/((?<!\d))([0-3][0-9]|[1-9])/[0-9]?[0-9]?[0-9]{2}")
        match = re.search(pattern, self.time_expression)
        if match is not None:
            tmp_parser = match.group().split("/")
            self._tp.unit[1] = int(tmp_parser[0])
            self._tp.unit[2] = int(tmp_parser[1])
            self._tp.unit[0] = int(tmp_parser[2])

        # 增加了:固定形式时间表达式 年.月.日 的正确识别
        pattern = re.compile(r"[0-9]?[0-9]?[0-9]{2}\\.((10)|(11)|(12)|([1-9]))\\.((?<!\\d))([0-3][0-9]|[1-9])")
        sub_func2(pattern, "\\.")

    # 设置以上文时间为基准的时间偏移计算
    def normal_base_related(self):
        time = self.time_base.__copy__()
        flag1 = False
        flag2 = False
        flag3 = False

        # 改变日
        def c_day(p, d_time):
            m = re.search(p, self.time_expression)
            if m is not None:
                d = int(m.group()) * d_time
                time.change_day(d)
                return True
            return False

        pattern = re.compile(r"\d+(?=天[以之]?前)")
        if c_day(pattern, -1):
            flag3 = True

        pattern = re.compile(r"\d+(?=天[以之]?后)")
        if c_day(pattern, 1):
            flag3 = True

        pattern = re.compile(r"\d+(?=日[以之]?前)")
        if c_day(pattern, -1):
            flag3 = True

        pattern = re.compile(r"\d+(?=日[以之]?后)")
        if c_day(pattern, 1):
            flag3 = True

        pattern = re.compile(r"\d+(?=(个)?星期[以之]?前)")
        if c_day(pattern, -7):
            flag3 = True
        pattern = re.compile(r"\d+(?=(个)?星期[以之]?后)")
        if c_day(pattern, 7):
            flag3 = True
        pattern = re.compile(r"\d+(?=周[以之]?前)")
        if c_day(pattern, -7):
            flag3 = True
        pattern = re.compile(r"\d+(?=周[以之]?后)")
        if c_day(pattern, 7):
            flag3 = True

        # 改变月
        def c_month(p, m_time):
            m = re.search(p, self.time_expression)
            if m is not None:
                m_num = int(m.group()) * m_time
                time.change_month(m_num)
                return True
            return False

        pattern = re.compile(r"\d+(?=(个)?月[以之]?前)")
        if c_month(pattern, -1):
            flag2 = True
        pattern = re.compile(r"\d+(?=(个)?月[以之]?后)")
        if c_month(pattern, 1):
            flag2 = True

        # 改变年
        def c_year(p, y_time):
            m = re.search(p, self.time_expression)
            if m is not None:
                y_num = int(m.group()) * y_time
                time.change_year(y_num)
                return True
            return False

        pattern = re.compile(r"\d+(?=年[以之]?前)")
        if c_year(pattern, -1):
            flag1 = True

        pattern = re.compile(r"\d+(?=年[以之]?后)")
        if c_year(pattern, 1):
            flag1 = True

        time_list = time.get_time_list()
        if flag1 or flag2 or flag3:
            self._tp.unit[0] = time_list[0]
        if flag2 or flag3:
            self._tp.unit[1] = time_list[1]
        if flag3:
            self._tp.unit[2] = time_list[2]

    # 设置当前时间相关的时间表达式
    def normal_cur_related(self):
        time = self.time_base.__copy__()
        flag1 = False
        flag2 = False
        flag3 = False

        # 改变年
        def c_year(p, num):
            m = re.search(p, self.time_expression)
            if m is not None:
                time.change_year(num)
                return True
            return False

        pattern = re.compile(r"前年")
        if c_year(pattern, -2):
            flag1 = True
        pattern = re.compile(r"去年")
        if c_year(pattern, -1):
            flag1 = True
        pattern = re.compile(r"今年")
        if c_year(pattern, 0):
            flag1 = True
        pattern = re.compile(r"明年")
        if c_year(pattern, 1):
            flag1 = True
        pattern = re.compile(r"后年")
        if c_year(pattern, 2):
            flag1 = True
        pattern = re.compile(r"同年")
        if c_year(pattern, 0):
            flag1 = True

        # 改变月
        def c_month(p, num):
            m = re.search(p, self.time_expression)
            if m is not None:
                time.change_month(num)
                return True
            return False

        pattern = re.compile(r"上(个)?月")
        if c_month(pattern, -1):
            flag2 = True
        pattern = re.compile(r"(本|这个|同)月")
        if c_month(pattern, 0):
            flag2 = True
        pattern = re.compile(r"下(个)?月")
        if c_month(pattern, 1):
            flag2 = True

        # 改变日
        def c_day(p, num):
            m = re.search(p, self.time_expression)
            if m is not None:
                time.change_day(num)
                return True
            return False

        pattern = re.compile(r"次日")
        if c_day(pattern, 1):
            flag3 = True
        pattern = re.compile(r"同日")
        if c_day(pattern, 0):
            flag3 = True
        pattern = re.compile(r"大前天")
        if c_day(pattern, -3):
            flag3 = True
        pattern = re.compile(r"(?<!大)前天")
        if c_day(pattern, -2):
            flag3 = True
        pattern = re.compile(r"昨")
        if c_day(pattern, -1):
            flag3 = True
        pattern = re.compile(r"今(?!年)")
        if c_day(pattern, 0):
            flag3 = True
        pattern = re.compile(r"明(?!年)")
        if c_day(pattern, 1):
            flag3 = True
        pattern = re.compile(r"(?<!大)后天")
        if c_day(pattern, 2):
            flag3 = True
        pattern = re.compile(r"大后天")
        if c_day(pattern, 3):
            flag3 = True

        # 更改星期
        def c_week(p, num):
            match = re.search(p, self.time_expression)
            if match is not None:
                d = 1
                str_d = match.group()
                if len(str_d) > 0:
                    d = int(str_d)
                time.change_week(num, d)
                return True
            return False

        pattern = re.compile(r"(?<=(上上[周|星期]))[1-7]?")
        if c_week(pattern, -2):
            flag3 = True
        pattern = re.compile(r"(?<=((?<!上)上[周|星期]))[1-7]?")
        if c_week(pattern, -1):
            flag3 = True
        pattern = re.compile(r"(?<=((?<!下)下[周|星期]))[1-7]?")
        if c_week(pattern, 1):
            flag3 = True
        pattern = re.compile(r"(?<=(下下[周|星期]))[1-7]?")
        if c_week(pattern, 2):
            flag3 = True
        pattern = re.compile(r"(?<=((?<![上|下|\d])[周|星期]))[1-7]?")
        if c_week(pattern, 0):
            flag3 = True
        time_list = time.get_time_list()
        if flag1 or flag2 or flag3:
            self._tp.unit[0] = time_list[0]
        if flag2 or flag3:
            self._tp.unit[1] = time_list[1]
        if flag3:
            self._tp.unit[2] = time_list[2]
