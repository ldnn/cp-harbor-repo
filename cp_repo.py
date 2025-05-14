import requests,configparser,urllib3  
from urllib.parse import quote
from requests.auth import HTTPBasicAuth

# 创建配置解析器对象
config = configparser.ConfigParser()

# 禁用不安全的请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 读取配置文件
config.read('config.ini')

# 从配置文件中获取变量
HARBOR_HOST = config.get('harbor', 'HARBOR_HOST')
SOURCE_PROJECT = config.get('harbor', 'SOURCE_PROJECT')
SOURCE_REPO = config.get('harbor', 'SOURCE_REPO')
TARGET_PROJECT = config.get('harbor', 'TARGET_PROJECT')
TARGET_REPO = config.get('harbor', 'TARGET_REPO')
USERNAME = config.get('harbor', 'USERNAME')
PASSWORD = config.get('harbor', 'PASSWORD')
ENABLE_OVERRIDE = config.getboolean('harbor', 'ENABLE_OVERRIDE')  # 读取布尔值
PAGE_SIZE = config.getint('harbor', 'PAGE_SIZE')  # 读取整数


def get_artifacts(page: int) -> list:
    """分页获取制品列表"""
    api_url = f"https://{HARBOR_HOST}/api/v2.0/projects/{SOURCE_PROJECT}/repositories/{SOURCE_REPO}/artifacts"
    params = {'page': page, 'page_size': PAGE_SIZE}
    try:
        response = requests.get(api_url, params=params,auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False)
        response.raise_for_status()
        return [art['digest'] for art in response.json()]
    except requests.exceptions.RequestException as e:
        print(f"获取制品失败: {str(e)}")
        return []

def copy_artifact(digest: str) -> None:
    """执行制品复制操作"""
    source_ref = f"{SOURCE_PROJECT}/{SOURCE_REPO}@{digest}"
    api_url = f"https://{HARBOR_HOST}/api/v2.0/projects/{TARGET_PROJECT}/repositories/{TARGET_REPO}/artifacts"
    params = {
        'from': source_ref,
        'override': ENABLE_OVERRIDE
    }
    

    try:
        response = requests.post(api_url, params=params, auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False)
        if response.status_code == 201:
            print(f"[成功] {digest}")
        elif response.status_code == 409:
            print(f"[冲突] {digest} 已存在")
        else:
            print(f"[失败] {digest} HTTP {response.status_code}")
            print(f"响应内容: {response.text}")  # 打印响应内容
    except requests.exceptions.RequestException as e:
        print(f"复制失败: {str(e)}")


def main():
    print("===== Harbor跨项目复制开始 =====")
    print(f"{SOURCE_PROJECT}/{SOURCE_REPO}—>{TARGET_PROJECT}/{TARGET_REPO}")
    page = 1
    key =(USERNAME, PASSWORD)
    while True:
        print(f"正在获取第{page}页制品...")
        artifacts = get_artifacts(page)
        if not artifacts:
            break
        
        for digest in artifacts:
            copy_artifact(digest)
        
        page += 1
    
    print("===== 操作完成 =====")

if __name__ == "__main__":
    main()
