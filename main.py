import requests
import json
import base64
import time
import bs4

cookie = None
username = None
password = None
delay = 0.3

headers = {
    "Host": "jwxt.njfu.edu.cn",
    "Origin": "http://jwxt.njfu.edu.cn",
    "Referer": "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/comeInGgxxkxk",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
}


# 网络请求函数
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

    if r.status_code != 200:
        raise requests.RequestException("获取选课id失败")

    # 解析表格
    try:
        sp = bs4.BeautifulSoup(text, "html.parser")
        t = sp.find("table", id="attend_class").find_all("tr")[1:]
        if len(t) > 1:
            name_list = []
            id_list = []

            for i in t:
                name_list.append(i.find_all("td")[1].text)
                id_list.append(i.find("a").attrs["onclick"].split("'")[1])

            return id_list[selector(name_list)]  # >1个需要用户选择

        elif len(t) == 1:
            return t[0].find("a").attrs["onclick"].split("'")[1]

    except Exception as e:
        return False


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
        "iDisplayLength": 999,
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
        raise requests.RequestException("获取课程id失败")

    course_info = json.loads(r.text)
    if course_info["iTotalRecords"] == 0:
        raise requests.exceptions.InvalidSchema("没有找到该课程")

    elif course_info["iTotalRecords"] > 1:
        # 多于一个课程需要选择
        print("找到多个课程")

        name_list = []
        ids_list = []

        for i in course_info["aaData"]:
            name_list.append(i["kcmc"])
            ids_list.append([i["jx0404id"], i["jx02id"]])

        index = selector(name_list)

        return ids_list[index] + name_list[index]

    else:
        jx0404id = course_info["aaData"][0]["jx0404id"]
        ckid = course_info["aaData"][0]["jx02id"]
        name = course_info["aaData"][0]["kcmc"]

    return [jx0404id, ckid, name]


def get_course(jx0404id, kcid):
    # 抢课
    global cookie, headers

    url = "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/ggxxkxkOper"
    data = {"jx0404id": jx0404id, "xkzy": "", "trjf": "", "kcid": kcid, "cfbs": ""}

    r = requests.post(url=url, data=data, cookies=cookie)
    if r.status_code != 200:
        raise requests.RequestException("选课失败")

    return r


def enter_selection(course_list_id):
    # 模拟进入选课,不然查不了课程id
    global cookie, headers

    url = f"http://jwxt.njfu.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid={course_list_id}"
    r = requests.get(url=url, cookies=cookie, headers=headers)
    if r.status_code != 200:
        raise requests.RequestException("模拟进入选课失败")
    return True


def exit_selection():
    # 网页的安全退出，不知道有没有必要..
    requests.get(
        url="http://jwxt.njfu.edu.cn/jsxsd/xsxk/xsxk_exit&jx0404id=1",
        headers=headers,
        cookies=cookie,
    )


# 功能函数
def selector(list_):
    print("请选择,并输入选择的序号:")
    for i in range(1, len(list_) + 1):
        print(f"[{i}]:\t{list_[i-1]}")

    while True:
        try:
            index = int(input("你选择的序号:")) - 1
        except ValueError:
            print("输入错误, 请重新输入")
            continue

        if index < 0 or index >= len(list_):
            print("输入错误, 请重新输入")
            continue

        return index


while True:
    while True:
        username = input("请输入学号: ")
        password = input("请输入密码: ")
        print("登录中...")

        if login(username, password):
            print("登录成功")
            break
        else:
            print("登录失败,请重试")

    try:
        courses = []
        while True:
            course = input(
                "请输入备选课程名(id也行但是可能出多个结果)(重要课程优先输入)(输入q结束): "
            )

            if course == "q":
                print(f"当前备选列表{courses},确认退出？(y/n): ", end="")
                if input() == "y":
                    break
                else:
                    continue

            courses.append(course)

        print("获取选课列表id中...")
        while True:
            course_list_id = get_course_list_id()
            if course_list_id:
                break

            print("获取选课列表id失败, 重试中...")
            time.sleep(delay * 5)

        print(f"获取选课列表成功!选课列表id: {course_list_id}")
        print("模拟进入选课中...")
        enter_selection(course_list_id)
        time.sleep(delay)

        for i in courses:
            print("获取课程信息...")
            jx0404id, ckid, name = get_course_ids(i)
            print(f"id: {jx0404id}, 课程id: {ckid}, 课程名: {name}")

            print("正在抢课...")
            r = get_course(jx0404id, ckid)

            rtext = json.loads(r.text)
            if rtext["success"]:
                print(f"课程 {name} 选课成功")
            else:
                print(f"课程 {name} 选课失败, 原因: {rtext['message']}")

            time.sleep(delay)

        print("选课完成!")
        exit_selection()
        break

    except requests.RequestException as e:
        print(f"发生链接错误: {e}")
        print("重新登录...")
