#render函数用于将数据渲染到指定的模板中，并返回生成的HTML内容
#redirect允许你将用户从一个URL重定向到另一个URL，通常用于处理单表提交、用户登录、注册等操作后的页面跳转
from django.db import models  # 核心修正点
from django.db.models import Q
from django.shortcuts import render,redirect
from app.models import User,TravelInfo
from app.recommdation import getUser_ratings,user_bases_collaborative_filtering
from app.utils import errorResponse,getHomeData,getPublicData,getChangeSelfInfoData,getAddCommentsData,getEchartsData,getRecommendationData
from django.contrib.auth.hashers import check_password  # 用于安全验证密码
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

def home(request):
    return render(request, 'app/home.html')
# def login(request):
#     if request.method == 'GET':
#         return render(request,'login.html')
#     else:
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         try:
#             User.objects.get(username=username, password=password)
#             request.session['username'] = username
#             return redirect('/app/home')
#
#         except:
#             return errorResponse.errorResponse(request,'账号或密码错误')


# def register(request):
#     if request.method == 'GET':
#         return render(request,'register.html')
#     else:
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         confirmPassword = request.POST.get('confirmPassword')
#         try:
#             User.objects.get(username=username)
#         except:
#             if not username or not password or not confirmPassword:return errorResponse.errorResponse(request,'不允许为空值')
#             if  password != confirmPassword:return errorResponse.errorResponse(request,'两次密码不一致')
#             User.objects.create(username=username,password=password)
#             return redirect('/app/login')
#
#         return errorResponse.errorResponse(request,'该账号已存在')
import django
import jieba
import pandas as pd
import imageio.v2 as imageio
from wordcloud import WordCloud
import wordcloud
import re
#todo  新的登录模块代码
def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 基本输入校验
        if not username or not password:
            return errorResponse.errorResponse(request, '用户名和密码不能为空')

        try:
            # 1. 查询用户是否存在
            user = User.objects.get(username=username)

            # 2. 使用 check_password 验证密码（与注册时的 make_password 匹配）
            if check_password(password, user.password):
                # 3. 登录成功：设置 session
                request.session['username'] = username
                return redirect('/app/home')
            else:
                # 密码错误
                return errorResponse.errorResponse(request, '账号或密码错误')

        except User.DoesNotExist:
            # 用户不存在
            return errorResponse.errorResponse(request, '账号或密码错误')

#todo  新的注册模块代码
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        # 校验输入
        if not username or not password or not confirm_password:
            return errorResponse.errorResponse(request, '不允许为空值')
        if password != confirm_password:
            return errorResponse.errorResponse(request, '两次密码不一致')

        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            return errorResponse.errorResponse(request, '该账号已存在')

        # 创建用户（使用 make_password 加密）
        user = User(username=username)
        user.set_password(password)  # 自动加密
        user.save()

        return redirect('/app/login')

def logOut(request):
    request.session.clear() #退出登录时，清除request.session
    return redirect('/app/login') #退出登录 转到登陆页面

