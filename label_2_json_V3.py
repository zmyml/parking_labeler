# 检查label是否包含最后时间加1秒,若没有则加一行数据
# 图像列表也加在函数中
# 单个生成一个标签
# 给出一个旧标签的位置(全路径),生成一张新标签
import os
import numpy as np
import json
from create_v3_012 import create_json_record
# from create_v2 import create_json_record


# path_txt_for_check = r'Y:\dataset\inroad_parking_videos\pics\2019_08_12\DDT2G1907ZMY00008SY_label.txt'
# path_txt_for_check = r'Y:\dataset\inroad_parking_videos\pics\2019_12_28\DDT2G1907ZMY00142SY_1211_label.txt'
# path_txt_for_check = r'W:\dataset\inroad_parking_videos\pics\2019_12_14\DDT2G1907ZMY00057SY_label.txt'
path_txt_for_check = r'W:\dataset\inroad_parking_videos\pics\2020_01_19\DDT2G1907ZMY00082SY_label.txt'
# path_txt_for_check = r'W:\dataset\inroad_parking_videos\pics\2019_12_31\DDT2G1907ZMY00142SY_1211_label.txt'

imgs_dir = os.path.dirname(path_txt_for_check)
folder_name = os.path.basename(path_txt_for_check).split('_')
if len(folder_name) == 2:
    folder_name = folder_name[0]
elif len(folder_name) == 3:
    folder_name = '_'.join(folder_name[0:2])
elif len(folder_name) == 4:
    folder_name = '_'.join(folder_name[0:3])

imgs_folder_path = f'{imgs_dir}\\{folder_name}'
imgs_list = os.listdir(imgs_folder_path)
imgs_list = [i for i in imgs_list if i.endswith('jpg')]
imgs_list.sort()  # 排序
imgs_list_only_time = ['_'.join(i.split('_')[:3]) for i in imgs_list]
# # 得到最后一张图片时间
imgs_last_time = os.path.splitext(imgs_list[-1])[0]
hh, mm, ss = imgs_last_time.split('_')[:3]
sec_last_plus_one = 3600 * int(hh) + 60 * int(mm) + int(ss) + 1  # #最后时间加1s
imgs_last_time_plus_one = f'{sec_last_plus_one//3600:02d}_{sec_last_plus_one%3600//60:02d}_{sec_last_plus_one%60:02d}'


# path_local = r'C:\Users\tongxin\Desktop\label_test_666'
# path_local = r'C:\Users\tongxin\Desktop\1'
path_local = r'C:\Users\tongxin\Desktop\label_test_2020_01_07'
path_json_converted = path_local + '\\' + \
    path_txt_for_check.split('\\')[-2] + '\\' + \
    os.path.splitext(os.path.basename(path_txt_for_check))[0] + '_v2.json'
#  os.path.splitext(os.path.basename(path_txt_for_check))[0]+'_d05.10.json'

if not os.path.isdir(os.path.dirname(path_json_converted)):
    os.makedirs(os.path.dirname(path_json_converted))

# 1.读取一个txt文件
data_raw = []
with open(path_txt_for_check, 'r', encoding='UTF-8') as file_to_read:
    lines = file_to_read.readlines()  # 读取数据
    for line in lines:
        if line != '\n':
            data_raw.append(line)

parking_space = [i.split(':')[0] for i in data_raw[-1].split(' ')[1:]]  # 看有多少停车位

# 2.转换文件
data_raw_np = []
for i in data_raw:
    for idx, j in enumerate(i.split(' ')):
        if idx == len(parking_space) and (j[-1] == '\n'):  # 最后一列
            data_raw_np.append(j[:-1])  # 去掉"\n"
        else:
            data_raw_np.append(j)

record_for_json = create_json_record(data_raw_np, parking_space, imgs_last_time_plus_one, imgs_list_only_time)
file = open(path_json_converted, 'w', encoding='utf-8')
json.dump(record_for_json, file, ensure_ascii=False, indent=4)
file.close()

print(f'save new label at:{path_json_converted}')
