# coding=utf-8
import urllib.parse, operator, json
from Utils.utils import get_md5, is_chinese, decode
from Utils.HttpUtils import get_path, get_payload
import numpy as np
from hmmlearn.hmm import GaussianHMM
from xml.etree import ElementTree
import warnings
from functools import reduce

warnings.filterwarnings("ignore", category=DeprecationWarning)


class Extractor(object):
    def __init__(self, data):
        self.parameter = {}
        self.data = data
        url = str(data["uri"].encode("utf-8"), encoding="utf-8")
        self.uri = urllib.parse.unquote(url).strip()
        self.path = decode(get_path(self.uri))
        self.payload = get_payload(self.uri).strip("?")
        self.host = urllib.parse.unquote(self.data["host"]).strip()
        self.method = urllib.parse.unquote(self.data["method"]).strip()
        self.content_type = self.data["content_type"]
        self.get_parameter()

    def get_parameter(self):
        if self.payload.strip():
            # url 的（参数，值）模式
            for (p_id, p_state, p_type, p_name) in self.url():
                self.parameter[p_id] = {}
                self.parameter[p_id]["p_state"] = p_state
                self.parameter[p_id]["p_type"] = p_type
                self.parameter[p_id]["p_name"] = p_name
            # url 的参数名模式
            (p_id, p_state, p_type, p_name) = self.uri_p_name()
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name
        # url path 模式
        if self.path.strip():
            (p_id, p_state, p_type, p_name) = self.path_p()
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name
        # http_type 模式
        if self.data["http_type"].strip():
            (p_id, p_state, p_type, p_name) = self.http_type()
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name
        # content_length 模式
        if self.data["content_length"]:
            (p_id, p_state, p_type, p_name) = self.content_length()
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name
        # cookie 模式
        if self.data["cookie"].strip():
            for (p_id, p_state, p_type, p_name) in self.cookie():
                self.parameter[p_id] = {}
                self.parameter[p_id]["p_state"] = p_state
                self.parameter[p_id]["p_type"] = p_type
                self.parameter[p_id]["p_name"] = p_name
            (p_id, p_state, p_type, p_name) = self.cookie_p_name()
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name
        # post 请求体模式
        if self.data["data"].strip():
            # 参数，值模式
            p_names = ""
            for (p_id, p_state, p_type, p_name) in self.post():
                self.parameter[p_id] = {}
                self.parameter[p_id]["p_state"] = p_state
                self.parameter[p_id]["p_type"] = p_type
                self.parameter[p_id]["p_name"] = p_name
                p_names += p_name
            # 参数名模式
            (p_id, p_state, p_type, p_name) = self.post_p_name(p_names)
            self.parameter[p_id] = {}
            self.parameter[p_id]["p_state"] = p_state
            self.parameter[p_id]["p_type"] = p_type
            self.parameter[p_id]["p_name"] = p_name

    def get_Ostate(self, s):
        """
        字母 =》'A'
        数字 =》'N'
        中文 =》'C'
        特殊字符不变

        :param s:
        :return:
        """
        A = self.get_num('A')
        N = self.get_num("N")
        C = self.get_num("C")
        state = []
        if not isinstance(s, str):
            s = decode(str(s))
        if len(s) == 0:
            # 空字符串取0
            state.append([0])
            return state
        # s=str(s).decode("utf-8","ignore")
        for i in s:
            if i.encode("utf-8").isalpha():
                state.append([A])
            elif i.isdigit():
                state.append([N])
            elif is_chinese(i):
                state.append([C])
            else:
                state.append([self.get_num(i)])
        return state

    def get_param_Ostate(self, s):
        """
        参数名比较固定，一般不会变化
        :param s:  参数名字符串
        :return:  观察的状态
        """
        state = []
        for i in s:
            state.append(i)
        return state

    def get_num(self, s):
        return ord(s)

    def url(self):
        for p in self.payload.split("&"):
            p_list = p.split("=")
            p_name = p_list[0]
            if len(p_list) > 1:
                p_value = reduce(operator.add, p_list[1:])
                p_id = get_md5(self.host + self.path + decode(p_name) + self.method)
                p_state = self.get_Ostate(p_value)
                p_type = "uri"
                yield (p_id, p_state, p_type, p_name)

    def path_p(self):
        p_id = get_md5(self.host + self.method + self.path)
        p_state = self.get_Ostate(self.path)
        p_type = "uri_path"
        p_name = ""
        return (p_id, p_state, p_type, p_name)

    def post(self):
        post_data = urllib.parse.unquote(urllib.parse.unquote(self.data["data"]))
        content_t = self.content_type

        def ex_urlencoded(post_data):
            for p in post_data.split("&"):
                p_list = p.split("=")
                p_name = p_list[0]
                if len(p_list) > 1:
                    p_value = reduce(operator.add, p_list[1:])
                    p_id = get_md5(self.host + self.path + decode(p_name) + self.method)
                    p_state = self.get_Ostate(p_value)
                    p_type = "post"
                    yield (p_id, p_state, p_type, p_name)

        def ex_json(post_data):
            post_data = json.loads(post_data)
            for p_name, p_value in post_data.items():
                p_id = get_md5(self.host + self.path + decode(p_name) + self.method)
                p_state = self.get_Ostate(str(p_value))
                p_type = "post"
                yield (p_id, p_state, p_type, p_name)

        def ex_xml(post_data):
            tree = ElementTree.fromstring(post_data)
            elements = []
            p_names = []

            def get_item(tree, parent_tag=""):
                if tree.getchildren():
                    if parent_tag:
                        parent_tag += "/" + tree.tag
                    else:
                        parent_tag = tree.tag
                    for t in tree.getchildren():
                        get_item(t, parent_tag)
                else:
                    elements.append(tree.text)
                    p_names.append(parent_tag + "/" + tree.tag)

            get_item(tree)
            for (p_name, p_value) in zip(p_names, elements):
                p_state = self.get_Ostate(p_value)
                p_type = "post"
                p_id = get_md5(self.host + self.path + decode(p_name) + self.method)
                yield (p_id, p_state, p_type, p_name)

        if "application/x-www-form-urlencoded" in content_t:
            return ex_urlencoded(post_data)
        elif "application/json" in content_t:
            return ex_json(post_data)
        elif "text/xml" in content_t:
            return ex_xml(post_data)
        else:
            return None

    def http_type(self):
        http_type = self.data["http_type"]
        p_id = get_md5(self.host + self.path + "http_type" + self.method)
        p_state = self.get_Ostate(http_type)
        p_type = "http_type"
        p_name = ""
        return (p_id, p_state, p_type, p_name)

    def content_length(self):
        content_length = self.data["content_length"]
        p_id = get_md5(self.host + self.path + "content_length" + self.method)
        p_state = self.get_Ostate(content_length)
        p_type = "content_length"
        p_name = ""
        return (p_id, p_state, p_type, p_name)

    def cookie(self):
        cookies = urllib.parse.unquote(str(self.data["cookie"].encode("utf-8"), encoding="utf-8"))
        for p in cookies.split("; "):
            if p.strip():
                p_list = p.split("=")
                p_name = p_list[0]
                if len(p_list) > 1:
                    p_value = reduce(operator.add, p_list[1:])
                    p_id = get_md5(self.host + self.path + decode(p_name) + self.method)
                    p_state = self.get_Ostate(p_value)
                    p_type = "cookie"
                    yield (p_id, p_state, p_type, p_name)

    def uri_p_name(self):
        p_name = ""
        for p in self.payload.split("&"):
            p_name += p.split("=")[0]
        p_state = self.get_Ostate(p_name)
        p_type = "uri_pname"
        p_id = get_md5(self.host + self.path + self.method + p_type)
        p_name = ""
        return (p_id, p_state, p_type, p_name)

    def cookie_p_name(self):
        cookie = urllib.parse.unquote(str(self.data["cookie"].encode("utf-8"), encoding="utf-8"))
        p_name = ""
        for p in cookie.split("; "):
            if p.strip():
                p_name += p.split("=")[0]
        p_type = "cookie_pname"
        p_id = get_md5(self.host + self.path + self.method + p_type)
        p_state = self.get_Ostate(p_name)
        p_name = ""
        return (p_id, p_state, p_type, p_name)

    def post_p_name(self, p_names):
        p_state = self.get_Ostate(p_names)
        p_type = "post_pname"
        p_name = ""
        p_id = get_md5(self.host + self.path + self.method + p_type)
        return (p_id, p_state, p_type, p_name)