def home(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    a5Len,commentsLenTitle,provienceDicSort = getHomeData.getHomeTagData()
    scoreTop10Data,saleCountTop10 = getHomeData.getAnthorData()
    year,mon,day = getHomeData.getNowTime()
    geoData = getHomeData.getGeoData()
    userBarCharData = getHomeData.getUserCreateTimeData()
    #字典
    return render(request,'home.html',{
        'userInfo':userInfo,
        'a5Len':a5Len,
        'commentsLenTitle':commentsLenTitle,
        'provienceDicSort':provienceDicSort,
        'scoreTop10Data':scoreTop10Data,
        'nowTime':{
            'year':year,
            'mon':getPublicData.monthList[mon - 1],
            'day':day
        },
        'geoData':geoData,
        'userBarCharData':userBarCharData,
        'saleCountTop10':saleCountTop10
    })

def changeSelfInfo(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year,mon,day = getHomeData.getNowTime()
    if request.method == 'POST':
        getChangeSelfInfoData.changeSelfInfo(username,request.POST,request.FILES)
        userInfo = User.objects.get(username=username)

    return render(request,'changeSelfInfo.html',{
        'userInfo':userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
    })

# def changePassword(request):
#     username = request.session.get('username')
#     userInfo = User.objects.get(username=username)
#     year, mon, day = getHomeData.getNowTime()
#     if request.method == 'POST':
#         res = getChangeSelfInfoData.getChangePassword(userInfo,request.POST)
#         if res != None:
#             return errorResponse.errorResponse(request,res)
#
#     return render(request, 'changePassword.html', {
#         'userInfo': userInfo,
#         'nowTime': {
#             'year': year,
#             'mon': getPublicData.monthList[mon - 1],
#             'day': day
#         },
#     })




#todo   新的修改密码代码
def changePassword(request):
    # 验证登录状态
    username = request.session.get('username')
    if not username:
        return redirect('/app/login')

    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        return errorResponse.errorResponse(request, '用户不存在')

    if request.method == 'POST':
        # 获取表单数据（字段名称与前端完全一致）
        old_password = request.POST.get('oldPassword', '').strip()  # 注意这里是 oldPassword
        new_password = request.POST.get('newPassword', '').strip()  # 注意这里是 newPassword
        confirm_password = request.POST.get('newPasswordConfirm', '').strip()  # 注意这里是 newPasswordConfirm

        # 字段非空校验
        if not all([old_password, new_password, confirm_password]):
            return errorResponse.errorResponse(request, '所有字段不能为空')

        # 验证旧密码
        if not userInfo.check_password(old_password):
            return errorResponse.errorResponse(request, '原密码错误')

        # 验证新密码一致性
        if new_password != confirm_password:
            return errorResponse.errorResponse(request, '两次新密码不一致')

        # 更新密码
        userInfo.set_password(new_password)
        userInfo.save()

        # 清除会话并跳转登录
        request.session.flush()
        return redirect('/app/home')

    # GET请求处理（保持原有时间逻辑）
    year, mon, day = getHomeData.getNowTime()
    return render(request, 'changePassword.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
    })


# def tableData(request):
#     username = request.session.get('username')
#     userInfo = User.objects.get(username=username)
#     year, mon, day = getHomeData.getNowTime()
#     talbeData = getPublicData.getAllTravelInfoMapData()
#     return render(request, 'tableData.html', {
#         'userInfo': userInfo,
#         'nowTime': {
#             'year': year,
#             'mon': getPublicData.monthList[mon - 1],
#             'day': day
#         },
#         'talbeData':talbeData
#     })


# todo 新增搜索功能和分页功能
def tableData(request):
    # 用户信息获取
    username = request.session.get('username')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        # 处理用户不存在的情况，这里可以重定向到登录页
        return redirect('login')

    # 获取当前时间
    year, mon, day = getHomeData.getNowTime()

    # 读取Excel数据
    try:
        df = pd.read_excel(r'D:\data.xlsx')
        # 去除包含空值的行
        #df = df.dropna()
        # 将DataFrame转换为列表字典格式，方便模板渲染
        all_data = df.to_dict('records')
    except Exception as e:
        # 处理文件读取错误，返回空数据集或默认数据
        all_data = []

    # 获取筛选条件和排序方式
    selected_product_attributes = request.GET.get('product_attributes', '')
    selected_usage_scenarios = request.GET.get('usage_scenarios', '')
    selected_ranking_types = request.GET.get('ranking_types', '')
    sort_by = request.GET.get('sort_by', 'weekly_sales_quantity')  # 默认按周销售数量排序

    # 筛选数据
    filtered_data = all_data.copy()  # 复制所有数据作为初始筛选集
    if selected_product_attributes:
        filtered_data = [item for item in filtered_data if item.get('商品属性') == selected_product_attributes]
    if selected_usage_scenarios:
        filtered_data = [item for item in filtered_data if item.get('使用场景') == selected_usage_scenarios]
    if selected_ranking_types:
        filtered_data = [item for item in filtered_data if item.get('榜单类型') == selected_ranking_types]

    # 排序数据
    if sort_by == 'weekly_sales_amount':
        filtered_data.sort(key=lambda x: x.get('周销售额', 0), reverse=True)
    else:
        filtered_data.sort(key=lambda x: x.get('周销售数量', 0), reverse=True)

    # 分页处理
    paginator = Paginator(filtered_data, 10)  # 每页10条
    page_number = request.GET.get('page', 1)

    try:
        tableData = paginator.page(page_number)
    except EmptyPage:
        # 如果页码超出范围，返回最后一页
        tableData = paginator.page(paginator.num_pages)
        # 计算起始序号
    start_index = (tableData.number - 1) * paginator.per_page + 1

    # 获取所有可能的筛选选项，用于填充前端下拉列表
    unique_product_attributes = list(set(item.get('商品属性', '') for item in all_data))
    unique_usage_scenarios = list(set(item.get('使用场景', '') for item in all_data))
    unique_ranking_types = list(set(item.get('榜单类型', '') for item in all_data))

    # 构造上下文
    context = {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
        'tableData': tableData,
        'product_attributes': unique_product_attributes,
        'usage_scenarios': unique_usage_scenarios,
        'ranking_types': unique_ranking_types,
        'selected_product_attributes': selected_product_attributes,
        'selected_usage_scenarios': selected_usage_scenarios,
        'selected_ranking_types': selected_ranking_types,
        'sort_by': sort_by,
        'start_index': start_index
    }

    return render(request, 'tableData.html', context)
def addComments(request,id):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year, mon, day = getHomeData.getNowTime()
    travelInfo = getAddCommentsData.getTravelById(id)
    if request.method == 'POST':
        getAddCommentsData.addComments({
            'id':id,
            'rate':int(request.POST.get('rate')),
            'content':request.POST.get('content'),
            'userInfo':userInfo,
            'travelInfo':travelInfo
        })
        return redirect('/app/tableData')
    return render(request, 'addComments.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
        'travelInfo':travelInfo,
        'id':id
    })

