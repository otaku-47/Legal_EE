from flask import Flask
from flask_bootstrap import Bootstrap
from flask import render_template
from flask import request
from flask import jsonify
from kashgari import utils
import re
import functools
from TimeFmt.parser import Parser
import time
import tensorflow as tf
from tensorflow.python.keras.backend import set_session
from crf_model import CRFModel

app = Flask(__name__)
bootstrap = Bootstrap(app)


test_text_1 = '2014年12月的一天，被告人张某趁鲍某试衣服时，将鲍某包中该银行卡盗走。12月30日9时许，被告人张某持卡到ATM机上盗取现金2300元。后被告人张某到派出所主动投案。'
test_text_2 = '2015年6月22日凌晨，被告人鞠某通过攀爬楼体的方式进入位于延安市宝塔区东盛大厦3号楼1单元603室被害人赵某办公室内，盗窃戴尔牌p04S型笔记本电脑1台（经鉴定价值1000元）。事后，被告人温某通过网络将2部笔记本电脑以5000元销赃。 '
sess = tf.Session()
graph = tf.get_default_graph()
set_session(sess)
loaded_model = utils.load_model('modelInfo/p1/input/p1')
event_list = ['B-Steal', 'B-Draw', 'B-Consume', 'B-Sale', 'B-Volunteer']


cm = CRFModel(model='crf/model')


# 自定义事件类
class MyEvent:
    def __init__(self, t1, t2, t_str, arg_type, arg_value, num):
        self.time1 = t1
        self.time2 = t2
        self.time_str = t_str
        self.arg_type = arg_type
        self.arg_value = arg_value
        self.num = num

    def to_list(self):
        return [self.time1, self.time2, self.time_str, self.arg_type, self.arg_value, self.num]


# 自定义事件类比较函数
def my_event_cmp(e1, e2):
    if e1.time1 > e2.time1:
        return 1
    elif e1.time1 == e2.time1:
        if e1.num > e2.num:
            return 1
        elif e1.num == e2.num:
            return 0
        else:
            return -1
    else:
        return -1


# 分句
# Input: 分句前原始文本
# Return: 分句后的list
def split_sentence(text):
    split_text = re.split(r'[。；！？]', text)
    for i in range(len(split_text)):
        tmp = split_text[i]
        split_text[i] = tmp + '。'
    return split_text[:len(split_text)-1]


# 将文本转换成分字的格式输入模型
# Input: 分字前的list
# Return: 分字后的list
def split_char(text):
    predict_text = []
    sentence = split_sentence(text)
    for i in sentence:
        tmp = []
        for j in range(len(i)):
            tmp.append(i[j])
        predict_text.append(tmp)
    return predict_text


# 判断是否含有事件
# Input: 一句话的标注
# Return: 这句话包括的事件list
def is_event_sent(lst):
    event = []
    idx = []
    for j in range(len(lst)):
        if lst[j] in event_list:
            x, y = lst[j].split('-')
            event.append(y)
            idx.append(j)
    return event, idx


# 用模型预测
# Input: 一段原始文本
# Return: 字段类型list，字段内容list
def do_predict(text):
    arg_type = []
    arg_value = []
    x = split_char(text)
    with graph.as_default():
        set_session(sess)
        t_y = loaded_model.predict(x)
        print(t_y)
    y = cm.predict(data=t_y)
    print(y)
    for i in range(len(x)):
        tmp_y = y[i]
        tmp_event_list, tmp_trigger_idx = is_event_sent(tmp_y)
        # 这句话中只有一个事件
        if len(tmp_event_list) == 1:
            tmp_type = ''
            tmp_value = ''
            tmp_arg_type = []
            tmp_arg_value = []
            for j in range(len(tmp_y)):
                a = ''
                b = ''
                if tmp_y[j] != 'O':
                    a, b = tmp_y[j].split('-')
                else:
                    a = 'O'
                    b = 'O'
                if a == 'I':  # 标注为I，继续拼字
                    tmp_value = tmp_value + x[i][j]
                else:  # 标注不为I，如需要则将新的事件元素插入
                    if tmp_type != '' and tmp_value != '':
                        tmp_arg_type.append(tmp_type)
                        tmp_arg_value.append(tmp_value)
                        tmp_type = ''
                        tmp_value = ''
                    if a == 'B':
                        tmp_type = b
                        tmp_value = tmp_value + x[i][j]
            arg_type.append(tmp_arg_type)
            arg_value.append(tmp_arg_value)
        # 这句话中有多个事件
        elif len(tmp_event_list) > 1:
            tmp_type = ''
            tmp_value = ''
            tmp_arg_type = []
            for j in range(len(tmp_event_list)):
                tmp_arg_type.append([])
            tmp_arg_value = []
            for j in range(len(tmp_event_list)):
                tmp_arg_value.append([])
            now = 0
            for j in range(len(tmp_y)):
                a = ''
                b = ''
                if tmp_y[j] != 'O':
                    a, b = tmp_y[j].split('-')
                else:
                    a = 'O'
                    b = 'O'
                if a == 'I':  # 标注为I，继续拼字
                    tmp_value = tmp_value + x[i][j]
                else:  # 标注不为I，如需要则将新的事件元素插入
                    if tmp_type != '' and tmp_value != '':
                        type_flag = 0
                        cnt = 0
                        for k in range(len(tmp_event_list)):
                            if tmp_event_list[k] in tmp_type:
                                type_flag = k
                                cnt = cnt + 1
                        if cnt == 1:  # 这句话中此类型的事件只有一个，直接加到所在的list
                            tmp_arg_type[type_flag].append(tmp_type)
                            tmp_arg_value[type_flag].append(tmp_value)
                        elif cnt > 1:  # 这句话中此类型的事件有多个，根据规则分配元素
                            # 计算距离
                            dis = []
                            for k in range(len(tmp_event_list)):
                                dis.append(None)
                            min_dis = 999
                            min_idx = 0
                            if 'Time' in b or 'Victim' in b or 'Person' in b:  # 时间，Victim必须在触发词之前
                                for k in range(len(tmp_event_list)):
                                    if tmp_event_list[k] in tmp_type:
                                        dis[k] = now - tmp_trigger_idx[k]
                                        if abs(dis[k]) < min_dis and dis[k] > 0:
                                            min_dis = abs(dis[k])
                                            min_idx = k
                                tmp_arg_type[min_idx].append(b)
                                tmp_arg_value[min_idx].append(tmp_value)
                            else:  # 不是时间元素直接判距离即可
                                for k in range(len(tmp_event_list)):
                                    if tmp_event_list[k] in tmp_type:
                                        dis[k] = now - tmp_trigger_idx[k]
                                        if abs(dis[k]) < min_dis:
                                            min_dis = abs(dis[k])
                                            min_idx = k
                                tmp_arg_type[min_idx].append(b)
                                tmp_arg_value[min_idx].append(tmp_value)
                        tmp_type = ''
                        tmp_value = ''
                    if a == 'B':
                        tmp_type = b
                        tmp_value = tmp_value + x[i][j]
                        now = j
            for j in range(len(tmp_event_list)):
                arg_type.append(tmp_arg_type[j])
                arg_value.append(tmp_arg_value[j])
    return arg_type, arg_value


