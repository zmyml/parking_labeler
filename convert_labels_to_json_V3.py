# 检查label是否包含最后时间加1秒,若没有则加一行数据
# 图像列表也加在函数中
# 对新生成的label文件,多个转化为json
import os
import numpy as np
import json
from create_v3_012 import create_json_record

# path = r'Y:\dataset\inroad_parking_videos\pics'
path = r'W:\dataset\inroad_parking_videos\pics'
# path = r'X:\20191106'
date_gap = ['2020_01_10', '2020_01_17']

list_all = []  # 找到包含标签的文件夹
for root, dirs, files in os.walk(path, topdown=False):
    for name in dirs:
        # if name.split('_')[0] in ['test', 'L', 'R'] or name.split('ZMY')[0] in ['DDT2G1907', 'DDZ2G1907']:
        if name.split('ZMY')[0] in ['DDT2G1907', 'DDZ2G1907']:
            date = os.path.basename(root)
            if date < date_gap[0] or date >= date_gap[1]:
                continue
            if os.path.isfile(os.path.join(root, name + '_label.txt')):
                list_all.append(os.path.join(root, name))
        elif 'test_dev' in name:
            if date < date_gap[0] or date >= date_gap[1]:
                continue
            if os.path.isfile(os.path.join(root, name + '_label.txt')):
                list_all.append(os.path.join(root, name))


for ii in list_all:
    path_txt_for_check = f'{ii}_label.txt'
    path_local = r'C:\Users\tongxin\Desktop\label_test_2020_01_07'
    path_json_converted = path_local + '\\' + ii.split('\\')[-2] + '\\' + os.path.splitext(os.path.basename(path_txt_for_check))[0] + '_v2.json'
    if not os.path.isdir(os.path.dirname(path_json_converted)):
        os.makedirs(os.path.dirname(path_json_converted))

    imgs_list = os.listdir(ii)
    imgs_list.sort()  # 排序
    imgs_list = [i for i in imgs_list if i.endswith('jpg')]
    last_time = os.path.splitext(imgs_list[-1])[0]
    # 全部图片时间秒
    h_f, m_f, s_f = last_time.split('_')[:3]
    # 计算图片最后一张加一秒的时_分_秒表达
    sec_last_plus_one = int(h_f) * 3600 + int(m_f) * 60 + int(s_f) + 1  # 在此加1s
    imgs_last_time_plus_one = f'{sec_last_plus_one//3600:02d}_{sec_last_plus_one%3600//60:02d}_{sec_last_plus_one%60:02d}'

    # 1.读取一个txt文件
    data_raw = []
    with open(path_txt_for_check, 'r', encoding='UTF-8') as file_to_read:
        lines = file_to_read.readlines()  # 整行读取数据
        for line in lines:
            if line != '\n':
                data_raw.append(line)

    parking_space = [i.split(':')[0] for i in data_raw[-1].split(' ')[1:]]

    # 2.转换文件
    data_raw_np = []
    for i in data_raw:
        for idx, j in enumerate(i.split(' ')):
            if (idx == len(parking_space)) and (j[-1] == '\n'):
                data_raw_np.append(j[:-1])  # 去掉"\n"
            else:
                data_raw_np.append(j)

    record_for_json = create_json_record(data_raw_np, parking_space, imgs_last_time_plus_one, imgs_list)
    file = open(path_json_converted, 'w', encoding='utf-8')
    json.dump(record_for_json, file, ensure_ascii=False, indent=4)
    file.close()

    print(f'save new label at:{path_json_converted}')
