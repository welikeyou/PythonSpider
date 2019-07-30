# encoding:utf-8
import re

# 对爬取的数据使用正则表达式获取


# constants for chinese_to_arabic
CN_NUM = {
    '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
    '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
}

CN_UNIT = {
    '十': 10,
    '拾': 10,
    '百': 100,
    '佰': 100,
    '千': 1000,
    '仟': 1000,
    '万': 10000,
    '萬': 10000,
    '亿': 100000000,
    '億': 100000000,
    '兆': 1000000000000,
}


def find_chinese_start_index(cn: str):
    startIndx = len(cn)
    for cn_num in CN_NUM:
        tempIndex = cn.find(cn_num)
        if tempIndex != -1:
            startIndx = min(startIndx, tempIndex)
    return startIndx


# 处理金额，将大写汉字金额转换为阿拉伯数字,并转换为以万为单位
def chinese_to_arabic(cn: str) -> int:
    unit = 0  # current
    ldig = []  # digest
    for cndig in reversed(cn):
        if cndig in CN_UNIT:
            unit = CN_UNIT.get(cndig)
            if unit == 10000 or unit == 100000000:
                ldig.append(unit)
                unit = 1
        else:
            dig = CN_NUM.get(cndig)
            if unit:
                dig *= unit
                unit = 0
            ldig.append(dig)
    if unit == 10:
        ldig.append(10)
    val, tmp = 0, 0
    for x in reversed(ldig):
        if x == 10000 or x == 100000000:
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val / 10000


# 处理日期，将日期统一转换为yyyy-mm-dd的格式
'''
    可以格式化的日期类型
    str1 = '  2019-01-08'
    str2 = '2019-1-8 00:00:00'
    str3 = '2019年1月8日'
    str4 = '2019年01月08日'
    str5 = '2019/1/8'
    str6 = '2019/01/08 00:00'
    str7 = '2019-1-8'
'''


def str2date(str_date):
    str_date = str_date.strip()
    year = 1900
    month = 1
    day = 1
    if (len(str_date) > 11):
        str_date = str_date[:11]
    if (str_date.find('-') > 0):
        year = str_date[:4]
        if (year.isdigit()):
            year = int(year)
        else:
            year = 0
        month = str_date[5:str_date.rfind('-')]
        if (month.isdigit()):
            month = int(month)
        else:
            month = 0
        if (str_date.find(' ') == -1):
            day = str_date[str_date.rfind('-') + 1:]
        else:
            day = str_date[str_date.rfind('-') + 1:str_date.find(' ')]
        if (day.isdigit()):
            day = int(day)
        else:
            day = 0
    elif (str_date.find('年') > 0):
        year = str_date[:4]
        if (year.isdigit()):
            year = int(year)
        else:
            year = 0
        month = str_date[5:str_date.rfind('月')]
        if (month.isdigit()):
            month = int(month)
        else:
            month = 0
        day = str_date[str_date.rfind('月') + 1:str_date.rfind('日')]
        if (day.isdigit()):
            day = int(day)
        else:
            day = 0
    elif (str_date.find('/') > 0):
        year = str_date[:4]
        if (year.isdigit()):
            year = int(year)
        else:
            year = 0
        month = str_date[5:str_date.rfind('/')]
        if (month.isdigit()):
            month = int(month)
        else:
            month = 0
        if (str_date.find(' ') == -1):
            day = str_date[str_date.rfind('/') + 1:]
        else:
            day = str_date[str_date.rfind('/') + 1:str_date.find(' ')]
        if (day.isdigit()):
            day = int(day)
        else:
            day = 0
    else:
        year = 1900
        month = 1
        day = 1
    if month < 10:
        month = '0' + str(month)
    if day < 10:
        day = '0' + str(day)
    return '%s-%s-%s' % (year, month, day)


def distinguish_jia_yi(data, startIndex, endIndex, before, after):
    # before表示向上扩展，after表示向下扩展
    # 返回结果为1表示是甲方信息，返回结果为-1表示是乙方信息
    yi_len = 0
    jia_len = 0
    time = 0  # 控制循环次数
    while yi_len == 0 and jia_len == 0 and time < 5:
        time += 1
        subStr = data[startIndex:endIndex]
        jia_info = re.findall(r'采购|招标', subStr)
        yi_info = re.findall(r'代理|中标供应商|成交供应商|供应商|中标', subStr)
        yi_len = len(yi_info)
        jia_len = len(jia_info)
        # 如果搜索不到关键词就扩大搜索范围
        startIndex -= before
        endIndex += after
    if jia_len > yi_len:
        return 1
    else:
        return -1


class DataType:
    def __init__(self):
        self.jia_name = "null"
        self.jia_contact_way = "null"
        self.jia_linkman = "null"
        self.yi_name = "null"
        self.yi_contact_way = "null"
        self.yi_linkman = "null"
        self.web_url = "null"
        self.has_agency = "False"
        self.address = "null"
        self.content = "null"
        self.money = "null"
        self.amount = "null"
        self.time = "null"