# def cityChar(request):
#     username = request.session.get('username')
#     userInfo = User.objects.get(username=username)
#     year, mon, day = getHomeData.getNowTime()
#     Xdata,Ydata = getEchartsData.cityCharDataOne()
#     resultData = getEchartsData.cityCharDataTwo()
#     return render(request, 'cityChar.html', {
#         'userInfo': userInfo,
#         'nowTime': {
#             'year': year,
#             'mon': getPublicData.monthList[mon - 1],
#             'day': day
#         },
#         'cityCharOneData':{
#             'Xdata':Xdata,
#             'Ydata':Ydata
#         },
#         'cityCharTwoData':resultData
#     })



# todo 添加新的功能，根据省份去查询
# 修改后的视图函数
def cityChar(request):
    return


def rateChar(request):
    # 用户信息获取
    username = request.session.get('username')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        # 处理用户不存在的情况，这里可以重定向到登录页
        return redirect('login')

    # 获取当前时间
    from datetime import datetime
    now = datetime.now()
    year = now.year
    mon = now.month
    day = now.day

    # 读取Excel数据
    try:
        df = pd.read_excel(r'D:\data.xlsx')
        # 去除包含空值的行

        # 将DataFrame转换为列表字典格式，方便模板渲染
        all_data = df.to_dict('records')
    except Exception as e:
        # 处理文件读取错误，返回空数据集或默认数据
        all_data = []

    # 获取筛选条件
    selected_usage_scenario = request.GET.get('usage_scenario', '')
    selected_ranking_type = request.GET.get('ranking_type', '')

    # 筛选数据
    filtered_data = all_data.copy()  # 复制所有数据作为初始筛选集
    if selected_usage_scenario:
        filtered_data = [item for item in filtered_data if item.get('使用场景') == selected_usage_scenario]
    if selected_ranking_type:
        filtered_data = [item for item in filtered_data if item.get('榜单类型') == selected_ranking_type]

    # 统计各使用场景下榜单类型的销售额占比
    usage_scenario_stats = {}
    for item in all_data:
        usage_scenario = item.get('使用场景', '')
        ranking_type = item.get('榜单类型', '')
        sales = item.get('周销售额', 0)

        if usage_scenario not in usage_scenario_stats:
            usage_scenario_stats[usage_scenario] = {}

        if ranking_type not in usage_scenario_stats[usage_scenario]:
            usage_scenario_stats[usage_scenario][ranking_type] = 0

        usage_scenario_stats[usage_scenario][ranking_type] += sales

    # 准备可变化图表数据（同时准备 treemap 和 sunburst 数据）
    chart_data = []
    sunburst_data = []
    if selected_usage_scenario and selected_usage_scenario in usage_scenario_stats:
        ranking_types = usage_scenario_stats[selected_usage_scenario]
        # 准备 treemap 数据
        chart_data = [
            {"name": ranking_type, "value": sales}
            for ranking_type, sales in ranking_types.items()
        ]
        # 准备 sunburst 数据
        sunburst_data = [
            {
                "name": selected_usage_scenario,
                "children": [
                    {"name": ranking_type, "value": sales}
                    for ranking_type, sales in ranking_types.items()
                ]
            }
        ]
    else:
        # 如果没有选择使用场景，展示所有数据的 treemap 格式
        for scenario, types in usage_scenario_stats.items():
            for type_name, sales in types.items():
                chart_data.append({"name": f"{scenario}-{type_name}", "value": sales})
        # 准备 sunburst 数据（所有使用场景和榜单类型的层级关系）
        sunburst_data = []
        for scenario, types in usage_scenario_stats.items():
            scenario_node = {
                "name": scenario,
                "children": [
                    {"name": type_name, "value": sales}
                    for type_name, sales in types.items()
                ]
            }
            sunburst_data.append(scenario_node)

    # 统计各榜单类型下产品种类的销售额占比
    ranking_type_kind_stats = {}
    for item in filtered_data:
        ranking_type = item.get('榜单类型', '')
        kind = item.get('种类', '')
        sales = item.get('周销售额', 0)

        if ranking_type not in ranking_type_kind_stats:
            ranking_type_kind_stats[ranking_type] = {}

        if kind not in ranking_type_kind_stats[ranking_type]:
            ranking_type_kind_stats[ranking_type][kind] = 0

        ranking_type_kind_stats[ranking_type][kind] += sales

    # 准备饼图数据
    pie_chart_data = []
    if selected_ranking_type and selected_ranking_type in ranking_type_kind_stats:
        kinds = list(ranking_type_kind_stats[selected_ranking_type].keys())
        sales = [ranking_type_kind_stats[selected_ranking_type][kind] for kind in kinds]
        pie_chart_data = [
            {"value": sales[i], "name": kinds[i]}
            for i in range(len(kinds))
        ]

    # 获取所有可能的使用场景和榜单类型，用于填充前端下拉列表
    unique_usage_scenarios = list(set(item.get('使用场景', '') for item in all_data))
    unique_ranking_types = list(set(item.get('榜单类型', '') for item in all_data))

    # 构造上下文
    context = {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': mon,
            'day': day
        },
        'chartData': chart_data,
        'sunburstData': sunburst_data,
        'pieChartData': pie_chart_data,
        'usage_scenarios': unique_usage_scenarios,
        'ranking_types': unique_ranking_types,
        'selected_usage_scenario': selected_usage_scenario,
        'selected_ranking_type': selected_ranking_type
    }

    return render(request, 'rateChar.html', context)
