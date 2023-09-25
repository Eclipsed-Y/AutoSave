import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from hashlib import md5
from PIL import Image
from io import BytesIO
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# 读取配置文件
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

authors = config.get('url_authors')
browser = config.get('browser', 'edge').lower()
image_class = config.get('image_class', 'img img-fluid block-center img-fit')
image_width = config.get('image_width', 'img img-fluid block-center img-fit')
image_height = config.get('image_height', 'img img-fluid block-center img-fit')

for url_author in authors:

    # 初始化WebDriver，根据json选择不同浏览器
    if browser == 'edge':
        driver = webdriver.Edge()
    elif browser == 'chrome':
        driver = webdriver.Chrome()
    else:
        raise Exception("请在json中设置合适的浏览器")

    # 打开网页A
    driver.get(url_author)

    # 创建保存图片的目录
    image_dir = 'downloaded_images'
    os.makedirs(image_dir, exist_ok=True)

    # 用于存储已下载图片的哈希值，以避免下载重复图片
    check_images = set()
    need_to_do = []

    print("记录需要的url中...")
    for a_element in driver.find_elements(By.TAG_NAME, 'a'):
        if a_element.get_attribute('class') == "project-image":
            need_to_do.append(a_element.get_attribute('href'))

    print("记录完成，开始下载图片...")

    # 创建新文件夹
    folder_name = f'folder_{url_author.split("/")[-1]}'
    folder_path = os.path.join(image_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    idx = 0

    for url in need_to_do:
        driver.quit()
        if browser == 'edge':
            driver = webdriver.Edge()
        elif browser == 'chrome':
            driver = webdriver.Chrome()
        else:
            raise Exception("请在json中设置合适的浏览器")
        driver.get(url)
        # 等待元素加载，直到找到元素或超时（最多等待 10 秒）
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'img')))

        for img_element in driver.find_elements(By.TAG_NAME, 'img'):
            if img_element.get_attribute("class") == image_class:
                img_url = img_element.get_attribute('src')
                if img_url:
                    # 计算图片的哈希值
                    img_hash = md5(img_url.encode()).hexdigest()
                    # 检查图片是否已经下载过
                    if img_hash not in check_images:
                        check_images.add(img_hash)  # 将哈希值添加到已下载集合中

                        # 发送HTTP请求并保存图片
                        img_response = requests.get(img_url)
                        if img_response.status_code == 200:
                            try:
                                # 使用PIL库获取图片分辨率
                                img_data = img_response.content
                                img = Image.open(BytesIO(img_data))
                                img_width, img_height = img.size
                                # 检查分辨率
                                if img_width >= image_width or img_height >= image_height:
                                    idx += 1
                                    # 提取图片文件名
                                    img_filename = os.path.join(folder_path, f'image_{idx}.{img_url.split(".")[-1].split("?")[0]}')
                                    # 保存图片到指定目录
                                    with open(img_filename, 'wb') as img_file:
                                        img_file.write(img_data)

                                    print(f'Saved image: {img_filename}')
                            except Exception as e:
                                print(f"Error processing image: {str(e)}")

    # 关闭浏览器
    driver.quit()