# 格式化输出事件抽取结果
# Input: 字段类型list，字段内容list
# Return: 去重且事件排序后的list，是否有自首情节
def print_info(arg_type, arg_value):
    event_info = []
    is_volunteer = False
    volun_list = []
    time_1 = ''
    time_2 = ''
    t_str = ''
    tmp_time = ''  # 用于记录上一个时间
    for i in range(len(arg_type)):
        tmp_event = MyEvent(time_1, time_2, '', [], [], i)
        # 用于去重
        person_stack = []
        location_stack = []
        things_stack = []
        victim_stack = []
        thief_stack = []
        tmp_type = []
        tmp_value = []
        for j in range(len(arg_type[i])):
            if 'Volun' in arg_type[i][j]:
                is_volunteer = True
                if 'Person' in arg_type[i][j]:
                    volun_list.append(arg_value[i][j])
            if 'Time' in arg_type[i][j]:  # 处理时间
                tmp_time = time_1
                tn = Parser()
                res = None
                if t_str != '':  # 不是第一个时间，将上一个时间作为基准时间
                    print(tmp_time)
                    t1 = time.strptime(tmp_time, '%Y-%m-%d %H:%M:%S')
                    dt = time.mktime(t1)
                    res = tn.parse(arg_value[i][j], dt)
                else:  # 是第一个时间，不需要设置基准时间
                    res = tn.parse(arg_value[i][j])
                t_str = arg_value[i][j]
                if len(res) == 1:  # 只有一个时间词
                    time_1 = res[0].time
                elif len(res) == 2:  # 有两个时间词
                    time_1 = res[0].time
                    time_2 = res[1].time
            elif 'Person' in arg_type[i][j]:  # 处理需要去重的元素，下同
                if arg_value[i][j] not in person_stack:
                    tmp_type.append(arg_type[i][j])
                    tmp_value.append(arg_value[i][j])
                    person_stack.append(arg_value[i][j])
            elif 'Location' in arg_type[i][j]:
                if arg_value[i][j] not in location_stack:
                    tmp_type.append(arg_type[i][j])
                    tmp_value.append(arg_value[i][j])
                    location_stack.append(arg_value[i][j])
            elif 'Things' in arg_type[i][j]:
                if arg_value[i][j] not in things_stack:
                    tmp_type.append(arg_type[i][j])
                    tmp_value.append(arg_value[i][j])
                    things_stack.append(arg_value[i][j])
            elif 'Victim' in arg_type[i][j]:
                if arg_value[i][j] not in victim_stack:
                    tmp_type.append(arg_type[i][j])
                    tmp_value.append(arg_value[i][j])
                    victim_stack.append(arg_value[i][j])
            elif 'Thief' in arg_type[i][j]:
                if arg_value[i][j] not in thief_stack:
                    tmp_type.append(arg_type[i][j])
                    tmp_value.append(arg_value[i][j])
                    thief_stack.append(arg_value[i][j])
            else:  # 无需去重的元素
                tmp_type.append(arg_type[i][j])
                tmp_value.append(arg_value[i][j])
        if not is_volunteer:
            tmp_event.time1 = time_1
            tmp_event.time2 = time_2
            tmp_event.arg_type = tmp_type
            tmp_event.arg_value = tmp_value
            tmp_event.time_str = t_str
            event_info.append(tmp_event)
        time_2 = ''
    sorted_event = sorted(event_info, key=functools.cmp_to_key(my_event_cmp))
    for k in range(len(sorted_event)):
        sorted_event[k] = sorted_event[k].to_list()
    return sorted_event, is_volunteer, volun_list


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/btn_start', methods=['GET', 'POST'])
def btn_start():
    a = request.json
    if a:
        t = a['t']
        print(t)
        arg_type, arg_value = do_predict(t)
        event, volun, vl = print_info(arg_type, arg_value)
        return jsonify({'event': event, 'volun': volun, 'vl': vl})
    return jsonify('fail')


if __name__ == '__main__':
    app.run(debug=False)