# def priceChar(request):
#     username = request.session.get('username')
#     userInfo = User.objects.get(username=username)
#     year, mon, day = getHomeData.getNowTime()
#     cityList = getPublicData.getCityList()
#     travelList = getPublicData.getAllTravelInfoMapData()
#     xData,yData = getEchartsData.getPriceCharDataOne(travelList)
#     x1Data,y1Data = getEchartsData.getPriceCharDataTwo(travelList)
#     disCountPieData = getEchartsData.getPriceCharDataThree(travelList)
#     return render(request, 'priceChar.html', {
#         'userInfo': userInfo,
#         'nowTime': {
#             'year': year,
#             'mon': getPublicData.monthList[mon - 1],
#             'day': day
#         },
#         'cityList': cityList,
#         'echartsData':{
#             'xData':xData,
#             'yData':yData,
#             'x1Data':x1Data,
#             'y1Data':y1Data,
#             'disCountPieData':disCountPieData
#         }
#     })

#生成词云图
def getcloudImg(request):
    category = request.GET.get('category', '')
    # 如果没有选择类别，则显示默认词云图
    if not category:
        # 显示默认词云图的逻辑
        # ...
        return render(request, 'commentContentCloud.html')
    # 读取Excel文件
    df = pd.read_excel(r'D:\data.xlsx')

    # 筛选指定榜单类型的数据
    filtered_df = df[df.iloc[:, 2] == category]  # 假设榜单类型是第3列（索引为2）

    # 提取商品名列数据
    titles = filtered_df.iloc[:, 5].tolist()  # 假设商品名是第6列（索引为5）

    # 将所有标题连接成一个字符串
    all_text = ''.join(map(str, titles))

    # 定义要替换的标点符号和特殊字符
    rp_str = '：，；、？——‘’“”（）()【】#！\n\t+-*/=<>%￥$'
    for char in rp_str:
        all_text = all_text.replace(char, '')  # 移除标点符号

    # 使用正则表达式移除所有字母和数字
    all_text = re.sub(r'[a-zA-Z0-9]', '', all_text)

    # 使用jieba进行分词
    words = jieba.lcut(all_text)

    # 初始化停用词列表
    stopwords = []

    # 添加自定义停用词
    custom_stopwords = ['的', '了', '和', '是', '在', '我', '有', '就', '不', '人', '都', '一', '一个', '上', '也',
                        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
                        '这个', '那个', '商品', '产品', '系列', '款']
    stopwords.extend(custom_stopwords)
    stopwords = set(stopwords)  # 将停用词列表转换为集合，提高查找效率

    # 统计词频
    words_dict = {}
    for word in words:
        if len(word) <= 1 or word in stopwords:
            continue
        words_dict[word] = words_dict.get(word, 0) + 1

    # 将词频统计结果转换为列表并排序
    words_list = list(words_dict.items())
    words_list.sort(key=lambda x: x[1], reverse=True)

    # 获取前100个高频词
    top_words = words_list[:100]

    # 将结果保存到CSV文件
    output_df = pd.DataFrame(top_words, columns=['词语', '频率'])
    output_df.to_csv('商品标题词频统计.csv', index=False, encoding='utf-8-sig')

    # 尝试加载遮罩图片
    try:
        mask_image = imageio.imread(r'C:\Users\86133\Desktop\mask_pic\2.png')
    except Exception as e:
        print(f"无法加载遮罩图片：{e}")
        mask_image = None

    # 创建词云对象
    w = WordCloud(
        background_color='white',  # 背景色为白色
        width=1000,  # 宽度1000像素
        height=800,  # 高度800像素
        font_path='C:\\Windows\\Fonts\\simhei.ttf',  # 指定中文字体，使用黑体
        mask=mask_image,  # 使用指定图片作为词云形状
        max_words=200,  # 最多显示200个词
        max_font_size=150,  # 最大字体大小
        random_state=42  # 随机种子，保证结果可重现
    )

    # 从词频统计结果生成词云
    w.generate_from_frequencies(dict(top_words))

    # 保存词云图到文件
    w.to_file('./static/Cloud.jpg')

    print("词频统计和词云生成完成！")
    print("词云已成功保存到: ./static/Cloud.jpg")
    print("程序执行完毕")
    return render(request, 'commentContentCloud.html')

