import os
import cv2
import sys
import csv
import augmentation as aug
import config as cf
import numpy as np
from operator import div
from PIL import Image

# print all the name of images in the directory.
def print_all_imgs(in_dir):
    for subdir, dirs, files in os.walk(in_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                print(file_path)

# check if the given file is an image format
def is_image(f):
    return f.endswith(".png") or f.endswith(".jpg")

# check if dir exists. If not, mkdir.
def check_and_mkdir(in_dir):
    if not os.path.exists(in_dir):
        print("Creating "+in_dir+"...")
        os.makedirs(in_dir)

# read and print all the image sizes of the dir.
def read_all_imgs(in_dir):
    for subdir, dirs, files in os.walk(in_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                img = cv2.imread(file_path)
                print('{:<100} {:>10}'.format(file_path, str(img.shape)))
                # print(file_path + ",img size = "+str(img.shape))

def normalize_images(in_dir, out_dir):
    check_and_mkdir(out_dir) # sanity check for the target output directory

    for subdir, dirs, files in os.walk(in_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                #img = cv2.imread(file_path)
                #resized_img = cv2.resize(img, (target_size, target_size), interpolation = cv2.INTER_CUBIC)
                im = Image.open(file_path).convert("RGB")
                x, y = im.size
                edge = x if x > y else y
                im2 = Image.new("RGB", (edge, edge))
                im2.paste(im, (0, 0, x, y))
                class_dir = out_dir + os.sep + file_path.split("/")[-2]
                check_and_mkdir(class_dir) # sanity check for the target class directory
                
                file_name = class_dir + os.sep + file_path.split("/")[-1]
                print(file_name)
                #cv2.imwrite(file_name, resized_img)
                im2.save(file_name)
                im.close()
                im2.close()

# resize the imgs from in_dir, and save with exact same hierarchy in the out_dir
def resize_images(in_dir, out_dir, target_size):
    check_and_mkdir(out_dir) # sanity check for the target output directory

    for subdir, dirs, files in os.walk(in_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                img = cv2.imread(file_path)
                resized_img = cv2.resize(img, (target_size, target_size), interpolation = cv2.INTER_CUBIC)
                class_dir = out_dir + os.sep + file_path.split("/")[-2]
                check_and_mkdir(class_dir) # sanity check for the target class directory

                file_name = class_dir + os.sep + file_path.split("/")[-1]
                print(file_name)
                cv2.imwrite(file_name, resized_img)

# count the direct one-step sub directories (which will represent the class name)
def class_info(in_dir, mode):
    class_lst = []

    for subdir, dirs, files in os.walk(in_dir):
        class_lst = dirs # the 'dirs' variable after the first os.walk loop will return the list of classes
        break

    if(mode == "len"):
        return (len(class_lst))
    elif(mode == "list"):
        return (class_lst)

# count the containing images of each classes
def count_each_class(in_dir):
    class_lst, cnt_lst = class_info(in_dir, "list"), []

    for class_dir in class_lst:
        class_count = 0
        for subdir, dirs, files in os.walk(in_dir + os.sep + class_dir):
            for f in files:
                file_path = subdir + os.sep + f
                if (is_image(f)):
                    class_count += 1

        print("\t| {:<15} {:>5}".format(class_dir, class_count))
        cnt_lst.append(class_count)

    return cnt_lst

# return whether the current phase is 'train' or 'validation'
def return_phase(num, val_num):
    if (num < val_num):
        return "val" + os.sep
    else:
        return "train" + os.sep

# create a train-val sub-organized directory from the original class directory
def create_train_val_split(in_dir, split_dir):
    print("Saving train-val splitted images into %s" %(split_dir))
    check_and_mkdir(split_dir)
    class_lst = class_info(in_dir, "list")

    for phase in ["train", "val"]:
        phase_dir = split_dir + os.sep + phase # The output directory will be "./split/[:file_dir]/[:phase]/[:class]"
        check_and_mkdir(phase_dir)

        for cls in class_lst:
            cls_dir = split_dir + os.sep + phase + os.sep + cls # Where to read the image from
            check_and_mkdir(cls_dir)

    val_num = cf.val_num # temporary

    for subdir, dirs, files in os.walk(in_dir):
        cnt = 0
        for f in files:
            file_path = subdir + os.sep + f
            if(is_image(f)):
                img = cv2.imread(file_path)
                cv2.imwrite(split_dir + os.sep + return_phase(cnt, val_num) + subdir.split("/")[-1] + os.sep + f, img)
                cnt += 1

    return split_dir

# get train-val information
def get_split_info(split_dir):
    # Must be activated after the 'split' option.
    for phase in ["train", "val"]:
        print("| %s set : " %phase)
        count_each_class(split_dir + os.sep + phase)

    return split_dir

# train data augmentation
def aug_train(split_dir):
    train_dir = split_dir + os.sep + "train"

    for subdir, dirs, files in os.walk(train_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                print(file_path)
                name, ext = os.path.splitext(f)
                img = cv2.imread(file_path)
                for i in range(3):
                    rot_dir = (subdir + os.sep + name + "_aug_"+str(i+1)+ext)
                    cv2.imwrite(rot_dir, aug.random_rotation(img))

def train_mean(split_dir):
    train_dir = split_dir + os.sep + "train"
    train_img_num = 0
    train_mean_lst = [0.0, 0.0, 0.0]

    for subdir, dirs, files in os.walk(train_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                img = cv2.imread(file_path)
                train_img_num += 1
                for channel in range(3):
                    train_mean_lst[channel] += img[:,:,channel].mean()

    mean_map = map(div, train_mean_lst, [train_img_num, train_img_num, train_img_num])
    return map(div, mean_map, [255.0, 255.0, 255.0])

def train_std(split_dir, train_mean):
    train_dir = split_dir + os.sep + "train"
    train_img_num = 0
    train_std_lst = [0.0, 0.0, 0.0]

    for subdir, dirs, files in os.walk(train_dir):
        for f in files:
            file_path = subdir + os.sep + f
            if (is_image(f)):
                img = cv2.imread(file_path)
                train_img_num += 1
                for channel in range(3):
                    train_std_lst[channel] += img[:,:,channel].var() # per image var()

    std_map = map(div, train_std_lst, [train_img_num, train_img_num, train_img_num])
    std_map = np.sqrt(std_map)
    return map(div, std_map, [255.0, 255.0, 255.0])
