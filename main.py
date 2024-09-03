import requests
import json
import base64
import time
import re

cookie = None
username = None
password = None

headers = {
    "Host": "jwxt.njfu.edu.cn",
    "Origin": "http://jwxt.njfu.edu.cn",
    "Referer": "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/comeInGgxxkxk",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
}


def get_course(jx0404id, kcid):
    # 抢课
    global cookie, headers

    url = "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/ggxxkxkOper"
    data = {"jx0404id": jx0404id, "xkzy": "", "trjf": "", "kcid": kcid, "cfbs": ""}

    r = requests.post(url=url, data=data, cookies=cookie)
    return r


def get_course_ids(courseinfo):
    # 获取抢课必要的两个id(是不是必要的我不知道,但是他们接口是这么写的)
    global cookie, headers

    url = "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/xsxkGgxxkxk"
    data = {
        "kcxx": courseinfo,
        "skls": "",
        "skxq": "",
        "endJc": "",
        "skjc": "",
        "sfym": False,
        "sfct": False,
        "szjylb": "",
        "sfxx": False,
        "skfs": "",
        "sEcho": 1,
        "iColumns": 13,
        "sColumns": "",
        "iDisplayStart": 0,
        "iDisplayLength": 15,
        "mDataProp_0": "kch",
        "mDataProp_1": "kcmc",
        "mDataProp_2": "xf",
        "mDataProp_3": "skls",
        "mDataProp_4": "sksj",
        "mDataProp_5": "skdd",
        "mDataProp_6": "xqmc",
        "mDataProp_7": "xkrs",
        "mDataProp_8": "syrs",
        "mDataProp_9": "ctsm",
        "mDataProp_10": "tsTskflMc",
        "mDataProp_11": "tsTskflMc2",
        "mDataProp_12": "czOper",
    }
    r = requests.post(url=url, data=data, cookies=cookie, headers=headers)

    if r.status_code != 200:
        print("获取课程id失败")
        return None

    print(r.text)
    course_info = json.loads(r.text)
    if course_info["iTotalRecords"] == 0:
        print("没有找到该课程")
        return None
    elif course_info["iTotalRecords"] > 1:
        # todo:提供选择
        print("找到多个课程, 请精确选择范围")
        return None
    else:
        jx0404id = course_info["aaData"][0]["jx0404id"]
        ckid = course_info["aaData"][0]["jx02id"]

    return jx0404id, ckid


def login(username, password):
    # 登录
    global cookie, headers

    login_headers = headers.copy()
    login_headers["Referer"] = "http://jwxt.njfu.edu.cn/jsxsd/xk"

    url = "http://jwxt.njfu.edu.cn/jsxsd/xk/LoginToXk"  # 三个登录接口之一,应该是最简单的了吧
    data = {
        "loginMethod": "LoginToXk",
        "userAccount": username,
        "userPassword": "",
        "encoded": base64.b64encode(username.encode()).decode()
        + "%%%"
        + base64.b64encode(password.encode()).decode(),  # 逆天加密(
    }

    # 随便访问一个获取cookie
    cookie = requests.get(
        url="http://jwxt.njfu.edu.cn/jsxsd/xk", headers=login_headers
    ).cookies

    r = requests.post(url=url, data=data, headers=login_headers, cookies=cookie)

    if r.status_code != 200:
        return False

    return True


def get_course_list_id():
    # 获取选课id
    global cookie, headers

    url = "http://jwxt.njfu.edu.cn/jsxsd/xsxk/xklc_list"
    r = requests.get(url=url, cookies=cookie, headers=headers)
    text = r.text

    ids = re.compile(r"toxk\('([^']*)'\)").findall(text)

    return list(ids)


def enter_selection(course_list_id):
    # 模拟进入选课,不然查不了课程id
    global cookie, headers

    url = f"http://jwxt.njfu.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid={course_list_id}"
    r = requests.get(url=url, cookies=cookie, headers=headers)
    if r.status_code != 200:
        return False
    return True


login(username, password)
time.sleep(1)
enter_selection(get_course_list_id()[0])
time.sleep(1)
jx0404id, ckid = get_course_ids("影视鉴赏")
time.sleep(1)
r = get_course(jx0404id, ckid)
print(r.text)