#种类包装词云图
def getcloud1Img(request):
    category = request.GET.get('category', '')
    # 如果没有选择类别，则显示默认词云图
    if not category:
        # 显示默认词云图的逻辑
        # ...
        return render(request, 'commentContentCloud.html')
    # 读取Excel文件
    df = pd.read_excel(r'D:\data.xlsx')

    # 筛选指定榜单类型的数据
    filtered_df = df[df.iloc[:, 2] == category]  # 假设榜单类型是第3列（索引为2）

    # 提取产品名称和包装形式数据
    product_names = filtered_df.iloc[:, 5].tolist()  # 假设产品名称是第6列（索引为5）
    packaging_forms = filtered_df.iloc[:, 12].tolist()  # 假设包装形式是第13列（索引为12）

    # 合并产品名称和包装形式
    all_text = []
    for name, form in zip(product_names, packaging_forms):
        if pd.notna(name):
            all_text.append(str(name))
        if pd.notna(form):
            all_text.append(str(form))
    all_text = ''.join(all_text)

    # 定义要替换的标点符号和特殊字符
    rp_str = '：，；、？——‘’“”（）()【】#！\n\t+-*/=<>%￥$'
    for char in rp_str:
        all_text = all_text.replace(char, '')  # 移除标点符号

    # 使用正则表达式移除所有字母和数字（如果需要保留字母和数字，可以注释掉这一步）
    # all_text = re.sub(r'[a-zA-Z0-9]', '', all_text)

    # 使用jieba进行分词
    words = jieba.lcut(all_text)

    # 初始化停用词列表
    stopwords = []

    # 添加自定义停用词
    custom_stopwords = ['的', '了', '和', '是', '在', '我', '有', '就', '不', '人', '都', '一', '一个', '上', '也',
                        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
                        '这个', '那个', '商品', '产品', '系列', '款', '包装', '形式', '规格']
    stopwords.extend(custom_stopwords)
    stopwords = set(stopwords)  # 将停用词列表转换为集合，提高查找效率

    # 统计词频
    words_dict = {}
    for word in words:
        if len(word) <= 1 or word in stopwords:
            continue
        words_dict[word] = words_dict.get(word, 0) + 1

    # 将词频统计结果转换为列表并排序
    words_list = list(words_dict.items())
    words_list.sort(key=lambda x: x[1], reverse=True)

    # 获取前100个高频词
    top_words = words_list[:100]

    # 将结果保存到CSV文件
    output_df = pd.DataFrame(top_words, columns=['词语', '频率'])
    output_df.to_csv('商品包装词频统计.csv', index=False, encoding='utf-8-sig')

    # 尝试加载遮罩图片
    try:
        mask_image = imageio.imread(r'C:\Users\86133\Desktop\mask_pic\2.png')
    except Exception as e:
        print(f"无法加载遮罩图片：{e}")
        mask_image = None

    # 创建词云对象
    w = WordCloud(
        background_color='white',  # 背景色为白色
        width=1000,  # 宽度1000像素
        height=800,  # 高度800像素
        font_path='C:\\Windows\\Fonts\\simhei.ttf',  # 指定中文字体，使用黑体
        mask=mask_image,  # 使用指定图片作为词云形状
        max_words=200,  # 最多显示200个词
        max_font_size=150,  # 最大字体大小
        random_state=42  # 随机种子，保证结果可重现
    )

    # 从词频统计结果生成词云
    w.generate_from_frequencies(dict(top_words))

    # 保存词云图到文件
    w.to_file('./static/Cloud1.jpg')

    print("词频统计和词云生成完成！")
    print("词云已成功保存到: ./static/Cloud1.jpg")
    print("程序执行完毕")
    return render(request, 'detailIntroCloud.html')
