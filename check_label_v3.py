'''
程序功能,先确定图片文件夹路径/标记结果路径/以及标记车位个数(小于6)
F5运行后鼠标选择车位
按上下显示上下图片
按左右显示标记到的图片
'''
import cv2
import numpy as np
import os
from detect_utils import parking_line
from detect_utils import show_parking_line

path_img = r'W:\dataset\inroad_parking_videos\pics\2020_01_10\DDT2G1907ZMY00124SY'  # 路径

path_txt_for_check = os.path.split(path_img)[0] + '\\' + os.path.split(path_img)[-1] + '_label.txt'

parking_num = 7  # 停车位个数
bias = 60  # 车位与状态标记在图片上的偏移
h_l, h_h = 10, 2000  # 显示图像的上下边界

ip_name = path_img.split('\\')[-1].split('_')[-1]
if ip_name == '1010':  # 待改进 针对 DDT2G1907ZMY00009SY_1010
    ip_name = path_img.split('\\')[-1]
parking_list_np = np.array(parking_line[ip_name]).astype(int)

# ip与停车位关系
if ip_name == '252':
    parking_num = 3
elif ip_name == '261':
    parking_num = 4
elif ip_name == '262':
    parking_num = 4
elif ip_name == '177':
    parking_num = 3
elif ip_name == '175':
    parking_num = 3

font = cv2.FONT_HERSHEY_SIMPLEX  # 使用默认字体
pos_show = []
pos_show_bias = []
state_loc = []

act = 0
idx_togo = 0
# #0.读取文件列表
# name_all_list = os.listdir(path_img)

# 1.读取一个txt文件
data_raw = []
with open(path_txt_for_check, 'r', encoding='UTF-8') as file_to_read:
    lines = file_to_read.readlines()  # 整行读取数据
    for line in lines:
        if line != '\n':
            data_raw.append(line)


# 2.转换文件为np.array
data_raw_np = []
for i in data_raw:
    for idx, j in enumerate(i.split(' ')):
        if idx:
            data_raw_np.append(float(j.split(':')[1]))

        else:
            pass
            # data_raw_np.append(int(j))

data_raw_np = np.array(data_raw_np)
# now we get the data
data_raw_np = data_raw_np.reshape(-1, len(data_raw[0].split(' ')) - 1)
data_raw_np = data_raw_np.astype(int)
row_fin = len(data_raw)

# 设置图像大小
global h
h = h_h - h_l
list_img = os.listdir(path_img)
list_img = [i for i in list_img if i.endswith('jpg')]
list_img.sort()  # 排序
os.chdir(path_img)
im_data = cv2.imread(list_img[0])

