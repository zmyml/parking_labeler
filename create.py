import os
import numpy as np

# 注意:imgs_last_time_plus_one是当天的最后一张图片加一秒,不是单个车的最后目击时间


def create_json_record(parking_record, parking_space, imgs_last_time_plus_one, imgs_list):
    record_for_json = []

    parking_record = np.array(parking_record)
    if isinstance(parking_space, int):
        parking_space = [f'[{i}]' for i in range(parking_space)]

    parking_record = parking_record.reshape((-1, len(parking_space) + 1))

    # 补全记录:如果最后记录时间不是最后时间加一秒,则增加时间,并增加出车记录
    if parking_record[-1][0] != imgs_last_time_plus_one:
        last_record = [imgs_last_time_plus_one]
        for i in parking_space:
            last_record.append(f'{i}:0')
        last_record = np.array(last_record)
        last_record = last_record.reshape((1, len(parking_space) + 1))
        parking_record = np.concatenate((parking_record, last_record), axis=0)

    else:  # 如果最后一条记录时间是最后时间加1秒,但记录不是全部出车,则重新做全部出车记录
        if set([i.split(':')[1] for i in parking_record[-1][1:]]) != {'0'}:
            last_record = [imgs_last_time_plus_one]
            for i in parking_space:
                last_record.append(f'{i}:0')
            last_record = np.array(last_record)
            last_record = last_record.reshape((1, len(parking_space) + 1))
            parking_record = np.concatenate((parking_record[:-1], last_record), axis=0)

    for col_num in range(1, parking_record.shape[-1]):
        record_for_dic = []
        parking_pos_list = []
        parking_time_list = []
        parking_num_list_2 = []
        parking_plate_list = []
        parking_state_past = '0'
        cols_parking_record = parking_record[:, [0, col_num]]
        for i in cols_parking_record:
            record_time = ''
            parking_num_list = []
            parking_state = ''
            parking_plate = ''
            parking_unknown = ''
            # 分解数据
            record_time = i[0]

            data_len = len(i[1].split(':'))
            if data_len == 4:  # 本行含坐标pos
                parking_num_list, parking_state, parking_pos, parking_plate = i[1].split(':')
            elif data_len == 3:  # 本行不含坐标pos
                parking_num_list, parking_state, parking_unknown = i[1].split(':')
                if parking_unknown[0] == '[':
                    parking_pos = parking_unknown  # 坐标
                    parking_plate = ''
                else:
                    parking_plate = parking_unknown
                    parking_pos = ''
            elif data_len == 2:  # 本行不含坐标pos
                parking_num_list, parking_state = i[1].split(':')
                parking_pos = ''  # 坐标pos为空
                parking_plate = ''

            # 判断数据
            if parking_state != parking_state_past:          # 停车状态与之前状态不同
                if parking_pos not in parking_pos_list:      # 不会储存重复的数值,包括''
                    parking_pos_list.append(parking_pos)     # 位置

                if parking_plate not in parking_plate_list:
                    parking_plate_list.append(parking_plate)  # 车牌

                if parking_num_list not in parking_num_list_2:
                    parking_num_list_2.append(parking_num_list)  # 车位号

                if record_time + '.jpg' in imgs_list:  # 只要时间在图片中,不管啥状态都记录
                    # 发生状态改变(不是'0'了),记录时间和状态
                    parking_time_list.append([parking_state, record_time])

                elif parking_state == '0':  # 不在图片列表但为0,时间变为之后的一张 ## 特别指出:若不在图片且为1,则不要这条记录
                    record_time_list = list(filter(lambda x: x > record_time + '.jpg', imgs_list))  # 看还有没有下一张图片

                    if record_time_list:  # 如果有下一张图片,替换记录时间为下一张图片时间
                        record_time_list.sort()
                        record_time = os.path.splitext(record_time_list[0])[0]
                    # 若列表为空则条件不满足,不替换记录时间,并进行记录
                    # 发生状态改变(不是'0'了),记录时间和状态
                    parking_time_list.append([parking_state, record_time])
                    # 同时增加最后目击时间
                    record_time_list = list(filter(lambda x: x < record_time + '.jpg', imgs_list))  # 找上一张图片

                    if record_time_list:  # 如果有上一张图片,记录图片时间为最后目击时间
                        record_time_list.sort()
                        record_time = os.path.splitext(record_time_list[-1])[0]
                    parking_time_list.append(['-1', record_time])  # 状态是'-1',最后目击时间

                # 特别指出:若不在图片且为1,则不要这条记录
                # 以上程序出现的json文件时间为处理好的时间,如果有状态2-1-2,则1是可见的状态(不是虚拟),那么再json转class类的时候,需要对这个1进行记录
                # 记录1的目的是:对停车间隔时间进行计时

            parking_state_past = parking_state  # 为过去状态更新新的数值

            if parking_state_past == '0':  # 若为0,代表完成一车的记录,在之前记录不为零时可以将记录进行保存
                if len(parking_time_list) != 0:
                    parking_plate_tmp = [
                        i for i in parking_plate_list if i != '']
                    if len(parking_plate_tmp) == 0:
                        parking_plate = ''
                    else:
                        parking_plate = parking_plate_tmp[0]
                    record_for_dic.append(parking_plate)  # 第一项:车牌
                    # record_for_dic.append(list(set(parking_num_list_2))) #第二项:车位去掉重复(顺序发生改变,不好)
                    parking_num_list_2_tmp = []  # 第二项:车位去掉重复(顺序正确)
                    for i in parking_num_list_2:
                        if i not in parking_num_list_2_tmp:
                            parking_num_list_2_tmp.append(i)
                    record_for_dic.append(parking_num_list_2_tmp)

                    # 发现有坐标值和''同时在列表的情况,当列表大于1且''在列表时,删除''
                    if (len(parking_pos_list) > 1) and ('' in parking_pos_list):
                        parking_pos_list.remove('')
                    record_for_dic.append(parking_pos_list)  # 第三项:坐标
                    record_for_dic.append(parking_time_list)  # 第四项:时间
                    d = dict({'plate': record_for_dic[0],
                              'parking_num': record_for_dic[1],
                              'parking_pos': record_for_dic[2],
                              'time': record_for_dic[3]})
                    record_for_json.append(d)
                    # 列表复位
                    record_for_dic = []
                    parking_pos_list = []
                    parking_time_list = []
                    parking_num_list_2 = []
                    parking_plate_list = []

    return record_for_json
