import os
# 文件夹根目录，年月日目录的上一级目录
im_path_root = r'E:\home_label'

for root, dirs, files in os.walk(im_path_root):
    if dirs == []:
        os.chdir(root)
        for name in files:
            if name.endswith('jpg'):
                splits = name.split('_')
                if len(splits) > 6:
                    new_name = '_'.join(splits[3:6])+'.jpg'
                    os.rename(name, new_name)   