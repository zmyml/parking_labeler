# 车牌人眼识别统计(项目暂不用代码统计)
import os

label_root_path = r'X:\20191014\2019_10_12'

horizontal_cam_ip = ['DDT2G1907ZMY00009SY_1010', 'DDT2G1907ZMY00016SY_1010', 'DDT2G1907ZMY00020SY_1010']


def find_child_folder(root_path, filter_ip):
    child_folder_list = []
    for root, path, file in os.walk(root_path):
        if path == []:
            child_folder_list.append(os.path.basename(root))
    return [i for i in child_folder_list if i in filter_ip]


def find_child_folder_label(folder_list: list, root_path):
    label_list = []
    for folder in folder_list:
        label_path = os.path.join(root_path, f'{folder}_label.txt')
        if os.path.isfile(label_path):
            label_list.append(label_path)
    return label_list


# def
# a = find_child_folder(label_root_path, horizontal_cam_ip)
# os.chdir(label_root_path)
# b = find_child_folder_label(a, label_root_path)
# b
