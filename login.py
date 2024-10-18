import requests
import bs4
import js2py


def encrypt():
    # 获取js加密函数(逆向失败..)
    js = requests.get("https://uia.njfu.edu.cn/authserver/custom/js/encrypt.js").text
    ex = js2py.EvalJs()
    ex.execute(js)

    return ex.encryptAES


def get_form_data(html):
    soup = bs4.BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="casLoginForm")  # 获取表单元素
    form_data = {}
    for input_tag in form.find_all("input"):
        try:
            form_data[input_tag["name"]] = input_tag["value"]
        except KeyError:
            try:
                form_data[input_tag["id"]] = input_tag["value"]
            except KeyError:
                pass

    return form_data


def uia_login(username: str, password: str) -> dict | None:
    s = requests.Session()  # 会话

    s.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "host": "jwxt.njfu.edu.cn",
    }

    s.get("http://jwxt.njfu.edu.cn/sso.jsp")  # 先获取cookie,不然会爆500

    s.headers["host"] = "uia.njfu.edu.cn"
    s.headers["referer"] = "http://jwxt.njfu.edu.cn"
    params = {"service": "http://jwxt.njfu.edu.cn/sso.jsp"}
    r = s.get("http://uia.njfu.edu.cn/authserver/login", params=params)

    form_data = get_form_data(r.text)
    form_data["username"] = username
    form_data["password"] = encrypt()(password, form_data["pwdDefaultEncryptSalt"])

    # 登录数据表单
    data = {
        "username": form_data["username"],
        "password": form_data["password"],
        "lt": form_data["lt"],
        "dllt": form_data["dllt"],
        "execution": form_data["execution"],
        "_eventId": form_data["_eventId"],
        "rmShown": form_data["rmShown"],
    }
    params.update(data)
    r = s.post(
        "https://uia.njfu.edu.cn/authserver/login",
        params=params,
        allow_redirects=False,  # 不能跳转,需要改headers的host
    )
    if "密码有误" in r.text:
        raise Exception("账号或密码错误")
    elif "请输入验证码" in r.text:  # 识别图形验证码太麻烦了, 能绕过就绕过
        raise Exception("需要验证码, 请在浏览器中登录一次后再尝试")

    s.headers["host"] = "jwxt.njfu.edu.cn"
    del s.headers["referer"]
    r = s.get(r.headers["Location"])

    if "教务系统欢迎您！" in r.text:
        return s.cookies.get_dict()
    else:
        raise Exception("登录失败-未知错误")


if __name__ == "__main__":
    print(uia_login(input("输入uia账号: "), input("输入uia密码: ")))