class Trainer(object):
    def __init__(self, data):
        self.p_id = data["p_id"]
        self.p_state = data["p_states"]

    def get_model(self):
        self.train()
        self.get_profile()
        return (self.model, self.profile)

    def train(self):
        Hstate_num = list(range(len(self.p_state)))   # 获取 序列的数目
        Ostate_num = list(range(len(self.p_state)))
        Ostate = []
        for (index, value) in enumerate(self.p_state):
            Ostate += value  # 观察状态序列
            Hstate_num[index] = len(set(np.array(value).reshape(1, len(value))[0]))  # 获取状态数列表
            Ostate_num[index] = len(value) #观测长度 列表
        self.Ostate = Ostate
        self.Hstate_num = Hstate_num
        self.n = int(round(np.array(Hstate_num).mean()))  # 隐藏状态数，平均值
        model = GaussianHMM(n_components=self.n, n_iter=1000, init_params="mcs", covariance_type="full")
        model.fit(np.array(Ostate), lengths=Ostate_num)
        s = model.transmat_.sum(axis=1).tolist()
        try:
            model.transmat_[s.index(0.0)] = np.array([1.0 / self.n] * self.n)  # 归一化
        except ValueError:
            pass
        self.model = model

    def get_profile(self):
        scores = np.array(range(len(self.p_state)), dtype="float64")
        for (index, value) in enumerate(self.p_state):
            scores[index] = self.model.score(value)   # 样本score
        self.profile = float(scores.min())    # 样本中最小的 score
        self.scores = scores

    def re_train(self):
        score_mean = self.scores.mean()      # 得分平均值
        sigma = self.scores.std()    # 得分标准差
        if self.profile < (score_mean - 3 * sigma):    #  在 3sigma 范围外 重新训练
            index = self.scores.tolist().index(self.profile)
            self.p_state.pop(index)
            self.train()
            self.get_profile()
            self.re_train()


