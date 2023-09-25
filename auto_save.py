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
import tkinter as tk
import tkinter.messagebox as messagebox
import threading
import sys
import datetime

# 禁用浏览器驱动程序的日志输出
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")  # 禁用日志输出

def start_download():
    global downloading, start_time
    start_time = time.time()
    if not downloading:
        try:
            download_status_label.config(text="下载中")
            # 获取用户在GUI中输入的配置变量
            url_authors = url_authors_entry.get('1.0', 'end')
            authors = url_authors.replace('\n', '').split(',')
            print(f"需要下载的内容有{authors}")
            browser = browser_entry.get()
            image_class = image_class_entry.get()
            image_width = int(image_width_entry.get())
            image_height = int(image_height_entry.get())

            downloading = True
            messagebox.showinfo("提示", "下载已开始，请点击确认")

            # 在单独的线程中执行下载任务
            download_thread = threading.Thread(target=task_download,
                                               args=(authors, browser.lower(), image_class, image_width, image_height))
            download_thread.start()

        except Exception as e:
            download_status_label.config(text="出错了")
            messagebox.showerror("错误", f"下载失败: {str(e)}")


def stop_download():
    global downloading, start_time
    downloading = False
    download_status_label.config(text="空闲中")
    if start_time > 0:
        print(f"总共耗时{round(time.time() - start_time, 1)}s")
        start_time = 0
    messagebox.showinfo("提示", "下载已停止")