# todo 价格和月销量分析新增加省份功能


def priceChar(request):
    # 读取Excel文件
    try:
        df = pd.read_excel(r'D:\data.xlsx')
    except Exception as e:
        return render(request, 'error.html', {'error_message': f"无法读取Excel文件：{e}"})

    # 获取当前时间
    from datetime import datetime
    now = datetime.now()
    year, mon, day = now.year, now.month, now.day

    # 处理榜单类型筛选
    category = request.GET.get('category', '').strip()
    if category:
        df = df[df['榜单类型'] == category]

    # 生成图表数据
    echarts_data = process_data_for_charts(df)

    # 获取所有可用的榜单类型用于筛选表单
    categories = df['榜单类型'].drop_duplicates().tolist()

    return render(request, 'priceChar.html', {
        'nowTime': {
            'year': year,
            'mon': mon,
            'day': day
        },
        'echartsData': echarts_data,
        'categories': categories,  # 传递榜单类型列表到模板
        'selected_category': category  # 传递当前选中的榜单类型
    })

def process_data_for_charts(df):
    # 生成价格分析数据
    price_x_data, price_y_data = generate_price_analysis(df)

    # 生成销量分析数据
    sales_x_data, sales_y_data = generate_sales_analysis(df)

    # 生成折扣占比分析数据
    discount_pie_data = generate_discount_analysis(df)

    # 生成券后价和周销售额关系数据
    coupon_price_sales_data = generate_coupon_price_sales_data(df)

    return {
        'xData': price_x_data,
        'yData': price_y_data,
        'x1Data': sales_x_data,
        'y1Data': sales_y_data,
        'disCountPieData': discount_pie_data,
        'couponPriceSalesData': coupon_price_sales_data
    }
