'''
Created on 2019年7月5日

@author: dell
'''
# 动态获取网址
#导入MySQLdb需要的安装的包是pip install mysqlclient
import MySQLdb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
import utils.parse_text_re as MyRe

# 获取页面招标信息，并调用MyRe来解析，content_class表示包含所有招标信息的容器的class名称（要包含招标标题）
# content_value表示招标内容中包含的文字，主要用于判断文字是否被加载出来
def crawl_page_data(url,content_class,content_value):
    try:
        browser.get(url)
        soup = BeautifulSoup(browser.page_source, "lxml")
        # 爬取网页信息
        # 需要等待信息全部加载后再读取
        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, content_class),content_value))
        info_text = soup.find(class_=content_class).get_text()
        info_text.encode('utf-8')
        parseData = MyRe.parse_local_data(info_text)
        # 将数据插入数据库
        cur.execute(
            "INSERT INTO spider_data(jia_name,jia_contact_way,jia_linkman,yi_name,yi_contact_way,yi_linkman,web_url,"
            "has_agency,address,content,money,amount,times) "
            "VALUES ("+parseData.jia_name+","+parseData.jia_contact_way+","+parseData.jia_linkman+","
            +parseData.yi_name+","+parseData.yi_contact_way+","+parseData.yi_linkman+","
            +parseData.web_url+","+parseData.has_agency+","+parseData.address+","
            +parseData.content+","+parseData.money+","+parseData.amount+","+parseData.time+")")





        # 保存到文本文档中，a+表示以读写且添加的方式写入，编码为utf-8，默认编码为gbk
        # with open('D:\\我的文档\\学习文档\\大三下\\2019刘老师实验室暑期实训\\data\\raw_data.txt', 'a+', encoding='utf-8') as f:
        #     f.write(info_text)
        #     # 作为分割
        #     f.write('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww')
        #     f.close()
    except Exception as e:
        print(e)



def parseSequence(pageNum):
    pageSequnece = pageNum.split("=")
    return pageSequnece[1]

def parseTime(pageTime):
    timeArr0 = pageTime.split("：")
    timeArr1 = timeArr0[1].split('-')
    timeStr = timeArr1[0] + timeArr1[1] + timeArr1[2]
    return timeStr

# 获取招标预警网所有公告的url,并调用crawl_page_data来获取页面内容
def get_warm_page_info():
    try:
        browser.get("https://www.job592.com/zb/wuhan.html")  # 起始地址
        input = browser.find_element_by_id('keywords')  # 找到id为kw的元素
        input.send_keys("医院 中标公告")  # 敲入要搜索的关键字
        input.send_keys(Keys.ENTER)  # 敲入回车
        wait = WebDriverWait(browser, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'c_swrap')))  # 等待某个元素加载出来
        browser.switch_to.window(browser.window_handles[1])  # 切换到跳转后的标签页
        # myWait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sd_page')))  # 等待某个元素加载出来
        wait.until(EC.text_to_be_present_in_element((By.ID, "resultpage"), u"下一页"))  # 因为下一页按钮是动态加载的，所以不能直接等待class加载。
        # 得到总页数
        totalPage = browser.find_element_by_css_selector('#resultpage > a:nth-last-child(2)').text
        print(totalPage)
        i = 0
        while i < int(totalPage):
            i = i + 1
            wait.until(EC.text_to_be_present_in_element((By.ID, "resultpage"), u"下一页"))
            html = browser.page_source
            # pq模块解析网页源代码
            doc = pq(html)
            pageUrlInfos = doc(".artitem").items()
            for pageUrlInfo in pageUrlInfos:
                #定位到url
                pageNum = pageUrlInfo("h2 a").attr("href")
                pageTime = pageUrlInfo(".afoot > span:last-child").text()
                #组合得到可访问的url
                theUrl = "https://show.job592.com/zb/" + parseTime(pageTime) + "_" + parseSequence(pageNum) + ".html"
                # 在这里调用解析详情的函数
                crawl_page_data(theUrl,"c_swrap","中标")
                print(theUrl)
            # 获取到下一页的按钮
            nextPage = browser.find_element_by_css_selector('#resultpage > a:last-child')
            nextPage.click()

    finally:
        # print(allUrl[0])
        # browser.close()
        print("hahaha")

# 对武汉市第一人民医院进行爬取
def crawl_first_hospital_data():
    for i in range(1, 4):
        browser.get("http://www.whyyy.com.cn/search_news.aspx?keyword=中标&page=" + str(i))
        html = browser.page_source
        # pq模块解析网页源代码
        doc = pq(html)
        pageUrlItems = doc('.news_txtlist li a').items()
        for pageUrlItem in pageUrlItems:
            pageUrl = "http://www.whyyy.com.cn" + pageUrlItem.attr("href")
            print(pageUrl)
            crawl_page_data(pageUrl,'list_aboutpage','中标')

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})  # 不加载图片,加快访问速度
    options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
    chromedriver_path = "C:\Program Files (x86)\Google\Chrome\Application/chromedriver.exe"  # 改成你的chromedriver的完整路径地址
    browser = webdriver.Chrome(executable_path=chromedriver_path, options=options)
    wait = WebDriverWait(browser, 10)  # 超时时长为10s
    try:
        # 连接数据库，改成自己数据的名称和密码
        conn = MySQLdb.connect(host="localhost", user="root", passwd="123456", db="spider_data",encoding='utf-8')
        # 创建游标
        cur = conn.cursor()
        # 调用解析函数
        # 爬取招标预警网
        # get_warm_page_info()
        # 爬取武汉市第一人民医院信息
        crawl_first_hospital_data()

         # 解析函数调用结束后关闭数据库,确保数据库被关闭
    finally:
        cur.close()
        conn.commit()
        conn.close()








