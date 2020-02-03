import os
import json

json_home = r'C:\Users\tongxin\Desktop\label_test_2019_10_22'
# 文件名:车位数量
parking_num_dic = {'DDT2G1907ZMY00009SY_1010_label_v2.json': 2,
                   'DDT2G1907ZMY00016SY_1010_label_v2.json': 2,
                   'DDT2G1907ZMY00020SY_1010_label_v2.json': 2}


def get_all_json_path(path):
    """输入总json路径,输出全部json路径

    Args:
        path: json根目录

    Returns:
        json路径列表
    """
    all_path = []
    for root, dir, files in os.walk(json_home):
        if not dir:
            for file_name in files:
                all_path.append(os.path.join(root, file_name))

    return all_path


for path in get_all_json_path(json_home):
    root, file_name = os.path.split(path)
    if file_name in parking_num_dic:
        os.chdir(root)
        with open(path, 'r', encoding='utf-8') as load_json:
            json_label_list = json.load(load_json)

        for dic in json_label_list:
            for num in dic['parking_num']:
                if isinstance(num, int):
                    if num >= parking_num_dic[file_name]:
                        print(f'err label:{path}')
                elif isinstance(num, list):
                    for n in num:
                        if n >= parking_num_dic[file_name]:
                            print(f'err label:{path}')

print('done')