h, w = im_data.shape[0:2]
x_panel = int(w * 0.85)
y_panel = int(h * 0.15)
y_panel_bias = y_panel - int(0.05 * h)
y_panel_bias2 = y_panel - 2 * int(0.05 * h)
font_size = w // 1000
bias = int(w * 0.025)  # 车位与状态标记在图片上的偏移
bias_y = int(h * -0.05)  # 车位idx号位置的偏移
font_width = int((h + w) / 1000)
if h == 0:
    w_w, w_h = (w // 8) * 3, (h // 8) * 3
    h_l = 0
    h_h = h
else:
    w_w, w_h = (w // 8) * 3, (h // 8) * 3


def check_format(r):
    if r[2] >= 60:
        r[2] -= 60
        r[1] += 1
    if r[1] >= 60:
        r[1] -= 60
        r[0] += 1
#     if r[0] >= 24:
#         r[0] -= 24
    return r


def sec2img_name(data_np, pic_one_name_np):
    name_raw = []
    for i in data_np:
        tmp = [i[0] // 3600, i[0] % 3600 // 60, (i[0] % 3600) % 60]
        tmp = np.array(tmp)
        tmp = tmp + pic_one_name_np
        name_raw.append(tmp)

    name_list = []
    for j in name_raw:
        tmp = check_format(j)
        name_list.append(str(tmp[0]).zfill(2) + '_' + str(tmp[1]).zfill(2) + '_' + str(tmp[2]).zfill(2) + '.jpg')

    return name_list


for i in range(parking_num):
    pos_show.append([0, 0])
    pos_show_bias.append([0, 0])
    state_loc.append(0)

# list_img = os.listdir(path_img)
# list_img.sort()  # 排序

list_img_time_only = ['_'.join(i.split('.')[0].split('_')[:3]) + '.jpg' for i in list_img]
h_0, m_0, s_0 = os.path.splitext(list_img[0])[0].split('_')[:3]
pic_one_name_np = np.array([int(h_0), int(m_0), int(s_0)])
name = sec2img_name(data_raw_np, pic_one_name_np)

os.chdir(path_img)
img_len = len(list_img)
idx = 0
h_0, m_0, s_0 = os.path.splitext(list_img[0])[0].split('_')[:3]
h_1, m_1, s_1 = os.path.splitext(list_img[1])[0].split('_')[:3]
# 两幅图片时间间隔
gap_sec = (int(h_1) - int(h_0)) * 3600 + \
    (int(m_1) - int(m_0)) * 60 + (int(s_1) - int(s_0))
one_min = 60 // gap_sec
five_mins = 300 // gap_sec

if one_min == 0:
    one_min = 2
if five_mins == 0:
    five_mins = 10


# 全部图片时间秒
h_f, m_f, s_f = os.path.splitext(list_img[img_len - 1])[0].split('_')[:3]
h_sum = int(h_f) - int(h_0)
m_sum = int(m_f) - int(m_0)
s_sum = int(s_f) - int(s_0)
sec_sum = h_sum * 3600 + m_sum * 60 + s_sum

img_data = cv2.imread(list_img[0])
record_list = []

click_time = 0


def get_p(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        global click_time
        global pos_show
        global pos_show_bias
        if click_time < parking_num:
            pos_show[click_time] = [x, y]
            # pos_show_bias[click_time] = [x+bias,y]
            pos_show_bias[click_time] = [x - bias // 4, y - bias]
            click_time += 1
            print(x, y)


global idx_txt
idx_txt = 0

cv2.namedWindow('img', 0)
cv2.startWindowThread()
cv2.resizeWindow('img', w_w, w_h)  # 宽,高

while idx < img_len:
    img_data = cv2.imread(list_img[idx])
    if img_data is None:
        idx += 1
        continue

    img_data = cv2.imread(list_img[idx])
    img_data = show_parking_line(img_data, parking_list_np, 4)  # 画停车线
    img_data = img_data[h_l:h_h, :, :]
    h, m, s = os.path.splitext(list_img[idx])[0].split('_')[:3]
    h_p = int(h) - int(h_0)
    m_p = int(m) - int(m_0)
    s_p = int(s) - int(s_0)
    sec_pass = h_p * 3600 + m_p * 60 + s_p

    img_data = cv2.putText(img_data, data_raw[idx_txt].split(' ')[0], (x_panel, y_panel),
                           font, font_size, (0, 255, 255), font_width)  # 添加文字，1.2表示字体大小，（3000,260）是初始的位置，(0,0,255)表示颜色，4表示粗细

    img_data = cv2.putText(img_data, '_'.join(os.path.splitext(list_img[idx])[0].split('_')[:3]), (x_panel, y_panel_bias),
                           font, font_size, (0, 0, 255), font_width)  # 添加文字，1.2表示字体大小，（3000,260）是初始的位置，(0,0,255)表示颜色，4表示粗细

    img_data = cv2.putText(img_data, str(int(sec_sum - sec_pass) // 60) + 'm' + str(int(sec_sum - sec_pass) % 60) + 's', (x_panel, y_panel_bias2),
                           font, font_size, (0, 255, 0), font_width)  # 添加文字，1.2表示字体大小，（3000,100）是初始的位置，(0,255,0)表示颜色，4表示粗细

    for i in range(parking_num):
        # 车位
        img_data = cv2.putText(img_data, str(i),
                               (pos_show[i][0], pos_show[i][1]), font, font_size, (255, 0, 255), font_width)

        # 状态标记
        img_data = cv2.putText(img_data, str(int(state_loc[i])),
                               (pos_show_bias[i][0], pos_show_bias[i][1]), font, font_size + 1, (0, 0, 255), font_width)

    cv2.setMouseCallback('img', get_p, 0)  # 鼠标操作回调函数
    cv2.imshow('img', img_data)
    key = cv2.waitKeyEx(30)  # 等待按键
    if act == 1 and idx < idx_togo:
        idx += 1
    else:
        act = 0

    if key == 27:  # ESC
        break
    elif key == ord('s') or key == ord('S'):  # s 前进1min
        act = 0
        idx += one_min
    elif key == ord('d') or key == ord('D'):  # d前进到下一个状态变化点
        act = 0
        idx_txt += 1
        if idx_txt < row_fin:
            if data_raw[idx_txt].split(' ')[0] + '.jpg' not in list_img_time_only:
                print('==>', end=' ')
                print(data_raw[idx_txt])
                continue
            idx = list_img_time_only.index(data_raw[idx_txt].split(' ')[0] + '.jpg')
            for i in range(parking_num):
                state_loc[i] = data_raw_np[idx_txt][i]
        else:
            idx_txt = row_fin - 1
            idx = len(list_img) - 1
    elif key == ord('a') or key == ord('A'):  # 后退一个状态变化点
        act = 0
        idx_txt -= 1
        if idx_txt >= 0:
            if data_raw[idx_txt].split(' ')[0] + '.jpg' not in list_img_time_only:
                print('==>', end=' ')
                print(data_raw[idx_txt])
                continue
            idx = list_img_time_only.index(data_raw[idx_txt].split(' ')[0] + '.jpg')
            for i in range(parking_num):
                state_loc[i] = data_raw_np[idx_txt][i]
        else:
            idx_txt = 0
            idx = list_img_time_only.index(data_raw[idx_txt].split(' ')[0] + '.jpg')
    elif key == ord('w') or key == ord('W'):  # w 后退1min
        act = 0
        if idx > 0:
            idx -= one_min
        else:
            idx = 0
    elif key == 2490368:  # 上
        act = 0
        if idx > 0:
            idx -= 1
        else:
            idx = 0

    elif key == 2621440:  # 下
        act = 0
        idx += 1

    elif key == 2424832:  # 左
        act = 0
        idx_txt -= 1
        if idx_txt >= 0:
            if data_raw[idx_txt].split(' ')[0] + '.jpg' not in list_img_time_only:  # 若不在列表
                print('==>', end=' ')
                print(data_raw[idx_txt])
                continue
            idx = list_img_time_only.index(
                data_raw[idx_txt].split(' ')[0] + '.jpg')  # 若在列表
            for i in range(parking_num):
                state_loc[i] = data_raw_np[idx_txt][i]
        else:
            idx_txt = 0
            idx = list_img_time_only.index(data_raw[idx_txt].split(' ')[0] + '.jpg')

    elif key == 2555904:  # 右
        idx_txt += 1
        if idx_txt < row_fin:
            act = 1
            if data_raw[idx_txt].split(' ')[0] + '.jpg' not in list_img_time_only:
                idx_togo = 0
                print('==>', end=' ')
                print(data_raw[idx_txt])
                tmp = np.array(list_img)
                tmp = tmp < (data_raw[idx_txt].split(' ')[0] + '.jpg')
                idx_togo += tmp.sum() - 1
                continue
            idx += 1
            for i in range(parking_num):
                state_loc[i] = data_raw_np[idx_txt - 1][i]
            idx_togo = list_img_time_only.index(data_raw[idx_txt].split(' ')[0] + '.jpg')
        else:
            idx_txt = row_fin - 1
            idx = len(list_img) - 1

    elif key == ord(' '):  # 空格控制act
        for i in range(parking_num):
            state_loc[i] = data_raw_np[idx_txt][i]

if key != 27:
    print('===========================')

print('fin')
cv2.destroyAllWindows()
