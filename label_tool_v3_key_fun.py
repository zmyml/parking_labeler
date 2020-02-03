'''
在2.1的基础上进行修改
'''
import cv2
import numpy as np
import os
import json
from detect_utils import parking_line
from detect_utils import show_parking_line
from create import create_json_record
path_img = r'C:\Users\tongxin\Desktop\2019_10_10\DDT2G1907ZMY00009SY_1010'  # 路径

parking_space = 3  # 停车位个数 #需要手动改

# #################不标车牌的IP##################
no_plate_list = ['177', '211', '212', '221', '222', '231',
                 '232', '241', '242', '251', '252', '261', '262']

# #################创建参数和初始化##################
path_txt = os.path.dirname(path_img) + '\\' + path_img.split('\\')[-1] + '_label.txt'
path_json = os.path.dirname(path_img) + '\\' + path_img.split('\\')[-1] + '_label_v2.json'
font = cv2.FONT_HERSHEY_SIMPLEX  # 使用默认字体
change_parking_state = 0
show_parking_num = 1
change_parking_num = 2
frame_car_use_left_button = 3
state_mouse_init = 0
drag_start = None
sel = (0, 0, 0, 0)  # 鼠标用
state_num_key = change_parking_state
state_mouse = state_mouse_init

parking_num_block = []  # 车位数据集合(选择跨车位停车时使用)
parking_num = []  # 格停车空间的所占的停车位号
state_loc = []  # 停车状态
pos_show = []  # 显示位置坐标
pos_show_bias = []  # 显示位置偏移后的坐标
color_parking_num = []  # 停车状态颜色
color_parking_space_num = []
car_frame_point = []
car_frame_point_abs = []

act = 0  # 控制是否连续播放
state_time_label_overwrite = 0
time_label = ''

id_parking_num_change = 0 # 车位索引

# 为各项数值初始化
for idx, i in enumerate(range(parking_space)):
    parking_num.append([idx])
    state_loc.append(0)
    pos_show.append([0, 0])
    pos_show_bias.append([0, 0])
    color_parking_num.append((255, 0, 255))
    color_parking_space_num.append((255, 0, 0))
    car_frame_point.append([])  # 车辆框架点初始为空
    car_frame_point_abs.append([])

# list_img = os.listdir(path_img)
# for filename in list_img:
#     if not filename.endswith('jpg'):
#         list_img.remove(filename)
# list_img.sort()  # 排序

file_list = os.listdir(path_img)
list_img = [file for file in file_list if file.endswith('jpg')]
list_img.sort()  # 排序
imgs_list_only_time = ['_'.join(i.split('_')[:3]) + '.jpg' for i in list_img]  # 以防文件名后为电压等
os.chdir(path_img)
im_data = cv2.imread(list_img[0])

# ##############得到图像参数##################
h, w = im_data.shape[0:2]
# ##############字体大小和位置参数##################
x_panel = int(w * 0.83)
y_panel = int(h * 0.10)
y_panel_bias = y_panel - int(0.05 * h)
font_size = w // 1000
bias = int(w * 0.025)  # 车位与状态标记在图片上的偏移
bias_y = int(h * -0.05)  # 车位idx号位置的偏移
font_width = int((h + w) / 1000)

# ##################得到IP地址并人为规定显示位置##################
# ip_name = path_img.split('\\')[-1].split('_')[-1]
img_dir_name = os.path.basename(path_img)
dir_content = img_dir_name.split('_')
underline_seg_num = len(dir_content)
if underline_seg_num == 2:
    if dir_content[-1] == '1010':  # 针对 DDT2G1907ZMY00009SY_1010 有待改进...
        ip_name = img_dir_name
    else:
        ip_name = dir_content[-1]  # 针对 test_170
elif underline_seg_num == 1:       # 针对 DDT2G1907ZMY00009SY
    ip_name = dir_content[0]

if ip_name in parking_line:
    parking_list_np = np.array(parking_line[ip_name]).astype(int)  # 获得车位线