def generate_coupon_price_sales_data(df):
    # 提取券后价和周销售额数据
    coupon_prices = df['券后价'].tolist()
    weekly_sales = df['周销售数量'].tolist()

    # 计算每个商品的周销售额（券后价 × 周销售数量）
    weekly_sales_amount = [cp * ws for cp, ws in zip(coupon_prices, weekly_sales)]

    # 生成散点图数据
    data = []
    for cp, ws, wsa in zip(coupon_prices, weekly_sales, weekly_sales_amount):
        data.append({
            'name': f'券后价: {cp}元, 销量: {ws}件',
            'value': [cp, wsa]
        })

    return data
def generate_price_analysis(df):
    # 定义更细粒度的价格区间
    price_ranges = [
        (0, 50, '0-50元'),
        (50, 100, '50-100元'),
        (100, 150, '100-150元'),
        (150, 200, '150-200元'),
        (200, 300, '200-300元'),
        (300, 400, '300-400元'),
        (400, 500, '400-500元'),
        (500, 700, '500-700元'),
        (700, 1000, '700-1000元'),
        (1000, float('inf'), '1000元以上')
    ]

    # 初始化数据字典
    data = {label: 0 for (_, _, label) in price_ranges}

    # 统计每个价格区间内的商品数量
    for price in df['市场价']:
        for (low, high, label) in price_ranges:
            if low <= price < high:
                data[label] += 1
                break

    return list(data.keys()), list(data.values())

def generate_sales_analysis(df):
    # 定义更细粒度的销量区间
    sales_ranges = [
        (0, 10, '0-10件'),
        (10, 20, '10-20件'),
        (20, 30, '20-30件'),
        (30, 50, '30-50件'),
        (50, 100, '50-100件'),
        (100, 200, '100-200件'),
        (200, 300, '200-300件'),
        (300, 500, '300-500件'),
        (500, float('inf'), '500件以上')
    ]

    # 初始化数据字典
    data = {label: 0 for (_, _, label) in sales_ranges}

    # 统计每个销量区间内的商品数量
    for sales in df['周销售数量']:
        for (low, high, label) in sales_ranges:
            if low <= sales < high:
                data[label] += 1
                break

    return list(data.keys()), list(data.values())