class Detector(object):
    def __init__(self, model, p):
        self.model = model
        self.profile = p

    def detect(self, data):
        self.score = self.model.score(data["p_state"])
        if self.score < self.p:
            return True
        else:
            return False


def main():
    data = {'content_length': 43, 'status': '', 'src_port': '59474',
            'cookie': 'JSESSIONID%3Da449d6d0-a91d-4db4-a619-ed55239675e9%3B%20socm4ia%3D33SdLeElYV-1ES4bZEzfJ2msWUzGyf8G%257Cguoweibo01.3QGvYoBnZm98bE%252B6w%252B6e1RMN%252BY6x1H4YjY%252FQ5lfKKZU%3B%20connectId%3Ds%253A33SdLeElYV-1ES4bZEzfJ2msWUzGyf8G.8AqrleZu1lQY%252BvV2sakGkiUNdtcyB6WNYf1HfK%252FaPpA%3B%20socm4ts%3D0p4JtcIKKScCOzTN1ZJ_0kCoUVelMBsu%257Cguoweibo01.1zRT7PIXe9CrS2Pn5kBTCQsKpwPydoKf0KaieeHD1I8%3B%20tsConnectId%3Ds%253A0p4JtcIKKScCOzTN1ZJ_0kCoUVelMBsu.7Z7vNkjVarRmFz0czSHUxEoMNzXnE69iYXxJWnKSkds',
            'uri': '/portal/logins/checklogin?a=23&b123=89', 'http_type': 'Request', 'server': '',
            'src_ip': '192.168.126.131', 'host': '10.10.10.1:8888',
            'referer': 'http://10.10.10.1:8888/portal/logins/login', 'flow_time': 1493966490,
            'content_type': 'text/xml', 'date': '', 'dst_ip': '10.10.10.1.180', 'dst_port': '8888',
            'data': '%3Croot%3E%3Cheader%3E%3Ctype%3Efetch%3C/type%3E%3C/header%3E%3Ccontent%3E%3Cprogram%3Etest%3C/program%3E%3C/content%3E%3C/root%3E',
            'method': 'POST', 'user_agent': ' Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'}
    ps = Extractor(data).parameter
    print(ps)
    for key in ps.keys():
        if ps[key]["p_type"] == "post_pname":
            print(ps[key])


if __name__ == "__main__":
    main()
