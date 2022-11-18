# MultiBaiduSpider
多线程百度图片爬虫

    # 线程数量
    threadNumber = 12
    # tasks 表示{爬取名称：爬取数量}
    tasks = {"苹果特写": 10,"橘子特写":10,"香蕉特写":10,"葡萄特写":10,"草莓特写":10}
    # task_list 爬取的时候会在同级目录生成图片文件夹和图片url文件夹，{爬取名称：爬取图片前缀}
    task_list = {"苹果特写": "apple","橘子特写":"orange","香蕉特写":"Banana","葡萄特写":"grape","草莓特写":"strawberry"}