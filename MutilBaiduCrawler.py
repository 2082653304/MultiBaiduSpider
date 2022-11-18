# -*- coding:utf-8 -*-
import argparse
import logging
import os
import queue
import re
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
import openpyxl
import pandas as pd
import threading
import time

# 设置超时
timeout = 5
socket.setdefaulttimeout(timeout)

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] - %(asctime)s - %(filename)s[line:%(lineno)d]: %(message)s')


class Crawler:
    # 睡眠时长
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 30

    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, task, task_list, tasks, t=0.1):
        self.time_sleep = t
        self.task = task
        self.tasks = tasks
        self.task_list = task_list

    # 获取后缀名
    @staticmethod
    def get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result

    # 保存图片
    def save_image(self, rsp_data, word, task_list):
        if not os.path.exists("./images/" + word):
            os.makedirs("./images/" + word)
        # 判断名字是否重复，获取图片长度
        self.__counter = len(os.listdir('./images/' + word)) + 1

        for image_info in rsp_data['data']:
            try:
                if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                    continue
                obj_url = image_info['replaceUrl'][0]['ObjUrl']
                thumb_url = image_info['thumbURL']
                url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (
                    urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                time.sleep(self.time_sleep)
                suffix = self.get_suffix(obj_url)
                # 指定UA和referrer，减少403
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    ('User-agent',
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'),
                ]
                urllib.request.install_opener(opener)
                # 保存图片
                filepath = './images/%s/%s' % (word, str(task_list[word]) + "_" + str(self.__counter) + str(suffix))
                urllib.request.urlretrieve(url, filepath)
                if self.__counter >= self.tasks[self.task] + 1:
                    break
                self.sickDataFrame.iloc[self.__counter, 0] = str(task_list[word]) + "_" + str(self.__counter)
                self.sickDataFrame.iloc[self.__counter, 1] = thumb_url
                # self.sick_index += 1

                if os.path.getsize(filepath) < 5:
                    logging.warning("下载到了空文件，跳过!")
                    os.unlink(filepath)
                    continue
            except urllib.error.HTTPError as urllib_err:
                logging.warning("urllib.error.HTTPError: " + str(urllib_err))
                continue
            except Exception as err:
                time.sleep(1)
                logging.warning("Function[save_image] error: 产生未知错误，放弃保存")
                logging.warning("the error is: " + str(err))
                continue
            else:
                if self.__counter % 50 == 0:
                    logging.info("已有" + str(self.__counter) + "张【" + self.task + "】图")
                self.__counter += 1
                if self.__counter > self.tasks[self.task]:
                    break
        return

    # 开始获取
    def get_images(self, word, task_list):
        search = urllib.parse.quote(word)
        # pn int 图片数
        pn = self.__start_amount
        # 如果保存在一个csv的不同表单中可以打开下面
        # if not os.path.exists("./data/sick.xlsx"):
        #     writer = pd.ExcelWriter("./data/sick.xlsx")
        # else:
        #     book = openpyxl.load_workbook("./data/sick.xlsx")
        #     writer = pd.ExcelWriter("./data/sick.xlsx")
        #     writer.book = book
        # writer = pd.ExcelWriter("./data/sick.xlsx", engine='openpyxl')
        # book = openpyxl.load_workbook("./data/sick.xlsx")
        # writer.book = book
        # self.sick_index = 0
        sickCol = ["pic_id", "thumbURL"]
        self.sickDataFrame = pd.DataFrame(columns=sickCol, index=range(self.tasks[self.task] + 1))
        error_index = 0
        antiClimbIndex = 0
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
                search, search, str(pn), self.__per_page)
            # 设置header防403
            try:
                if self.__counter > self.tasks[self.task]:
                    break
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'],
                                                                  page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except Exception as e:
                logging.warning("Function[get_images] error: " + str(e))
                error_index += 1
                if error_index > 5:
                    break

            else:
                if self.__counter > self.tasks[self.task]:
                    break
                # 解析json
                try:
                    rsp_data = json.loads(rsp, strict=False)
                except:
                    pass
                if 'data' not in rsp_data:
                    antiClimbIndex += 1
                    if antiClimbIndex % 10 == 0:
                        logging.warning("触发了10次反爬机制，已自动重试！")
                    if antiClimbIndex > 10000:
                        break
                else:
                    if self.__counter > self.tasks[self.task]:
                        break
                    self.save_image(rsp_data, word, task_list)
                    # 读取下一页
                    if (pn % self.__per_page) % 10 == 0:
                        logging.info("正在下载: " + word + "第" + str(pn % self.__per_page + 1) + "页")
                    pn += self.__per_page

        base_save_path = "./data"
        if not os.path.exists(base_save_path):
            os.mkdir(base_save_path)
        save_path = base_save_path + "/" + self.task + ".xlsx"
        self.sickDataFrame.to_excel(save_path, sheet_name=self.task, index=False)
        # writer.save()
        # writer.close()
        logging.info("下载任务结束")
        return

    def start(self, task_list, total_page=1, start_page=1, per_page=30):
        """
        爬虫入口
        :param task_list: 保存格式前缀
        :param total_page: 需要抓取数据页数 总抓取图片数量为 页数 x per_page
        :param start_page:起始页码
        :param per_page: 每页数量
        :return:
        """
        self.__per_page = per_page
        self.__start_amount = (start_page - 1) * self.__per_page
        self.__amount = total_page * self.__per_page + self.__start_amount
        self.get_images(self.task, task_list)


class MyThread(threading.Thread):
    def __init__(self, name, tasks, task_list, work_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.tasks = tasks
        self.task_list = task_list
        self.work_queue = work_queue

    def getTask(self):
        while True:
            try:
                crawler = Crawler(self.work_queue.get(), self.task_list, self.tasks, 0.05)  # 抓取延迟为 0.05
                crawler.start(self.task_list, 100, 1, 60)
                if self.work_queue.empty():
                    logging.info("【" + self.name + "】completes the task")
                    break
            except Exception as e:
                logging.warning("Function[getTask] error: " + str(e))
                break

    def run(self):
        self.getTask()


def MyRun(tasks, task_list, threadNumber):
    start = time.time()
    work_queue = queue.Queue(len(tasks))
    for task in tasks:
        work_queue.put(task)

    threads = []
    for i in range(threadNumber if threadNumber < work_queue.qsize() else work_queue.qsize()):
        thread = MyThread("Thread-" + str(i), tasks, task_list, work_queue)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    end = time.time()
    logging.info("Queue多线程爬虫耗时：{} s".format(end - start))


if __name__ == '__main__':
    # 线程数量
    threadNumber = 12
    # tasks 表示{爬取名称：爬取数量}
    tasks = {"苹果特写": 10,"橘子特写":10,"香蕉特写":10,"葡萄特写":10,"草莓特写":10}
    # task_list 爬取的时候会在同级目录生成图片文件夹和图片url文件夹，{爬取名称：爬取图片前缀}
    task_list = {"苹果特写": "apple","橘子特写":"orange","香蕉特写":"Banana","葡萄特写":"grape","草莓特写":"strawberry"}

    MyRun(tasks, task_list, threadNumber)
