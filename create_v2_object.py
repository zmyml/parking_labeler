import os
import numpy as np

# 注意:imgs_last_time_plus_one是当天的最后一张图片加一秒,不是单个车的最后目击时间


class Parking_Record:
    def __init__(self, plate, parking_num, parking_pos):
        self.plate = plate
        self.parking_num = [parking_num]
        self.parking_pos = [parking_pos]
        self.time = []

    def __str__(self):
        if self.text:
            return self.plate
        else:
            return "车牌未标记"


def create_json_record(parking_record, parking_space, imgs_last_time_plus_one, imgs_list):
    record_for_json = []
    parking_record_list = []

    parking_record = np.array(parking_record)
    if isinstance(parking_space, int):  # 如果parking_space是数,变成列表,没啥用,就是为了计数
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

    # 处理记录信息
    for col_num in range(1, parking_record.shape[-1]):
        record_for_dic = []
        parking_pos_list = []
        parking_time_list = []
        parking_plate_list = []
        parking_state_past = 'out'
        cols_parking_record = parking_record[:, [0, col_num]]  # 当前记录是时间列 记录列 两列
        for i in cols_parking_record:
            record_time = ''
            parking_num_list = []
            parking_state = ''
            parking_plate = ''
            parking_unknown = ''
            # 分解数据
            record_time = i[0]  # 时间列

            records = i[1].split(':')
            data_len = len(records)
            if data_len == 4:  # 本行含坐标pos
                parking_num_list, parking_state, parking_pos, parking_plate = records
            elif data_len == 3:  # 本行不含坐标pos
                parking_num_list, parking_state, parking_unknown = records
                if parking_unknown.startswith('['):
                    parking_pos = parking_unknown  # 坐标
                    parking_plate = ''
                else:
                    parking_plate = parking_unknown
                    parking_pos = ''
            elif data_len == 2:  # 本行不含坐标pos
                parking_num_list, parking_state = records
                parking_pos = ''  # 坐标pos为空
                parking_plate = ''

            if isinstance(parking_num_list, str):
                parking_num_list = parking_num_list.strip('[]').split(',')
                parking_num_list = [int(i) for i in parking_num_list]
                if len(parking_num_list) == 1:
                    parking_num_list = parking_num_list[0]

            if isinstance(parking_pos, str):
                if parking_pos == '':
                    parking_pos = None
                else:
                    parking_pos_tmp = parking_pos.strip('[()]').split('),(')
                    parking_pos_tmp = [i.strip('()').split(',') for i in parking_pos_tmp]
                    parking_pos = [[int(j) for j in i]for i in parking_pos_tmp]
                # print(parking_pos)

            if parking_state == '0':
                parking_state = 'out'
            elif parking_state == '1':
                parking_state = 'move'
            elif parking_state == '2':
                parking_state = 'stop'

            # # 判断数据
            if parking_state != parking_state_past:  # 当前状态与之前状态不同
                if parking_record_list == [] or parking_state_past == 'out':  # 记录列表为空,或之前状态位'0',创建新的记录
                    precord = Parking_Record(parking_plate, parking_num_list, parking_pos)
                    precord.time.append([f'{parking_state}', record_time])
                    parking_record_list.append(precord)
                else:  # 记录列表不为空,且之前状态不为'0',认为是前一个记录需要补全的
                    precord = parking_record_list[-1]
                    if parking_state == 'stop':  # 若是1-2的情况,需要增加车牌plate信息
                        if parking_plate != '':
                            precord.plate = parking_plate
                        if precord.parking_num[-1] != parking_num_list:  # 若是1-2-1-2这样的情况,可能有多种parking_list需要记录
                            precord.parking_num.append(parking_num_list)
                    if parking_pos not in precord.parking_pos:
                        precord.parking_pos.append(parking_pos)
                    precord.time.append([f'{parking_state}', record_time])

            parking_state_past = parking_state

    for precord in parking_record_list:
        if len(precord.parking_pos) == 1 and precord.parking_pos[0] is None:
            d = dict({'plate': precord.plate, 'parking_num': precord.parking_num,
                      'time': precord.time})
        else:
            d = dict({'plate': precord.plate, 'parking_num': precord.parking_num,
                      'parking_pos': precord.parking_pos, 'time': precord.time})

        record_for_json.append(d)

    return record_for_json
