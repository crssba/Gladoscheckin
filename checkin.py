import requests
import json
import os

# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # Gotify 推送配置
    gotify_url = "https://ysewsxzmhzws.us-east-1.clawcloudrun.com"
    gotify_token = "Avz-fZpA5oUK2Cz"

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies = os.environ.get("COOKIES", "").split("&")
    if cookies[0] != "":

        check_in_url = "https://glados.space/api/user/checkin"        # 签到地址
        status_url = "https://glados.space/api/user/status"          # 查看账户状态

        referer = 'https://glados.space/console/checkin'
        origin = "https://glados.space"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.one'
        }
        
        for cookie in cookies:
            try:
                checkin = requests.post(
                    check_in_url,
                    headers={
                        'cookie': cookie,
                        'referer': referer,
                        'origin': origin,
                        'user-agent': useragent,
                        'content-type': 'application/json;charset=UTF-8'
                    },
                    data=json.dumps(payload),
                    timeout=10
                )
                state = requests.get(
                    status_url,
                    headers={
                        'cookie': cookie,
                        'referer': referer,
                        'origin': origin,
                        'user-agent': useragent
                    },
                    timeout=10
                )

                message_status = ""
                points = 0
                message_days = ""
                email = "未知"

                # 签到结果
                if checkin.status_code == 200:
                    result = checkin.json()
                    print("签到返回:", result)
                    check_result = result.get('message', '无返回信息')
                    points = result.get('points', 0)

                    # 状态结果
                    result = state.json()
                    print("状态返回:", result)
                    if result.get("data"):
                        leftdays = int(float(result['data'].get('leftDays', 0)))
                        email = result['data'].get('email', '未知邮箱')
                    else:
                        leftdays = 0
                        fail += 1
                        message_status = f"状态查询失败: {result.get('message', '未知错误')}"
                        message_days = "error"

                    # 判断签到情况
                    if "Checkin! Got" in check_result:
                        success += 1
                        message_status = "签到成功，会员点数 + " + str(points)
                    elif "Checkin Repeats!" in check_result:
                        repeats += 1
                        message_status = "重复签到，明天再来"
                    else:
                        fail += 1
                        message_status = "签到失败: " + check_result

                    if not message_days:
                        message_days = f"{leftdays} 天" if leftdays else "error"
                else:
                    fail += 1
                    message_status = f"签到请求失败: HTTP {checkin.status_code}"
                    message_days = "error"

            except Exception as e:
                fail += 1
                email = "未知"
                message_status = f"脚本异常: {str(e)}"
                message_days = "error"

            # 拼接每个账号的结果
            context += f"账号: {email}, P: {points}, 剩余: {message_days}, 状态: {message_status} | "

        title = f'Glados, 成功{success},失败{fail},重复{repeats}'
        print("Send Content:\n", context)
        
    else:
        title = f'# 未找到 cookies!'

    # 推送消息到 Gotify
    if not gotify_token:
        print("No Gotify token set, skip push")
    else:
        try:
            resp = requests.post(
                f"{gotify_url}/message",
                headers={"X-Gotify-Key": gotify_token},
                json={
                    "title": title,
                    "message": context,
                    "priority": 5
                },
                timeout=10
            )
            if resp.status_code == 200:
                print("Gotify 推送成功")
            else:
                print("Gotify 推送失败:", resp.text)
        except Exception as e:
            print("Gotify 异常:", str(e))