else:
    blank_list = []
    for i in range(parking_space):
        blank_list.append([[0, 0], [0, 0], [0, 0], [0, 0]])  # 待修改
    parking_list_np = np.array(blank_list)

if ip_name == '177':
    h_h = 600
    h_l = 1400
elif ip_name == '175':
    h_h = 700
    h_l = 1700
elif ip_name == '176':
    h_h = 500
    h_l = 1400
elif ip_name == '178':
    h_h = 250
    h_l = 1050
elif ip_name == '170':
    h_h = 250
    h_l = 1300
elif ip_name == '211':
    h_h = 350
    h_l = 850
elif ip_name == '212':
    h_h = 350
    h_l = 850
elif ip_name == '221':
    h_h = 350
    h_l = 850
elif ip_name == 'DDZ2G1907ZMY00002SY':
    h_h = 200   # 显示的最上边界
    h_l = 1300  # 显示的最下边界
elif ip_name == 'DDT2G1907ZMY00008SY':
    h_h = 300   # 显示的最上边界
    h_l = 1400  # 显示的最下边界
elif ip_name == 'DDT2G1907ZMY00016SY':
    h_h = 600   # 显示的最上边界
    h_l = 1450  # 显示的最下边界
else:
    h_h = 300   # 显示的最上边界
    h_l = 1500  # 显示的最下边界

