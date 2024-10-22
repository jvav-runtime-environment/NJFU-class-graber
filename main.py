import requests
import json
import time
import bs4
import os
from login import uia_login


username = None
password = None
delay = 0.3

safe_mode = True
# 该选项控制是否启用安全模式,
# 即在仅有一个选项的情况下会询问用户是否选择
# 避免误抢发生
# 当然开启这个选项会要求用户输入导致抢课速度变慢
# 视情况自行选择是否使用


cookie = None
headers = {
    "Host": "jwxt.njfu.edu.cn",
    "Origin": "http://jwxt.njfu.edu.cn",
    "Referer": "http://jwxt.njfu.edu.cn/jsxsd/xsxkkc/comeInGgxxkxk",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
}


class Course:
    def __init__(self, data):
        if isinstance(data, str):
            self.raw_text = data
            self.data = json.loads(data)
        elif isinstance(data, dict):
            self.raw_text = json.dumps(data, ensure_ascii=False)
            self.data = data

        self.name = self.data["kcmc"]
        self.jx02id = self.data["jx02id"]
        self.jx0404id = self.data["jx0404id"]


# 网络请求函数
def login(username, password):
    # 登录
    global cookie, headers

    try:
        cookie = uia_login(username, password)
    except Exception as e:
        print(e)
        return False

    return True


def get_course_list_id():
    # 获取选课id
    global cookie, headers

    url = "http://jwxt.njfu.edu.cn/jsxsd/xsxk/xklc_list"
    r = requests.get(url=url, cookies=cookie, headers=headers)

    if r.status_code != 200:
        raise requests.RequestException("获取选课id失败")

    # 解析表格
    try:
        sp = bs4.BeautifulSoup(r.text, "html.parser")
        t = sp.find("table", id="attend_class").find_all("tr")[1:]

        name_list = []
        id_list = []

        for i in t:
            name_list.append(i.find_all("td")[1].text)
            id_list.append(i.find("a").attrs["onclick"].split("'")[1])

        return id_list[selector(name_list)]

    except Exception as e:
        return False


def get_course_ids(courseinfo, sec_info) -> Course:
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
        "iDisplayLength": 99,
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
        print("找到多个课程")

    course_list: list[Course] = []

    for i in course_info["aaData"]:
        course_list.append(Course(i))

    # 如果只有一个选项且包含关键字则直接返回
    if sec_info and (len(course_list) == 1) and (sec_info in course_list[0].raw_text):
        print("符合第二关键字, 直接选择...")
        index = 0
    else:
        index = selector([_.name for _ in course_list])

    return course_list[index]


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
    global cookie, headers

    requests.get(
        url="http://jwxt.njfu.edu.cn/jsxsd/xsxk/xsxk_exit&jx0404id=1",
        headers=headers,
        cookies=cookie,
    )


# 功能函数
def selector(list_):
    if len(list_) == 1:
        if not safe_mode:  # 安全模式下即使就一个选项也需要询问
            return 0

        elif comfirm(list_[0]):
            return 0

    elif len(list_) > 1:
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


def comfirm(item):
    a = input(f"请确认选择 <{item}> ?(enter键确认, 其他取消): ")
    if a == "":
        return True
    return False


print("--------------------------------------------------------\n")
print("南京林业大学新教务系统自动抢课工具v1.3\n")
print("authored by jvav-runtime-environment\n")
print("--------------------------------------------------------\n")

if os.path.isfile("data.json"):
    print("检测到配置文件, 读取数据...")
    with open("data.json", "r") as f:
        data = json.load(f)
        username = data["username"]
        password = data["password"]
        safe_mode = data["safe_mode"]

else:
    with open("data.json", "w") as f:
        json.dump({"username": None, "password": None, "safe_mode": True}, f)


while True:
    while True:
        if not (username and password):
            username = input("请输入uia账号: ")
            password = input("请输入uia密码: ")

        print("登录中...")
        if login(username, password):
            print("登录成功")

            with open("data.json", "w") as f:
                json.dump(
                    {
                        "username": username,
                        "password": password,
                        "safe_mode": safe_mode,
                    },
                    f,
                )

            break
        else:
            print("登录失败,请重试")
            username = None
            password = None

    try:
        courses = []
        while True:
            course = input("请输入备选课程id(重要课程优先输入)(输入q结束): ")
            if course == "q":
                if input(f"当前备选列表{courses}, 确认退出？(y/n): ") == "y":
                    break
                else:
                    continue
            course_sec_info = input(
                "请输入任意备选课程信息(宁可少填不要错填)(可以留空): "
            )

            courses.append([course, course_sec_info])

        print("\n--------------------------")
        print("准备工作完成!")
        print("按回车键开始抢课...")
        print("--------------------------\n")
        input()

        print("获取选课列表id中...")
        while True:
            try:
                course_list_id = get_course_list_id()
            except TypeError:  # 如果没有确认对应的选课列表
                print("刷新选课列表...")
            except requests.Timeout:  # 高峰时间波动处理
                print("获取选课列表id超时, 重试中...")

            if course_list_id:
                break

            print("获取选课列表id失败, 重试中...")
            time.sleep(delay * 10)

        print(f"获取选课列表成功! 选课列表id: {course_list_id}")
        print("模拟进入选课中...")
        enter_selection(course_list_id)
        time.sleep(delay)

        for i in courses:
            print("正在查询课程信息...")
            try:
                course = get_course_ids(i[0], i[1])

            except TypeError:
                print("未知格式, 已取消选择, 切换下一门课程...")
                continue

            except requests.exceptions.InvalidSchema:
                print("未找到对应的课程, 切换下一门课程...")
                continue

            print(
                f"id: {course.jx0404id}, 课程id: {course.jx02id}, 课程名: {course.name}"
            )

            print("正在抢课...")
            for j in range(3):  # 尝试3次
                try:
                    r = get_course(course.jx0404id, course.jx02id)

                    rtext = json.loads(r.text)
                    if rtext["success"]:
                        print(f"课程 {course.name} 抢课成功")
                    else:
                        print(f"课程 {course.name} 抢课失败, 原因: {rtext['message']}")

                    break

                except requests.RequestException:
                    print(f"抢课失败, 重试中...({j+1}/3)")
                    if j == 2:
                        print(f"课程 {course.name} 抢课失败, 切换下一门课程...")
                    time.sleep(delay)

            time.sleep(delay)

        print("抢课完成!")
        exit_selection()
        break

    except requests.RequestException as e:
        print(f"发生连接错误: {e}")
        print("重新登录...")

    except Exception as e:
        print(f"发生未知错误: {e}")
        print("重新登录...")