def task_download(authors, browser, image_class, image_width, image_height):
    global downloading, toggle_var

    # 用于存储已下载图片的哈希值，以避免下载重复图片
    check_images = set()

    # 创建保存图片的目录
    image_dir = 'downloaded_images'
    os.makedirs(image_dir, exist_ok=True)

    if toggle_var.get() == 1:
        for url_author in authors:
            if not downloading:
                print("下载中止")
                return
            # 初始化WebDriver，根据json选择不同浏览器
            driver = check_browser(browser)

            # 打开网页A
            driver.get(url_author)

            need_to_do = []

            print(f"任务{url_author.split('/')[-1]}开始")

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
                if not downloading:
                    driver.quit()
                    print("下载中止")
                    return
                driver.quit()
                driver = check_browser(browser)
                try:
                    driver.get(url)
                    # 等待元素加载，直到找到元素或超时（最多等待 10 秒）
                    wait = WebDriverWait(driver, 10)
                    # wait.until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
                    wait.until(lambda driver: any(
                        x.get_attribute('class') == image_class for x in driver.find_elements(By.TAG_NAME, 'img')))
                    print(f"开始查询{url.split('/')[-1]}...")

                    for img_element in driver.find_elements(By.TAG_NAME, 'img'):
                        if not downloading:
                            driver.quit()
                            print("下载中止")
                            return
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
                                                img_filename = os.path.join(folder_path,
                                                                            f'image_{idx}.{img_url.split(".")[-1].split("?")[0]}')
                                                # 保存图片到指定目录
                                                with open(img_filename, 'wb') as img_file:
                                                    img_file.write(img_data)

                                                print(f'Saved image: {img_filename}')
                                        except Exception as e:
                                            download_status_label.config(text="出错了")
                                            print(f"Error processing image: {str(e)}")
                except Exception as exx:
                    with open("timeout.txt", 'a') as file:
                        file.write(f"{datetime.datetime.now()}---{url}\n")
                    download_status_label.config(text="有超时发生\n超时链接记录至txt文件内")
                    print(f"Error processing image: {str(exx)}")
            # 关闭浏览器
            driver.quit()
            print(f"任务{url_author.split('/')[-1]}完成")
    else:
        need_to_do = authors
        idx = 0
        for url in need_to_do:
            # 初始化WebDriver，根据json选择不同浏览器
            driver = check_browser(browser)
            print(f"任务{url.split('/')[-1]}开始...")
            # 创建新文件夹
            folder_name = f'folder_{url.split("/")[-1]}'
            folder_path = os.path.join(image_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            if not downloading:
                driver.quit()
                print("下载中止")
                return

            try:
                driver.get(url)
                # 等待元素加载，直到找到元素或超时（最多等待 10 秒）
                wait = WebDriverWait(driver, 10)
                # wait.until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
                wait.until(lambda driver: any(
                    x.get_attribute('class') == image_class for x in driver.find_elements(By.TAG_NAME, 'img')))

                for img_element in driver.find_elements(By.TAG_NAME, 'img'):
                    if not downloading:
                        driver.quit()
                        print("下载中止")
                        return
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
                                            img_filename = os.path.join(folder_path,
                                                                        f'image_{idx}.{img_url.split(".")[-1].split("?")[0]}')
                                            # 保存图片到指定目录
                                            with open(img_filename, 'wb') as img_file:
                                                img_file.write(img_data)

                                            print(f'Saved image: {img_filename}')
                                    except Exception as e:
                                        download_status_label.config(text="出错了")
                                        print(f"Error processing image: {str(e)}")
            except Exception as exx:
                with open("timeout.txt", 'a') as file:
                    file.write(f"{datetime.datetime.now()}---{url}\n")
                download_status_label.config(text="有超时发生\n超时链接记录至txt文件内")
                print(f"Error processing image: {str(exx)}")
            driver.quit()
            print(f"任务{url.split('/')[-1]}完成")

    print("所有任务已完成")
    stop_download()


def check_browser(browser):
    if browser == 'edge':
        driver = webdriver.Edge()
    elif browser == 'chrome':
        driver = webdriver.Chrome(options=options)
    else:
        download_status_label.config(text="出错了")
        raise Exception("请在输入框中设置合适的浏览器")
    return driver


def on_closing():
    global downloading  # 引用全局变量
    if downloading:
        downloading = False  # 等待下载线程完成
    root.destroy()


# 重定向print到文本框
def redirect_print(*args):
    text = ' '.join(map(str, args))
    output_text.insert(tk.END, text + '\n')
    output_text.see(tk.END)  # 自动滚动文本框到最底部


# 创建两个状态的开关按钮
def toggle_on():
    toggle_var.set(1)  # 设置为打开状态


def toggle_off():
    toggle_var.set(0)  # 设置为关闭状态


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # 使用pythonw.exe代替python.exe来运行
    sys.stdout = sys.stderr = open(os.devnull, 'w')

# 读取配置文件
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

default_browser = config.get('browser', 'edge').lower()
default_image_class = config.get('image_class', 'img img-fluid block-center img-fit')
default_image_width = config.get('image_width', '480')
default_image_height = config.get('image_height', '270')

# 创建GUI窗口
root = tk.Tk()
root.title("Auto_Save")

# 创建URL输入框
url_authors_label = tk.Label(root, text="urls:\n(链接用逗号隔开)")
url_authors_label.grid(row=0, column=0, padx=10, pady=0)  # 使用padx和pady设置外部间距
url_authors_entry = tk.Text(root, height=10, width=45)
url_authors_entry.grid(row=0, column=1, pady=15)

# 创建浏览器选项
browser_label = tk.Label(root, text="browser:\n(edge或chrome)")
browser_label.grid(row=1, column=0, padx=10, pady=5)
browser_entry = tk.Entry(root, width=45)
browser_entry.grid(row=1, column=1, pady=15)
browser_entry.insert(0, default_browser)

# 创建图像类别
image_class_label = tk.Label(root, text="image_class:\n(不知道就别改)")
image_class_label.grid(row=2, column=0, padx=10, pady=5)
image_class_entry = tk.Entry(root, width=45)
image_class_entry.grid(row=2, column=1, pady=15)
image_class_entry.insert(0, default_image_class)

# 创建图像宽度阈值
image_width_label = tk.Label(root, text="image_width:")
image_width_label.grid(row=3, column=0, padx=10, pady=5)
image_width_entry = tk.Entry(root, width=45)
image_width_entry.grid(row=3, column=1, pady=15)
image_width_entry.insert(0, str(default_image_width))

# 创建图像高度阈值
image_height_label = tk.Label(root, text="image_height:")
image_height_label.grid(row=4, column=0, padx=10, pady=5)
image_height_entry = tk.Entry(root, width=45)
image_height_entry.grid(row=4, column=1, pady=15)
image_height_entry.insert(0, str(default_image_height))

# 创建一个Label组件来显示下载状态
download_status_label = tk.Label(root, text="空闲中", width=20)
download_status_label.grid(row=5, column=2, padx=10, pady=0)

# 创建文本框来显示print的内容
output_text = tk.Text(root, height=26, width=60)
output_text.grid(row=0, column=2, rowspan=5, padx=30, pady=0)

# 重定向标准输出和标准错误
sys.stdout.write = redirect_print
sys.stderr.write = redirect_print

# 创建一个整数变量以存储开关状态（1表示根据作者，0表示直接按url）
toggle_var = tk.IntVar()
toggle_var.set(1)  # 初始状态为1

# 创建“打开”状态的按钮
open_button = tk.Radiobutton(root, text="根据作者", variable=toggle_var, value=1, command=toggle_on)
open_button.grid(row=5, column=0, padx=2, pady=0)

# 创建“关闭”状态的按钮
close_button = tk.Radiobutton(root, text="根据URL", variable=toggle_var, value=0, command=toggle_off)
close_button.grid(row=6, column=0, padx=2, pady=0)

root.protocol("WM_DELETE_WINDOW", on_closing)

# 创建开始按钮
start_button = tk.Button(root, text="开始下载", command=start_download)
start_button.grid(row=5, column=1, padx=0, pady=10)

# 创建停止按钮
stop_button = tk.Button(root, text="停止下载", command=stop_download)
stop_button.grid(row=6, column=1, padx=0, pady=5)

# 初始化变量以跟踪下载状态
downloading = False

root.geometry("920x500")

start_time = 0  # 计时

# 运行Tkinter事件循环
root.mainloop()