# 标记窗口大小设置
# 待修改
if ip_name == '177':
    # w_w = w//3
    # w_h = (h_l - h_h)//3
    w_w = (w // 7) * 3
    w_h = ((h_l - h_h) // 7) * 3
elif ip_name == '170':
    w_w = (w // 7) * 3
    w_h = ((h_l - h_h) // 7) * 3
elif ip_name in ['211', '212', '221']:
    w_w = (w // 3) * 3
    w_h = ((h_l - h_h) // 3) * 3
else:
    w_w = (w // 5) * 2
    w_h = ((h_l - h_h) // 5) * 2

img_len = len(list_img)
idx = 0
h_0, m_0, s_0 = os.path.splitext(list_img[0])[0].split('_')[:3]  # 排序后第一个时间
h_1, m_1, s_1 = os.path.splitext(list_img[1])[0].split('_')[:3]
# 两幅图片时间间隔
# 如果时间间隔不确定,这个就对程序没意义了
gap_sec = (int(h_1) - int(h_0)) * 3600 + (int(m_1) - int(m_0)) * 60 + (int(s_1) - int(s_0))
one_min = 60 // gap_sec
three_mins = 180 // gap_sec
five_mins = 300 // gap_sec
if one_min == 0:
    one_min = 2
if three_mins == 0:
    three_mins = 6
if five_mins == 0:
    five_mins = 10

# 得到初始时间秒值
initial_time_sec = int(h_0) * 3600 + int(m_0) * 60 + int(s_0)

# 全部图片时间秒
h_f, m_f, s_f = os.path.splitext(list_img[-1])[0].split('_')[:3]
h_sum = int(h_f) - int(h_0)
m_sum = int(m_f) - int(m_0)
s_sum = int(s_f) - int(s_0)
sec_sum = h_sum * 3600 + m_sum * 60 + s_sum

# 计算图片最后一张加一秒的时_分_秒表达
sec_all = int(h_f) * 3600 + int(m_f) * 60 + int(s_f)
sec_all_plus_one_sec = sec_all + 1
h_last = sec_all_plus_one_sec // 3600  # 时
m_last = sec_all_plus_one_sec % 3600 // 60  # 分
s_last = sec_all_plus_one_sec % 60  # 秒
last_time = str(h_last).zfill(2) + '_' + str(m_last).zfill(2) + '_' + str(s_last).zfill(2)
imgs_last_time_plus_one = last_time  # 为了减少改动


img_data = cv2.imread(list_img[0])
# global record_list
record_list = []

click_time = 0


def onmouse(event, x, y, flags, param):
    global drag_start, sel
    global click_time
    global pos_show
    global pos_show_bias
    if state_mouse == state_mouse_init:
        if event == cv2.EVENT_LBUTTONDOWN:
            if click_time < parking_space:
                pos_show[click_time] = [x, y]
                pos_show_bias[click_time] = [x + bias, y]
                click_time += 1
                print(x, y)
    if state_mouse == frame_car_use_left_button:
        if event == cv2.EVENT_LBUTTONDOWN:
            drag_start = x, y
            sel = 0, 0, 0, 0
        elif event == cv2.EVENT_LBUTTONUP:
            drag_start = None
            car_frame_point[id_parking_num_change] = [(sel[0], sel[1]), (sel[2], sel[3])]
            car_frame_point_abs[id_parking_num_change] = [(sel[0], sel[1] + h_h), (sel[2], sel[3] + h_h)]
            print('是否保留该边框?是:点击回车确认;否:直接重画')
            # state_mouse = frame_car_use_left_button
        elif drag_start:
            if flags & cv2.EVENT_FLAG_LBUTTON:
                minpos = min(drag_start[0], x), min(drag_start[1], y)
                maxpos = max(drag_start[0], x), max(drag_start[1], y)
                sel = minpos[0], minpos[1], maxpos[0], maxpos[1]
                img = img_data.copy()
                cv2.rectangle(img, (sel[0], sel[1]), (sel[2], sel[3]), (0, 255, 255), 4)
                cv2.imshow("label", img)

            else:
                print("selection is complete")
                drag_start = None

# 在数字键用来改变停车状态下的简单显示


def tmp_print(state_loc):
    for idx_state_loc, i in enumerate(state_loc):
        if idx_state_loc < parking_space - 1:
            print(i, end='\t')
        else:
            print(i)

# 加减一秒数值状态简单显示


def tmp_print_time_label(state_loc, time_label):
    for i in state_loc:
        print(i, end='\t')
    print(time_label)

# 加减一秒数值状态删除显示


def tmp_print_for_delete(tmp_np_array):
    for i in tmp_np_array:
        print(i, end='')
    print('<--X')

# 加车牌函数


def add_plate_2_label_v2(data_raw):  # 待修改
    parking_state_txt_record_state = []
    for i in range(parking_space):
        parking_state_txt_record_state.append('0')  # 初始状态为0

    data_updata = []  # 第一行处理方法,见2加车牌
    for i in data_raw:
        data_updata.append(i[0])
        for idx_0 in range(parking_space):
            if (i[idx_0 + 1].split(':')[1] == '2') and (parking_state_txt_record_state[idx_0] == '0'):
                data_updata.append(i[idx_0 + 1] + ':蓝辽Axxxxx')
            else:
                data_updata.append(i[idx_0 + 1])
            if i[idx_0 + 1].split(':')[1] != '1':  # 若无此判断,则012的2显示不了车牌
                parking_state_txt_record_state[idx_0] = i[idx_0 + 1].split(':')[1]

    data_updata = np.array(data_updata)
    data_updata = data_updata.reshape((-1, parking_space + 1))

    return data_updata


def save_json_label(record_list, parking_space, path_json, imgs_last_time_plus_one, imgs_list_only_time):
    record_for_json = create_json_record(record_list, parking_space, imgs_last_time_plus_one, imgs_list_only_time)
    file = open(path_json, 'w', encoding='utf-8')
    json.dump(record_for_json, file, ensure_ascii=False)
    file.close()
    print(f'save json at:{path_json}')


# 补全记录(在记录的最后一条补全出车)
def complement_record_list(record_list, last_time, parking_space):  # 这里的last_time就是最后图片加1s的时间
    record_list_tmp = np.array(record_list)  # 得到记录
    record_list_tmp = record_list_tmp.reshape((-1, parking_space + 1))  # 排版
    record_list_last = record_list_tmp[-1]  # 得到最后一行

    for i in range(parking_space + 1):
        if i == 0:
            info = last_time
        else:
            info_splits = record_list_last[i].split(':')
            if len(info_splits) == 2:
                info = info_splits[0] + ':' + '0'
            elif len(info_splits) == 3:
                info = info_splits[0] + ':' + '0' + ':' + info_splits[2]

        record_list.append(info)
    return record_list


def save_label_and_print(record_list, path_txt, parking_space):
    print('============原始数据如下===============')
    record_list = np.array(record_list)
    record_list = record_list.reshape((-1, parking_space + 1))
    for i in record_list:
        for idx_i, j in enumerate(i):
            if idx_i < parking_space:
                print(j, end=' ')  # 原始数据加制表
            else:
                print(j)  # 最后一个数据加回车
    # 对所有结果按时间由小到大排序
    tmp = record_list.T  # np排序方法
    record_list_order = tmp[0].argsort()  # 得出比较结果
    record_list_new_order = record_list[record_list_order]  # 排序完毕
    # 去掉重复行
    tmp_f = record_list_new_order[0]  # 为了去掉重复行
    data_raw = []
    for idx_i, j in enumerate(tmp_f):  # 第一行的写法
        if idx_i < parking_space:
            data_raw.append(j)
        else:
            data_raw.append(j)

    for i in record_list_new_order[1:]:  # 后面的写法
        if (i != tmp_f).any():
            for idx_i, j in enumerate(i):
                if idx_i < parking_space:
                    data_raw.append(j)
                else:
                    data_raw.append(j)
        tmp_f = i

    data_raw = np.array(data_raw)
    data_raw = data_raw.reshape((-1, parking_space + 1))

    if ip_name in no_plate_list:  # ['177']
        record_list_new_order = data_raw
    else:
        record_list_new_order = add_plate_2_label_v2(data_raw)

    # 输出到txt
    path_txt = path_txt
    file = open(path_txt, 'a+', encoding='UTF-8')
    for i in record_list_new_order:
        for idx_i, j in enumerate(i):
            if idx_i < parking_space:
                file.write(j + ' ')
            else:
                file.write(j + '\n')
    file.close()
    print('save txt at :{}'.format(path_txt))

# 删除一行


def modify_record_list(record_list, list_img, idx):
    # 1.先找当前图片是否存在记录,无则显示无需修改,有则显示列表的idx
    # 2.取出相应记录,使用remove删除该图片名称下全部记录
    # if record_list is None:
    #     record_list = []
    #     print('记录里啥也没有,没东西可删')
    #     return record_list
    # #return要返回值,否则就会把record变成none

    if len(record_list) == 0:
        print('记录里啥也没有,没东西可删')
    else:
        tmp_np_array = np.array(record_list)
        tmp_np_array = tmp_np_array.reshape(-1, parking_space + 1)
        delete_time = '_'.join(os.path.splitext(list_img[idx])[0].split('_')[:3])

        if (tmp_np_array.T[0] == delete_time).any():  # any:不加括号是bug
            idx_for_delete = [idx for idx, i in enumerate(tmp_np_array.T[0]) if i == delete_time]  # 得到索引值
            idx_for_delete = idx_for_delete[::-1]  # 从后往前删除,否则idx失效
            tmp_np_array_for_print = tmp_np_array[idx_for_delete]  # 先取出要删除的
            for i in idx_for_delete:
                tmp_np_array = np.delete(tmp_np_array, i, 0)  # 将要删除的删除
            tmp_print_for_delete(tmp_np_array_for_print)  # 显示出已经删除的条目
            tmp_np_array = tmp_np_array.reshape(-1)  # 恢复record
            record_list = tmp_np_array.tolist()  # 恢复record
        else:
            print('记录中无当前时间条目')

    return record_list


def str_space_remove(content):
    temp = ''
    for letter in content:
        if letter != ' ':
            temp += letter
    return temp


cv2.namedWindow('label', 0)
cv2.namedWindow('next', 0)
cv2.startWindowThread()
cv2.resizeWindow('label', w_w, w_h)  # 宽,高
cv2.resizeWindow('next', w_w, w_h)  # 宽,高


def num_key_function(num_press, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block):
    if state_num_key == change_parking_state:
        if state_loc[num_press] == 2:
            state_loc[num_press] = 0
        else:
            state_loc[num_press] += 1
        tmp_print(state_loc)
    elif state_num_key == show_parking_num:
        id_parking_num_change = num_press
        print(f'{num_press}')
        print('按数字选择该空间所占车位,按回车确定', end=' ')
        state_num_key = change_parking_num
    elif state_num_key == change_parking_num:
        parking_num_block.append(num_press)
        print(f'{num_press}', end=' ')

    return state_loc, state_num_key, id_parking_num_change, parking_num_block


while idx < img_len - 1:
    idx_next = idx + 1
    img_data = cv2.imread(list_img[idx])
    img_data_next = cv2.imread(list_img[idx_next])
    if img_data is None:
        idx += 1
        continue
    if img_data_next is None:
        if img_data is None:
            idx += 1
            continue
        else:
            idx_next += 1
            continue

    img_data = show_parking_line(img_data, parking_list_np, 4)  # 画停车线
    img_data = img_data[h_h:h_l, ...]
    img_data_next = img_data_next[h_h:h_l, ...]

    h, m, s = os.path.splitext(list_img[idx])[0].split('_')[:3]
    h_p = int(h) - int(h_0)
    m_p = int(m) - int(m_0)
    s_p = int(s) - int(s_0)
    sec_pass = h_p * 3600 + m_p * 60 + s_p

    # 显示的是当前时间(使用图片文件名)
    img_data = cv2.putText(img_data, '_'.join([h.zfill(2), m.zfill(2), s.zfill(2)]), (x_panel, y_panel),
                           font, font_size, (0, 0, 255), font_width)  # 添加文字，字体大小，初始位置，颜色，粗细

    # 显示剩余时间
    img_data = cv2.putText(img_data, str(int(sec_sum - sec_pass) // 60) + 'm' + str(int(sec_sum - sec_pass) % 60) + 's', (x_panel, y_panel_bias),
                           font, font_size, (0, 255, 0), font_width)  # 添加文字，字体大小，初始位置，颜色，粗细

    if state_num_key == change_parking_num:
        if len(parking_num_block) > 1:  # 车位数据集合(选择跨车位停车时使用)
            parking_num_block.sort()
        parking_num[id_parking_num_change] = parking_num_block  # 写进去使命就完成了

    for i in range(parking_space):
        if len(car_frame_point[i]) == 0:
            pass
        else:
            # 画图时只使用当前的两点坐标,但是在记入label时,使用绝对值坐标
            img_data = cv2.rectangle(img_data, car_frame_point[i][0], car_frame_point[i][1], (0, 255, 255), 4)

    for i in range(parking_space):

        if state_num_key == show_parking_num:
            color_parking_space_num[i] = (0, 255, 255)
        elif state_num_key == change_parking_state:
            color_parking_space_num[i] = (255, 0, 0)
        elif state_num_key == change_parking_num:
            color_parking_space_num[i] = (255, 0, 0)

        if state_num_key == show_parking_num:
            color_parking_num[i] = (255, 0, 255)
        elif state_num_key == change_parking_state:
            color_parking_num[i] = (255, 0, 255)
        elif state_num_key == change_parking_num:
            color_parking_num[i] = (255, 0, 255)
            color_parking_num[id_parking_num_change] = (0, 255, 255)
        # 车位idx
        img_data = cv2.putText(img_data, str(i),
                               (pos_show[i][0], pos_show[i][1] + bias_y), font, font_size, color_parking_space_num[i], font_width)

        # 车位
        img_data = cv2.putText(img_data, str(parking_num[i]),
                               (pos_show[i][0], pos_show[i][1]), font, font_size, color_parking_num[i], font_width)

        # 状态标记
        img_data = cv2.putText(img_data, str(int(state_loc[i])),
                               (pos_show_bias[i][0], pos_show_bias[i][1] + bias_y), font, font_size + 1, (0, 0, 255), font_width)

    # cv2.namedWindow('label',0)
    # cv2.resizeWindow('label',w_w ,w_h)    #宽,高
    cv2.setMouseCallback('label', onmouse, 0)  # 鼠标操作回调函数
    # cv2.startWindowThread()
    cv2.imshow('label', img_data)

    # cv2.namedWindow('next',0)
    # cv2.resizeWindow('next',w_w ,w_h)    #宽,高
    cv2.imshow('next', img_data_next)

    key = cv2.waitKeyEx(1)  # 等待按键
    if act == 1:
        idx += 1

    if key == 27:  # ESC
        break
    elif key == ord(' '):  # 空格控制act
        if act:
            act = 0
        else:
            act = 1
    elif key == ord('s') or key == ord('S'):  # s 前进3min
        idx += three_mins
    elif key == ord('d') or key == ord('D'):  # d前进5min
        idx += five_mins
    elif key == ord('a') or key == ord('A'):  # a后退5min
        if idx > 0:
            idx -= five_mins
        else:
            idx = 0
    elif key == ord('w') or key == ord('W'):  # w 后退3min
        if idx > 0:
            idx -= three_mins
        else:
            idx = 0
    elif key == 2490368:  # 上
        if idx > 0:
            idx -= 1
        else:
            idx = 0

    elif key == 2621440:  # 下
        idx += 1
    elif key == 2424832:  # 左
        if idx > 10:
            idx -= one_min  # 1min
        else:
            idx = 0
    elif key == 2555904:  # 右
        idx += one_min  # 1min
    elif key == 13:  # p或回车
        if state_mouse == frame_car_use_left_button:
            # 待改进
            print(f'两点当前坐标为({sel[0]}, {sel[1]}), ({sel[2]}, {sel[3]})')
            print(f'两点绝对坐标为({sel[0]}, {sel[1]+h_h}), ({sel[2]}, {sel[3]+h_h})')
            state_mouse = state_mouse_init  # 将状态返回为初始化
            continue

        if state_num_key == change_parking_num:
            if len(parking_num_block) == 0:
                parking_num_block = []  # 为其复位,归空
                print('请赋值')
            elif len(parking_num_block) == 1:  # 列表里只有一个值
                state_num_key = change_parking_state
                # car_frame_point[parking_num_block[0]] = []  # 取出唯一的值作为索引,并将里面的值去掉,成为[],这样不对
                car_frame_point[id_parking_num_change] = []  # 取出唯一的值作为索引,并将里面的值去掉,成为[]
                parking_num_block = []  # 为其复位,归空
                print('赋值已完成,不需要画框了')
            elif len(parking_num_block) > 1:
                state_num_key = change_parking_state
                state_mouse = frame_car_use_left_button
                parking_num_block = []  # 为其复位,归空
                print("\n赋值结束,请用鼠标左键为车画框")
        elif state_num_key == change_parking_state:
            if state_time_label_overwrite == 0:  # 如果秒数没有被改写
                # record_list.append(os.path.splitext(list_img[idx])[0])  # 先记录时间
                record_list.append('_'.join([h.zfill(2), m.zfill(2), s.zfill(2)]))  # 先记录时间
                for idx_state_loc, i in enumerate(state_loc):  # 再记录数据
                    parking_num_str = str_space_remove(str(parking_num[idx_state_loc]))
                    if len(car_frame_point[idx_state_loc]) == 0:
                        record_list.append(parking_num_str + ':' + str(i))
                    else:
                        car_frame_point_abs_str = str_space_remove(str(car_frame_point_abs[idx_state_loc]))
                        record_list.append(parking_num_str + ':' + str(i) + ':' + car_frame_point_abs_str)

                for i in state_loc:
                    print(i, end='\t')
                # print(os.path.splitext(list_img[idx])[0], end=' ')
                print('_'.join([h.zfill(2), m.zfill(2), s.zfill(2)]), end=' ')
                print('<---')

            else:
                record_list.append(time_label)  # 先记录时间
                for idx_state_loc, i in enumerate(state_loc):  # 再记录数据
                    parking_num_str = str_space_remove(str(parking_num[idx_state_loc]))
                    if len(car_frame_point[idx_state_loc]) == 0:
                        record_list.append(parking_num_str + ':' + str(i))
                    else:
                        car_frame_point_abs_str = str_space_remove(str(car_frame_point_abs[idx_state_loc]))
                        record_list.append(parking_num_str + ':' + str(i) + ':' + car_frame_point_abs_str)

                for i in state_loc:
                    print(i, end='\t')
                print(time_label, end=' ')
                print('<---')

            state_time_label_overwrite = 0  # 更改状态
    elif (key == ord('p')) or key == ord('P'):  # p
        if state_num_key == change_parking_state:
            print("点击数字选择一个要更改的停车区域,从零开始", end=' ')
            state_num_key = show_parking_num

    elif (key == ord('o')) or key == ord('O'):  # o或O
        if state_num_key == show_parking_num:
            print("\n状态恢复")
            state_num_key = change_parking_state

    elif key == ord('f') or key == ord('F'):  # f 时间标签增加1s
        tmp = sec_pass + initial_time_sec
        tmp += 1
        time_label = f'{tmp//3600:02d}_{tmp%3600//60:02d}_{tmp%60:02d}'  # 上下都行
        state_time_label_overwrite = 1
        tmp_print_time_label(state_loc, time_label)

    elif key == ord('r') or key == ord('R'):  # r 时间标签减少1s
        tmp = sec_pass + initial_time_sec
        tmp -= 1
        time_label = f'{tmp//3600:02d}_{tmp%3600//60:02d}_{tmp%60:02d}'  # 上下都行
        state_time_label_overwrite = 1
        tmp_print_time_label(state_loc, time_label)

    elif key == ord('m') or key == ord('M'):  # m 减去当前图片名下的一条数据
        record_list = modify_record_list(record_list, list_img, idx)

    elif key == ord('l') or key == ord('L'):  # l leave 离开需要马上打印
        record_list = complement_record_list(record_list, last_time, parking_space)
        save_label_and_print(record_list, path_txt, parking_space)
        # save_json_label(record_list, parking_space, path_json)

    elif key == 48 and parking_space > 0:  # 0
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(0, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 49 and parking_space > 1:  # 1
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(1, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 50 and parking_space > 2:  # 2
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(2, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 51 and parking_space > 3:  # 3
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(3, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 52 and parking_space > 4:  # 4
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(4, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 53 and parking_space > 5:  # 5
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(5, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 54 and parking_space > 6:  # 6
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(6, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 55 and parking_space > 7:  # 7
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(7, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 56 and parking_space > 8:  # 8
        state_loc, state_num_key, id_parking_num_change, parking_num_block = \
            num_key_function(8, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    # elif key == 57 and parking_space > 9:  # 9
    #     state_loc, state_num_key, id_parking_num_change, parking_num_block = \
    #         num_key_function(9, state_num_key, change_parking_state, show_parking_num, state_loc, id_parking_num_change, parking_num_block)

    elif key == 57:  # 9
        record_list = complement_record_list(record_list, last_time, parking_space)
        save_label_and_print(record_list, path_txt, parking_space)
        save_json_label(record_list, parking_space, path_json, imgs_last_time_plus_one, imgs_list_only_time)

if key != 27:  # ESC没按输出结果到txt
    record_list = complement_record_list(record_list, last_time, parking_space)
    save_label_and_print(record_list, path_txt, parking_space)
    # save_json_label(record_list, parking_space, path_json, imgs_last_time_plus_one, imgs_list_only_time)


cv2.destroyAllWindows()
print('程序结束')
