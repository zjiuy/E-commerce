import jieba
import pandas as pd
from matplotlib import pylab as plt
from wordcloud import WordCloud
from PIL import Image
import numpy as np
import json
import os
import django
import jieba
import pandas as pd
import imageio.v2 as imageio
import wordcloud
import re
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Travel_system.settings')
django.setup()
from app.models import TravelInfo


def getIntroCloudImg(targetImgSrc,resImgSrc):
    travelList = TravelInfo.objects.all()
    text = ''
    stopwords = ['的', '是', '在', '这', '那', '他', '她', '它', '我', '你','和','等','为','有','与']
    for travel in travelList:
         text += travel.detailIntro

    cut = jieba.cut(text)
    newCut = []
    for tex in cut:
        if tex not in stopwords:
            newCut.append(tex)

    string = ' '.join(newCut)

    img = Image.open(targetImgSrc)
    img_arr = np.array(img)
    wc = WordCloud(
        background_color='white',
        mask=img_arr,
        font_path='STHUPO.TTF'
    )

    wc.generate_from_text(string)

    # 绘制图片
    fig = plt.figure(1)
    plt.imshow(wc)
    plt.axis('off') # 不显示坐标轴

    # plt.show()

    plt.savefig(resImgSrc,dpi=500)


def getCommentContentCloudImg(targetImgSrc,resImgSrc):
    travelList = TravelInfo.objects.all()
    text = ''
    stopwords = ['的', '是', '在', '这', '那', '他', '她', '它', '我', '你','和','等','为','有','与']
    for travel in travelList:
        comments = json.loads(travel.comments)
        for comm in comments:
            text += comm['content']

    cut = jieba.cut(text)
    newCut = []
    for tex in cut:
        if tex not in stopwords:
            newCut.append(tex)

    string = ' '.join(newCut)

    img = Image.open(targetImgSrc)
    img_arr = np.array(img)
    wc = WordCloud(
        background_color='white',
        mask=img_arr,
        font_path='STHUPO.TTF'
    )

    wc.generate_from_text(string)

    # 绘制图片
    fig = plt.figure(1)
    plt.imshow(wc)
    plt.axis('off') # 不显示坐标轴

    # plt.show()

    plt.savefig(resImgSrc,dpi=500)


def getcloudImg(category):
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
if __name__ == '__main__':
    #getCommentContentCloudImg('./static/2.jpg','./static/commentContentCloud.jpg')
    getcloudImg('香水')  # 示例：生成榜单类型为“饮料冲调”的商品名词云图