def parse_local_data(data):
    # 统一编码格式
    #
    # 预处理，去掉空格
    data = data.replace(' ', '')
    data = data.replace(' ', '')
    data = data.replace('\n', '')
    parseData = DataType()

    # 控制循环次数
    time = 0

    # 区分甲方还是乙方的电话
    # 因为电话一般是在后面，所以取更多前面的信息
    try:
        jia_contact_way = re.search(r'(甲方联系方式|甲方电话|采购单位电话|采购单位联系方式|采购单位联系电话)(：)*((\d{3}-\d{8})|1\d{10}|\d{8})', data)
        if jia_contact_way:
            parseData.jia_contact_way = jia_contact_way.group(3)
            time += 1

        yi_contact_way = re.search(r'(代理机构联系方式|代理机构联系电话)(：)*((\d{3}-\d{8})|1\d{10}|\d{8})', data)
        if yi_contact_way:
            parseData.has_agency = True
            parseData.yi_contact_way = yi_contact_way.group(3)
            time += 1

        span = 0
        while time < 5 and span < len(data) and (jia_contact_way is None or yi_contact_way is None):
            time += 1
            group = False

            phoneNum = re.search(r'(电话|联系方式)(：)*((\d{3}-\d{8})|1\d{10}|\d{8})', data[span:len(data)])
            if phoneNum is None:
                phoneNum = re.search(r'((\d{3}-\d{8})|1\d{10}|\d{8})', data[span:len(data)])
                group = True
            startIndex = max(phoneNum.span()[0] - 20, 0)  # 先往前取50个字
            endIndex = phoneNum.span()[1]
            temp = span
            span += endIndex
            startIndex += temp
            endIndex += temp
            dis_num = distinguish_jia_yi(data, startIndex, endIndex, 20, 0)
            if dis_num > 0:
                if parseData.jia_contact_way == "null":
                    if group:
                        parseData.jia_contact_way = phoneNum.group()
                    else:
                        parseData.jia_contact_way = phoneNum.group(3)
            else:
                if parseData.yi_contact_way == "null":
                    if group:
                        parseData.yi_contact_way = phoneNum.group()
                    else:
                        parseData.yi_contact_way = phoneNum.group(3)
    except AttributeError:
        phoneNum = "null"
    print('jia_contact_way' + parseData.jia_contact_way)
    print('yi_contact_way' + parseData.yi_contact_way)

    # 区分甲方还是乙方的公司名称
    # 因为公司名称一般是在前面，所以取更多后面的信息
    try:
        # 每次初始化循环里的控制变量
        time = 0
        span = 0
        jia_name = re.search(r'(使用单位|甲方名称|采购单位|采购人|采购单位名称|招标人)(：)((([^，,、；。])*?)(医院|医科))', data)
        if jia_name:
            parseData.jia_name = jia_name.group(3)
            time += 1
        else:
            jia_name = re.search(r'(使用单位|甲方名称|采购单位|采购人|采购单位名称|招标人)((([^，,、；。])*?)(医院|医科))', data)
            if jia_name:
                parseData.jia_name = jia_name.group(2)
                time += 1

        yi_name = re.search(r'(乙方名称|供应商名称|供应商单位名称|中标人|中标单位名称)(：)((([^，,、；。])*?)公司)', data)
        if yi_name:
            parseData.yi_name = yi_name.group(3)
            time += 1
        else:
            yi_name = re.search(r'(乙方名称|供应商名称|供应商单位名称|中标人|中标单位)((([^，,、；。])*?)公司)', data)
            if yi_name:
                parseData.yi_name = yi_name.group(2)
                time += 1

        while time < 3 and span < len(data) and (jia_name is None or yi_name is None):
            time += 1
            name = re.search(r'(名称)(：)(((.[^，,、；。])*?)(公司|医院))', data[span:len(data)])

            startIndex = max(name.span()[0] - 10, 0)  # 先往前取20个字
            endIndex = name.span()[1] + 20
            temp = span
            span += endIndex
            startIndex += temp
            endIndex += temp
            dis_num = distinguish_jia_yi(data, startIndex, endIndex, 5, 20)
            if dis_num > 0:
                if parseData.jia_name == "null":
                    parseData.jia_name = name.group(3)
            else:
                if parseData.yi_name == "null":
                    parseData.yi_name = name.group(3)
    except AttributeError:
        name = "null"
    print("jia_name" + parseData.jia_name)
    print("yi_name" + parseData.yi_name)

    # 区分甲方还是乙方的联系人
    # 因为联系人一般是在中间，所以取更多前面的信息
    try:
        # 每次初始化控制循环里的控制变量
        time = 0
        span = 0
        jia_linkman = re.search(r'(甲方联系人|采购单位联系人)(：)([\u4E00-\u9FA5]{2,3})', data)
        if jia_linkman:
            parseData.jia_linkman = jia_linkman.group(3)
            time += 1
        yi_linkman = re.search(r'(乙方联系人|供应方联系人)(：)([\u4E00-\u9FA5]{2,3})', data)
        if yi_linkman:
            parseData.yi_linkman = yi_linkman.group(3)
            time += 1

        while time < 3 and span < len(data) and (jia_linkman is None or yi_linkman is None):
            time += 1
            linkman = re.search(r'(联系人)(：)([\u4E00-\u9FA5]{2,3})', data[span:len(data)])
            startIndex = max(linkman.span()[0] - 20, 0)  # 先往前取20个字
            endIndex = linkman.span()[1] + 20
            temp = span
            span += endIndex
            startIndex += temp
            endIndex += temp
            dis_num = distinguish_jia_yi(data, startIndex, endIndex, 20, 20)
            if dis_num > 0:
                if parseData.jia_linkman == "null":
                    parseData.jia_linkman = linkman.group(3)
            else:
                if parseData.yi_linkman == "null":
                    parseData.yi_linkman = linkman.group(3)
    except AttributeError:
        linkman = "null"
    print("jia_linkman:" + parseData.jia_linkman)
    print("yi_linkman:" + parseData.yi_linkman)

    try:
        parseData.content = re.search(r'(采购)*项目名称(：)(.[^、。，；]*?项目)', data).group(3)
        content_temp = re.match(r'(.*?)(结果|公示|公告)', data).group(1)
        if len(parseData.content) > len(content_temp):
            parseData.content = content_temp
    except AttributeError:
        try:
            parseData.content = re.match(r'(.*?)(中标公告|结果公示|中标公示)', data).group(1)
        except AttributeError:
            parseData.content = "null"
    print("content" + parseData.content)
    try:
        parseData.money = re.search(r'(((总中标|成交|中标|采购|投标)?金额)|报价|预算)[^、。，；]?(((\d+\.?\d*)万?元)|(.*?元整))',
                                    data).group(4)
        if parseData.money.endswith("整"):
            startInx = find_chinese_start_index(parseData.money)
            endInx = parseData.money.find("元")
            parseData.money = chinese_to_arabic(parseData.money[startInx:endInx])
        else:
            parseData.money = parseData.money[:-2]
    except AttributeError:
        parseData.money = "null"
    print('money:' + str(parseData.money))

    try:
        parseData.time = re.search(r'(时间|日期)[^、。，；1-9]*((\d+-\d+-\d{1,2})|(\d+年\d+月\d{1,2}日)|(\d+/\d+/\d{1,2}))',
                                   data).group(2)
    except AttributeError:
        try:
            parseData.time = re.search(r'(\d+-\d+-\d{1,2})|(\d+年\d+月\d+日)', data).group()
        except AttributeError:
            parseData.time = "null"
    if parseData.time != "null" and parseData.time.find('-') == -1:
        parseData.time = str2date(parseData.time)
    print('time' + parseData.time)
    try:
        parseData.amount = re.search(r'数量[^、。，；1-9]?(\d+)(台|套|件|个)?', data).group(1)
    except AttributeError:
        parseData.amount = "null"
    print('amount' + parseData.amount)
    return parseData