def generate_discount_analysis(df):
    # 定义更细粒度的折扣范围
    discount_ranges = [
        (0, 0.3, '3折以下'),
        (0.3, 0.5, '3-5折'),
        (0.5, 0.6, '5-6折'),
        (0.6, 0.7, '6-7折'),
        (0.7, 0.8, '7-8折'),
        (0.8, 0.9, '8-9折'),
        (0.9, 1.0, '9折以上')
    ]

    # 初始化数据字典
    data = {label: 0 for (_, _, label) in discount_ranges}

    # 提取折扣信息并转换为小数形式
    for discount in df['折扣']:
        try:
            discount_value = float(discount.replace('折', '')) / 10
            for (low, high, label) in discount_ranges:
                if low <= discount_value < high:
                    data[label] += 1
                    break
        except:
            continue

    return [{"name": k, "value": v} for k, v in data.items()]
#
# def commentsChar(request):
#     username = request.session.get('username')
#     userInfo = User.objects.get(username=username)
#     year, mon, day = getHomeData.getNowTime()
#     xData,yData = getEchartsData.getCommentsCharDataOne()
#     commentsScorePieData = getEchartsData.getCommentsCharDataTwo()
#     x1Data,y1Data = getEchartsData.getCommentsCharDataThree()
#     return render(request, 'commentsChar.html', {
#         'userInfo': userInfo,
#         'nowTime': {
#             'year': year,
#             'mon': getPublicData.monthList[mon - 1],
#             'day': day
#         },
#         'echartsData':{
#             'xData':xData,
#             'yData':yData,
#             'commentsScorePieData':commentsScorePieData,
#             'x1Data':x1Data,
#             'y1Data':y1Data
#         }
#     })


# todo 新增根据省份去查询数据
def commentsChar(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year, mon, day = getHomeData.getNowTime()
    province = request.GET.get('province')  # 获取省份参数

    # 根据省份参数获取对应数据
    if province:
        xData, yData = getEchartsData.getCommentsCharDataOne(province)
        commentsScorePieData = getEchartsData.getCommentsCharDataTwo(province)
        x1Data, y1Data = getEchartsData.getCommentsCharDataThree(province)
    else:
        xData, yData = getEchartsData.getCommentsCharDataOne()
        commentsScorePieData = getEchartsData.getCommentsCharDataTwo()
        x1Data, y1Data = getEchartsData.getCommentsCharDataThree()

    return render(request, 'commentsChar.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
        'echartsData': {
            'xData': xData,
            'yData': yData,
            'commentsScorePieData': commentsScorePieData,
            'x1Data': x1Data,
            'y1Data': y1Data
        }
    })



def recommendation(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year, mon, day = getHomeData.getNowTime()
    try:
        user_ratings = getUser_ratings()
        recommended_items = user_bases_collaborative_filtering(userInfo.id, user_ratings)
        resultDataList = getRecommendationData.getAllTravelByTitle(recommended_items)
    except:
        resultDataList = getRecommendationData.getRandomTravel()

    return render(request, 'recommendation.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        },
        'resultDataList':resultDataList
    })

def detailIntroCloud(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year, mon, day = getHomeData.getNowTime()
    return render(request, 'detailIntroCloud.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        }
    })

def commentContentCloud(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    year, mon, day = getHomeData.getNowTime()
    return render(request, 'commentContentCloud.html', {
        'userInfo': userInfo,
        'nowTime': {
            'year': year,
            'mon': getPublicData.monthList[mon - 1],
            'day': day
        }
    })