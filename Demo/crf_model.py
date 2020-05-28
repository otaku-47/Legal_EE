import os
import subprocess
import CRFPP


class CRFModel(object):
    def __init__(self, model='model_name'):
        """
        函数说明: 类初始化
        :param model: 模型名称
        """
        self.model = model

    def predict(self, data):
        """
        函数说明: 预测
        :param data: 输入数据
        """
        result = []
        if not os.path.exists(self.model):
            print('模型不存在,请确认模型路径是否正确!')
            exit()
        tagger = CRFPP.Tagger("-m {} -v 3 -n2".format(self.model))
        # 处理距离
        for stc in data:
            tmp_steal = []
            tmp_draw = []
            tmp_consume = []
            tmp_sale = []
            tmp_volun = []
            tmp_steal_dis = []
            tmp_draw_dis = []
            tmp_consume_dis = []
            tmp_sale_dis = []
            tmp_volun_dis = []
            if 'B-Steal' in stc:
                idx = stc.index('B-Steal')
                cnt = 0
                for wd in stc:
                    tmp_steal.append(1)
                    tmp_steal_dis.append(abs(idx-cnt)+1)
                    cnt = cnt + 1
            else:
                for wd in stc:
                    tmp_steal.append(0)
                    tmp_steal_dis.append(256)
            if 'B-Draw' in stc:
                idx = stc.index('B-Draw')
                cnt = 0
                for wd in stc:
                    tmp_draw.append(1)
                    tmp_draw_dis.append(abs(idx-cnt)+1)
                    cnt = cnt + 1
            else:
                for wd in stc:
                    tmp_draw.append(0)
                    tmp_draw_dis.append(256)
            if 'B-Consume' in stc:
                idx = stc.index('B-Consume')
                cnt = 0
                for wd in stc:
                    tmp_consume.append(1)
                    tmp_consume_dis.append(abs(idx-cnt)+1)
                    cnt = cnt + 1
            else:
                for wd in stc:
                    tmp_consume.append(0)
                    tmp_consume_dis.append(256)
            if 'B-Sale' in stc:
                idx = stc.index('B-Sale')
                cnt = 0
                for wd in stc:
                    tmp_sale.append(1)
                    tmp_sale_dis.append(abs(idx-cnt)+1)
                    cnt = cnt + 1
            else:
                for wd in stc:
                    tmp_sale.append(0)
                    tmp_sale_dis.append(256)
            if 'B-Volunteer' in stc:
                idx = stc.index('B-Volunteer')
                cnt = 0
                for wd in stc:
                    tmp_volun.append(1)
                    tmp_volun_dis.append(abs(idx-cnt)+1)
                    cnt = cnt + 1
            else:
                for wd in stc:
                    tmp_volun.append(0)
                    tmp_volun_dis.append(256)
            tagger.clear()
            for i in range(len(stc)):
                s = stc[i] + ' ' + str(tmp_steal[i]) + ' ' + str(tmp_draw[i]) + ' ' + str(tmp_consume[i]) + ' '\
                    + str(tmp_sale[i]) + ' ' + str(tmp_volun[i]) + ' ' + str(tmp_steal_dis[i]) + ' ' + str(tmp_draw_dis[i]) \
                    + ' ' + str(tmp_consume_dis[i]) + ' ' + str(tmp_sale_dis[i]) + ' ' + str(tmp_volun_dis[i])
                print(s)
                tagger.add(s)
            tagger.parse()
            tmp_result = []
            size = tagger.size()
            for i in range(size):
                tmp_result.append(tagger.y2(i))
                print(tagger.y2(i))
            result.append(tmp_result)
        return result

    def add_tagger(self, tag_data):
        """
        函数说明: 添加语料
        :param tag_data: 数据
        :return:
        """
        word_str = tag_data.strip()
        if not os.path.exists(self.model):
            print('模型不存在,请确认模型路径是否正确!')
            exit()
        tagger = CRFPP.Tagger("-m {} -v 3 -n2".format(self.model))
        tagger.clear()
        for word in word_str:
            tagger.add(word)
        tagger.parse()
        return tagger

    def text_mark(self, tag_data, begin='B', middle='I', end='E', single='S'):
        """
        文本标记
        :param tag_data: 数据
        :param begin: 开始标记
        :param middle: 中间标记
        :param end: 结束标记
        :param single: 单字结束标记
        :return result: 标记列表
        """
        tagger = self.add_tagger(tag_data)
        size = tagger.size()
        tag_text = ""
        for i in range(0, size):
            word, tag = tagger.x(i, 0), tagger.y2(i)
            if tag in [begin, middle]:
                tag_text += word
            elif tag in [end, single]:
                tag_text += word + "*&*"
        result = tag_text.split('*&*')
        result.pop()
        return result

    def crf_test(self, tag_data, separator='_'):
        """
        函数说明: crf测试
        :param tag_data:
        :param separator:
        :return:
        """
        result = self.text_mark(tag_data)
        data = separator.join(result)
        return data

    def crf_learn(self, filename):
        """
        函数说明: 训练模型
        :param filename: 已标注数据源
        :return:
        """
        crf_bash = "crf_learn -f 3 -c 4.0 api/template.txt {} {}".format(filename, self.model)
        process = subprocess.Popen(crf_bash.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output.decode(encoding='utf-8'))