if __name__ == "__main__":
    data11 = "武汉市第一医院中医部2层病区改造工程中标公示 时间：2016-05-27 16:03:32 发布单位: 本站 武汉市第一医院于2016年5月26日上午8：30，在医院中西医结合二楼会议室，就中医部2层病区改造工程招标，招标编号：WHYYY-2016-015，经院评标委员会评审，现将中标结果公示如下：中标单位：武汉第七建设集团有限公司中标金额：63万元质 保 期：两年工    期：20天公 示 期：三个工作日投标人对上诉公示结果有异议，请在公示期内以书面形式向武汉市第一医院提出质疑，逾期将不再受理。招 标 人：武汉市第一医院地    址：武汉市桥口区中山大道215号（利济北路）联 系 人： 冯老师电    话： 85332020 武汉市第一医院                                  2016年5月27日"
    data = "武汉大学中南医院“ 皮肤科红光治疗仪2台”成交结果公示项目名称皮肤科红光治疗仪2台项目编号" \
           "WDZN-SBC-2018-071#采购形式竞争性磋商采购机构招投标管理办公室磋商时间" \
           "2018年8月22磋商地点1号楼13楼2号会议室公 示 内 容拟推荐成交供应商单位名称：武汉高科恒大光电有限" \
           "公司标的名称：红光治疗仪数量：2台报价（总价）：￥：23456.9质保期：5年产品制造商：武汉高科恒大光电" \
           "有限公司规格型号：GHX-630E-GN单位地址：武汉东湖开发区高新大道818号B8号生产孵化楼W/S-3未中标单位湖" \
           "北悦生医疗器械有限公司湖北济生医药有限公司公示时间：公示期为  2018  年  8 月 23 日至 2018 " \
           "年  8 月 24 日异议与投诉：投标人或者其他利害关系人对成交结果有异议的，应在成交结果公示之日起7个" \
           "工作日内以书面形式向采购人提出，采购人将自收到异议之日起7个工作日内作出书面答复。作出答复前，将暂" \
           "停采购活动。联系方式：采购人：武汉大学中南医院地址：湖北省武汉市武昌区东湖路169号招投标管理办" \
           "公室联系人：胡老师电话027-67812503纪检监察办公室联系人：余老师电话0" \
           "27-67813013  招投标管理办公室  2018 年 8 月 23 日"
    data1 = "西院中医科高频胸壁振荡排痰仪中标公告 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建" \
            "四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群" \
            "（785832389），结交更多朋友！招标信息网 招标详情西院中医科高频胸壁振荡排痰仪中标公告信息来源：中国国际招标网" \
            "发布时间：西院中医科高频胸壁振荡排痰仪中标公告发布时间：2019-07-11竞标信息： 项目编号竞价分类设备申请单位医学" \
            "工程科使用单位西院中医科币种人民币报名截止时间备注序号中标供应商名称中标产品数量(套/台)武汉医捷迅安商贸有限公司" \
            "高频胸壁振荡排痰仪null 地址：湖北省武汉市解放大道1277号 电话：027-85726090 友情提示： 为保证您能够顺利投标，" \
            "请在投标或购买招标文件前向招标代理机构或招标人咨询投标详细要求，具体要求及项目情况以招标代理机构或招标人的解释" \
            "为准。  Copyright  2016 |  job592.Com | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工" \
            "资待遇求职招聘我的职业圈意见反馈"
    data2 = "江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目中标公告 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），结交更多朋友！招标信息网 招标详情江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目中标公告信息来源：湖北省政府采购网发布时间：江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目中标公告根据武汉市江夏区政府采购计划执行确认书夏财采计【2019】00480号文要求，湖北中冠投资咨询有限公司受武汉市江夏区第一人民医院的委托，于2019年6月20日至2019年7月12日对“江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目”进行公开招标。现就本次采购的成交结果公告如下： 一、项目概况 （一）项目编号： （二）项目名称：江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目 （三）采购预算价：281.7万元（四）项目内容及需求 1.本次采购共分1个项目包，具体需求如下。详细技术规格、参数及要求见本项目采购文件第（ 三 ）章内容。 1）项目编号：2）项目名称：江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目3）项目内容：信息系统集成实施服务4）类别：服物5）用途：医疗 2.本项目投标报价超过采购预算价为无效投标。 二、招标文件内容（简要内容，全文见下方链接）详见附件三、供应商产生方式：通过发布公告 评审专家推荐供应商：北京麦迪克斯创新科技有限公司四、评审信息（一）评审时间： （二）评审地点：湖北中冠投资咨询有限公司江夏办事处开标室（武汉江夏经济开发区阳光一路中共武汉海德天物支部委员会三楼会议室） （三）评审专家名单黄艳,刘兰萍,王立超,汤文先,马敏五、成交结果信息（一）成交信息 1.项目编号： 2.项目名称：江夏区第一人民医院区域化急诊急救、远程诊断及胸痛中心建设项目 3.类别：服务 4.用途：医疗 5.采购预算：281.7万元 6.成交金额：万元 7.成交供应商名称：北京麦迪克斯创新科技有限公司 8.成交供应商地址：北京市海淀区高里掌路1号院11号楼1层3单元102 9.成交供应商企业类型： 10.交货期：签订合同后4个月内完成项目的交货、安装调试并通过采购人组织的验收后交付招标人正常使用 11.质保期：验收合格之日起按国家标准2年内免费质保，质保期内所有产品如有质量问题，严格按照国家相关三包政策规定执行 （二）未成交信息 各有关当事人对中标结果有异议的，可以在中标公告发布之日起七个工作日内以书面形式向本项目集中采购机构、政府采购代理机构或采购人提出质疑，逾期将不再受理六、联系事项 采购人联系方式： 采 购 人：武汉市江夏区第一人民医院地址：武汉江夏区文化大道1号联系人：祖主任       电 话： 集中采购机构或政府采购代理机构联系方式： 代理机构：湖北中冠投资咨询有限公司地址：武汉市江岸区幸福街圣诚阳光丽景4栋1205联系人：胡超电  话：七、监督管理部门监督管理部门：武汉市江夏区政府采购办公室联系电话：八、信息发布媒体（一）湖北省政府采购网 （网址： 湖北中冠投资咨询有限公司                                             2019年7月15日 人民医院 Copyright  2016 |  job592.Com | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工资待遇求职招聘我的职业圈意见反馈"
    data3 = "武汉市江夏区第一人民医院第七届世界军人运动会直接检眼镜等系列医疗专用设备购置项目中标结果公示 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），结交更多朋友！招标信息网 招标详情武汉市江夏区第一人民医院第七届世界军人运动会直接检眼镜等系列医疗专用设备购置项目中标结果公示信息来源：湖北省政府采购网发布时间：根据夏财采计【号执行确认书的要求，武汉盛泰百年招标有限公司受武汉市江夏区第一人民医院的委托，对其所需的第七届世界军人运动会直接检眼镜等系列医疗专用设备购置项目进行公开招标采购（招标编号：），开评标工作已于年月日结束，经评标委员会评审推荐、采购人确认，现就本次招标的中标结果公布如下：一、招标项目名称、用途、简要技术要求及合同履行日期：项目名称：第七届世界军人运动会直接检眼镜等系列医疗专用设备购置项目用途：医用简要技术要求：详见中标人的投标文件合同履行日期（交货期）：签订合同后日内交付二、中标信息：产品名称及数量：直接检眼镜台、电脑验光仪台、焦度计个、综合验光仪台、间接眼底镜（含镜头）台、非接触眼压计台、裂隙灯显微镜台、电子鼻咽喉镜台、电耳镜台、综合治疗台台、听力计台中标供应商名称：北京汉华荣欣经贸有限公司中标供应商地址：北京市西城区国英园号楼层室、室产品规格型号：等制造商名称：苏州六六视觉科技股份有限公司、上海雄博精密仪器股份有限公司等交货期：签订合同后日内交付质保期：验收合格后壹年中标金额：人民币（大写）壹佰柒拾捌万贰仟元整（￥三、招标公告媒体：中国湖北政府采购网（招标公告日期：年月日四、评标信息：评标日期：年月日评标地点：武汉市武昌区中北路号知音广场写字楼层武汉盛泰百年招标有限公司号评标室评标委员会名单：邓力、文灯华、张德新、张金木、李卫海五：中标公告期限：个工作日六、本次招标联系事项：采购代理机构：武汉盛泰百年招标有限公司项目联系人：陈黎霞邹桃红联系电话：联系地址：武汉市武昌区中北路号知音广场写字楼层采购人：武汉市江夏区第一人民医院联系人：夏科长联系电话：联系地址：武汉市江夏区文化大道号如投标当事人对中标结果有异议的，可以在中标公示发布之日起七个工作日内，以书面形式向武汉盛泰百年招标有限公司提出质疑，逾期将不再受理。特此公示武汉盛泰百年招标有限公司年月日武汉盛泰百年招标有限公司人民医院武汉市江夏区第一人民医院 Copyright  2016 |  job592.Com | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工资待遇求职招聘我的职业圈意见反馈 "
    data4 = "华中科技大学同济医学院附属同济医院 3.0t磁共振采购项目中标结果公告(1) - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），结交更多朋友！招标信息网 招标详情华中科技大学同济医学院附属同济医院 3.0t磁共振采购项目中标结果公告(1)信息来源：中国国际招标网发布时间：华中科技大学同济医学院附属同济医院 3.0T磁共振采购项目中标结果公告(1)发布时间：2019-07-11项目名称：华中科技大学同济医学院附属同济医院 3.0T磁共振采购项目 项目编号：0616-1940WH195009 招标范围：华中科技大学同济医学院附属同济医院 3.0T磁共振采购项目 1台（套） 招标机构：湖北省招标股份有限公司 招标人：华中科技大学同济医学院附属同济医院 开标时间：2019-06-19 09:30 公示时间：2019-07-01 12:44 - 2019-07-04 23:59 中标结果公告时间：2019-07-11 00:05 中标人：湖北人福医药集团有限公司 制造商：通用电气公司 制造商国家或地区：美国 友情提示： 为保证您能够顺利投标，请在投标或购买招标文件前向招标代理机构或招标人咨询投标详细要求，具体要求及项目情况以招标代理机构或招标人的解释为准。湖北省招标股份有限公司医学院 Copyright  2016 |  job592.Com | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工资待遇求职招聘我的职业圈意见反馈"
    data5 = "武汉市东西湖区人民医院心电网络及配套软件采购项目中标公告 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福" \
            "建四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），结" \
            "交更多朋友！招标信息网 招标详情武汉市东西湖区人民医院心电网络及配套软件采购项目中标公告信息来源：中国政府采购网发布时间：　　湖" \
            "北依联体招标咨询有限公司受武汉市东西湖区人民医院的委托，就“武汉市东西湖区人民医院心电网络及配套软件采购项目”项目（项目编号：" \
            "YLT-1906ZH-024）组织采购，评标工作已经结束，中标结果如下：一、项目信息项目编号：YLT-1906ZH-024项目名称：武汉市东西湖区人民医院" \
            "心电网络及配套软件采购项目项目联系人：刘自强联系方式：027-83899224二、采购单位信息采购单位名称：武汉市东西湖区人民医院采购单位" \
            "地址：湖北省武汉市东西湖区环山路81号采购单位联系方式：刘自强027-83899224三、项目用途、简要技术要求及合同履行日期：详见招标文件" \
            "四、采购代理机构信息采购代理机构全称：湖北依联体招标咨询有限公司采购代理机构地址：武汉市武昌区民主路782号洪广大酒店23层采购代" \
            "理机构联系方式：徐鹏、喻红027-87819897-809五、中标信息招标公告日期：2019年06月19日中标日期：2019年07月10日总中标金额：128.8 万" \
            "元（人民币）中标供应商名称、联系地址及中标金额：序号中标供应商名称中标供应商联系地址中标金额(万元)武汉医岚商贸有限公司武汉市东" \
            "西湖区水产养殖场钢结构产品生产扩建项目综合楼-1栋1-12层本项目招标代理费总金额：1.8168 万元（人民币）本项目招标代理费收费标准：" \
            "依据计价格[2002]1980号《招标代理服务费收费管理暂行办法》收取评审专家名单：李涛、高洁、张志彬、罗诚、郑富强中标标的名称、规格型" \
            "号、数量、单价、服务要求：中标人名称：武汉医岚商贸有限公司中标内容：心电网络及配套软件（含心电数据管理系统软件和数字式多道心电" \
            "图机）规格、型号: Zonnet ECG含武汉中旗数字式多道心电图机 数量 （台/套）: 1套含心电数据管理系统软件1套/数字式多道心电图机36台中" \
            "标金额：人民币壹佰贰拾捌万捌仟元整（￥1,288,000.00）质 保 期：项目验收合格后2年六、其它补充事宜公告期限1个工作日。有关当事人对" \
            "中标结果有异议的，可以在中标公告发布之日起7个工作日内以书面形式向湖北依联体招标咨询有限公司提出质疑，逾期将不予受理。同时，感" \
            "谢各投标人对本次招标工作的支持，并希望在以后的招标工作中继续合作。人民医院武汉市东西湖区人民医院 Copyright  2016 |  job592.Com" \
            " | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工资待遇求职招聘我的职业圈意见反馈"
    data6 = "同济医院分院区数据中心改造及升级项目公开招标公告 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建" \
            "四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），" \
            "结交更多朋友！招标信息网 招标详情同济医院分院区数据中心改造及升级项目公开招标公告信息来源：中国政府采购网发布时间：　　湖北省" \
            "成套招标股份有限公司受华中科技大学同济医学院附属同济医院委托，根据《中华人民共和国政府采购法》等有关规定，现对同济医院分院区数据" \
            "中心改造及升级项目 进行公开招标，欢迎合格的供应商前来投标。项目名称：同济医院分院区数据中心改造及升级项目 项目编号：" \
            "项目联系方式：项目联系人：王科长项目联系电话：027-83662896采购单位联系方式：采购单位：华中科技大学同济医学院附属同济医院" \
            "地址：武汉市解放大道1095号联系方式：王科长；027-83662896代理机构联系方式：代理机构：湖北省成套招标股份有限公司代理" \
            "机构联系人：刘李鹏、胡小康； 027-87816666-8206、8209代理机构地址： 武昌区东湖西路平安财富中心B座7-10楼一、采购项目的" \
            "名称、数量、简要规格描述或项目基本概况介绍：包号内容采购需求（简要）预算金额/最高限价质量标准交货（安装）期/服务期质保期" \
            "/缺陷责任期备注数据中心改造及升级机房管线防结露保温，接缝处严密；楼板保温；更换扣板；空气循环区域防尘处理；使室内保持正压使尘埃" \
            "不易进入室内；机房内所有空洞及衔接处均密封；设立缓冲空间；完整的业务数据库迁移解决方案。210万元合格合同签订后60日历日内供货并" \
            "安装完毕，验收合格数据中心主机：5年，其余部分：2年二、投标人的资格要求：1. 符合《中华人民共和国政府采购法》第二十二条规定的" \
            "条件；2. 其他资格要求：提供投标人参加政府采购活动前3年内在经营活动中没有重大违法记录的书面声明（格式要求详见第六章相关格式）" \
            "3. 未被列入“信用中国”网站( www.creditchina.gov.cn)失信被执行人、重大税收违法案件当事人名单、政府采购严重违法失信行为记录名单" \
            "和“中国政府采购”网站（ www.ccgp.gov.cn）政府采购严重违法失信行为记录名单（以投标截止时间前查询结果为准）；4. 本次招标不接受联" \
            "合体投标。联合体投标的，应满足下列要求：本项目不适用。5. 如国家法律法规对市场准入有要求的还应符合相关规定。三、招标文件的发售时" \
            "间及地点等：预算金额：210.0 万元（人民币）时间：2019年07月12日 08:30 至 2019年07月18日 16:30(双休日及法定节假日除外)地点：湖北省成" \
            "套招标股份有限公司服务大厅 湖北省武汉市武昌区东湖西路特2号平安财富中心B座七楼。招标文件售价：￥300.0 元，本公告包含的招标文件售" \
            "价总和招标文件获取方式：供应商获取招标文件时须携带以下资料：供应商法定代表人凭法定代表人身份证明书（原件）或委托代理人凭法定" \
            "代表人授权书（原件）、本人身份证（原件）。 供应商需开具发票应提供以下内容：供应商单位名称、纳税人识别号或统一社会信用代码、" \
            "地址、电话、开户银行及账号。招标文件获取时间：2019年7月12日起至2019年7月18日每天上午8:30～12:00 、下午14:00～16:30 （节假" \
            "日除外）。四、投标截止时间：2019年08月01日 09:30五、开标时间：2019年08月01日 09:30六、开标地点：湖北省成套招标股份有限公司" \
            "10楼1009号会议室七、其它补充事宜八、采购项目需要落实的政府采购政策：中小企业、节能环保、监狱企业、促进残疾人就业湖北省成套" \
            "招标股份有限公司数据中心 Copyright  2016 |  job592.Com | All rights reserved | 招标信息预警网 | 版权所有 首页工资面试评价工资待遇求职招聘我的职业圈意见反馈 "
    data7 = "武汉市金银潭医院静脉用药调配中心项目磋商公告成交公告 - 招标预警网首页公众号关于我们全国全国北京上海广东天津重庆江苏浙江福建四川湖南湖北山东辽宁吉林云南安徽江西黑龙江河北陕西海南河南山西内蒙古广西贵州宁夏青海新疆西藏甘肃加入客户QQ群（785832389），结交更多朋友！招标信息网 招标详情武汉市金银潭医院静脉用药调配中心项目磋商公告成交公告信息来源：中国国际招标网发布时间：武汉市金银潭医院静脉用药调配中心项目磋商公告成交公告发布时间：2019-07-11公告信息：采购项目名称武汉市金银潭医院静脉用药调配中心项目磋商公告品目工程/其他建筑工程采购单位武汉市金银潭医院行政区域武汉市公告时间2019年07月11日 14:31本项目招标公告日期2019年06月26日成交日期2019年07月10日谈判小组、询价小组成员、磋商小组成员名单及单一来源采购人员名单邵林广、程冬娥、魏刚总成交金额￥129.809500 万元（人民币）联系人及联系方式：项目联系人常先生、王女士项目联系电话采购单位武汉市金银潭医院采购单位地址武汉市东西湖区银潭路1号采购单位联系方式范女士 027-85509033代理机构名称湖北创盛招标有限公司代理机构地址武汉市青山区和平大道建设二路吾行里写字楼1801号代理机构联系方式常先生、王女士 027-86666003湖北创盛招标有限公司受武汉市金银潭医院的委托，就“武汉市金银潭医院静脉用药调配中心项目磋商公告”项目（项目编号：QYGC-2019002）组织采购，评标工作已经结束，成交结果如下：一、项目信息项目编号：QYGC-2019002项目名称：武汉市金银潭医院静脉用药调配中心项目磋商公告项目联系人：常先生、王女士联系方式：027-86666003二、采购单位信息采购单位名称：武汉市金银潭医院采购单位地址：武汉市东西湖区银潭路1号采购单位联系方式：范女士 027-85509033三、采购代理机构信息采购代理机构全称：湖北创盛招标有限公司采购代理机构地址：武汉市青山区和平大道建设二路吾行里写字楼1801号采购代理机构联系方式：常先生、王女士 027-86666003四、成交信息招标文件编号：W19060192-0180本项目招标公告日期：2019年06月26日成交日期：2019年07月10日总成交金额：129.8095 万元（人民币）成交供应商名称、地址及成交金额：成交供应商名称： 湖北悦康绿源净化工程有限公司联系地址： 武汉市洪山区关山街曹家湾92号一楼（当代花园小区后）成交金额：￥1298095元； 人民币壹佰贰拾玖万捌仟零玖拾伍元整本项目代理费总金额：1.9471 万元（人民币）本项目代理费收费标准：成交金额的1.5%谈判小组、询价小组、磋商小组成员名单及单一来源采购人员名单：邵林广、程冬娥、魏刚五、项目用途、简要技术要求及合同履行日期：工程内容包括为武汉市金银潭医院静脉用药调配中心的装修改造、给排水安装、通风系统、电气照明安装、强弱电安装等，计划于2019年7月15日开工。六、成交标的名称、规格型号、数量、单价、服务要求：成交标的名称：武汉市金银潭医院静脉用药调配中心工程项目要求工期90天，质量合格。七、其它补充事宜本公告期限为1个工作日。友情提示： 为保证您能够顺利投标，请在投标或购买招标文件前向招标代理机构或招标人咨询投标详细要求，具体要求及项目情况以招标代理机构或招标人的解释为准。 "
    data8 = "当前位置：首页 » 政采公告 » 地方公告 » 中标公告武汉大学中南医院超声骨动力系统采购项目（三次）中标结果公告2019" \
            "年07月12日 17:41 来源：中国政府采购网 【打印】 【显示公告正文】【显示公告概要】公告概要：公告信息：采购项目名称武汉大学中" \
            "南医院超声骨动力系统采购项目品目货物/专用设备/医疗设备/医用超声波仪器及设备采购单位武汉大学中南医院行政区域武汉市公告时间2" \
            "019年07月12日  17:41本项目招标公告日期2019年06月21日中标日期2019年07月12日评审专家名单郑富强、徐文胜、姚迅、秦冬梅、胡超" \
            "总中标金额￥150.000000 万元（人民币）联系人及联系方式：项目联系人刘工项目联系电话027-87272702 采购单位武汉大学中南医院采" \
            "购单位地址武汉市武昌区东湖路169号采购单位联系方式邢老师 027-67812503代理机构名称湖北中天招标有限公司代理机构地址湖北省武" \
            "汉市武昌区中北路109号中铁1818中心10楼代理机构联系方式刘工027-87272702湖北中天招标有限公司受武汉大学中南医院的委托，就“武汉" \
            "大学中南医院超声骨动力系统采购项目”项目（项目编号：ZB0205-1904-ZCHW0021）组织采购，评标工作已经结束，中标结果如下： 一" \
            "、项目信息项目编号：ZB0205-1904-ZCHW0021项目名称：武汉大学中南医院超声骨动力系统采购项目项目联系人：刘工联系方式：027-87272702 " \
            " 二、采购单位信息采购单位名称：武汉大学中南医院采购单位地址：武汉市武昌区东湖路169号采购单位联系方式：邢老师 027-67812503 " \
            "三、项目用途、简要技术要求及合同履行日期：采购超声骨动力系统1套（技术要求详见招标文件第三章项目技术、服务及商务要求（已完" \
            "成进口论证）交货期：合同签订后两个月内，允许提前交货质保期：产品验收合格后至少12个月 四、采购代理机构信息采购代理机构全称" \
            "：湖北中天招标有限公司采购代理机构地址：湖北省武汉市武昌区中北路109号中铁1818中心10楼采购代理机构联系方式：刘工027-87272702 " \
            "五、中标信息招标公告日期：2019年06月21日中标日期：2019年07月12日总中标金额：150.0 万元（人民币）中标供应商名称、联系地址及" \
            "中标金额：中标单位名称：国药控股湖北医疗器械有限公司中标单位地址：武汉市东湖新技术开发区高新大道666号CRO办公区A19栋10楼B区中" \
            "标金额：人民币壹佰伍拾万元整（¥1,500,000.00）本项目招标代理费总金额：0.0 万元（人民币）本项目招标代理费收费标准：根据国家发展" \
            "与改革委员会办公厅发改办价格[2003]857号文的规定，经与采购人协商，由中标人按国家发展计划委员会计价格【2011】534号文及原国家计" \
            "委《招标代理服务收费管理暂行办法》（【2002】1980号）规定的标准向招标代理机构支付代理服务费。 评审专家名单：郑富强、徐文胜、" \
            "姚迅、秦冬梅、胡超 中标标的名称、规格型号、数量、单价、服务要求：中标单位名称：国药控股湖北医疗器械有限公司中标单位地址：武" \
            "汉市东湖新技术开发区高新大道666号CRO办公区A19栋10楼B区中标金额：人民币壹佰伍拾万元整（¥1,500,000.00）数量：1套交货期：合同签" \
            "订后30天内质保期：产品验收合格后5年 六、其它补充事宜1、公告媒体：中国政府采购网、中国招标投标公共服务平台、湖北中天招标有限" \
            "公司网站2、中标公告期限：1个工作日3、各有关当事人对中标结果有异议的，可以在中标公告发布之日起七个工作日内以书面形式向采购人及" \
            "采购代理机构提出质疑，逾期将不再受理。  相关公告"
    data9 = "武汉市第一医院2019年制作零星宣传物料项目中标公告时间：2019-04-22 08:00:00发布单位: OA武汉市第一医院制作零星宣传物料项目中标公告湖北中盛汇金项目管理有限公司受武汉市第一医院的委托，对其武汉市第一医院制作零星宣传物料项目进行公开招标采购。于2019年3月26日发布招标公告，评标工作已结束，中标结果公告如下：一、项目概况（一）项目编号：ZSHJ-2019-034（二）项目名称：武汉市第一医院制作零星宣传物料（三）采购预算：26万元（四）项目基本概况:	1.本次项目共分1 个包。详细技术规格、参数及要求见本项目招标文件第五章内容第1包：（1）项目包名称：武汉市第一医院制作零星宣传物料（2）类别（货物/工程/服务）：货物（3）用途：办公（4）数量：1（批）（5）采购预算：26万元（6）合同期限：1年（7）质保期：按各类货物行业标准执行8）其他：（无）	2.投标人参加投标的报价超过该包采购预算金额或最高限价的，其该包投标无效。	3.参加多包投标的相关规定：（无）二、评审信息（一）评审时间：2019-04-17（二）评标委员会名单：韩洪、张雯、李莉、魏文敏、王娟（三）评标地址：湖北中盛汇金项目管理有限公司（武汉市江岸区胜利街128号新源大厦4楼）会议室三、中标结果信息（一）中标信息第1包中标1. 项目包名称：武汉市第一医院制作零星宣传物料2. 中标供应商名称：中浩紫云科技股份有限公司3. 中标供应商地址：武汉市江汉区红旗渠路18号17A9-144. 中标金额：采用比率报价的项目78%5.  期限（服务期）：2年. 质保期：0（年）四、联系事项采购人联系方式：名称：武汉市第一医院地址：湖北省武汉市硚口区中山大道215号电话：027-85332742采购代理机构联系方式：名称：湖北中盛汇金项目管理有限公司地址：武汉市江岸区胜利街128号新源大厦4楼电话：027-82822990   82822296   82822091五、信息发布媒体中国政府采购网（http://www.ccgp.gov.cn/湖北中盛汇金项目管理有限公司2019年04月22日"
    data10 = " 武汉市第一医院2号楼肿瘤病区零星改造工程汇总中标公示 时间：2016-05-27 16:00:29 发布单位: 本站 武汉市第一医院于2016年5月26日上午8：30，在医院中西医结合二楼会议室，就2号楼肿瘤病区零星改造工程汇总招标，招标编号：WHYYY-2016-014，经院评标委员会评审，现将中标结果公示如下：中标单位：湖北中睿建设有限公司中标金额：59.2万元质 保 期：三年工    期：40天公 示 期：三个工作日投标人对上诉公示结果有异议，请在公示期内以书面形式向武汉市第一医院提出质疑，逾期将不再受理。招 标 人：武汉市第一医院地    址：武汉市桥口区中山大道215号（利济北路）联 系 人： 冯老师电    话： 85332020 武汉市第一医院                                  2016年5月27日   "
    '''

    x = chinese_to_arabic("一千一百二十三万四千五百六十七")
    print(x)

    '''
    parse_local_data(data8)
    parse_local_data(data)
    parse_local_data(data1)
    parse_local_data(data2)

    parse_local_data(data4)
    parse_local_data(data5)
    parse_local_data(data6)
    parse_local_data(data7)
    parse_local_data(data8)
    parse_local_data(data3)
