import os
import sys
sys.path.append(os.path.dirname(os.path.basename(__file__)))

import pandas
import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split


def split_dataframe(folder_label_path: str, shuffle: bool = True) \
        -> Tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]:
    # Split training dataframe to training and validation by train.csv
    df_train_val = pd.read_csv(os.path.join(folder_label_path, 'train.csv'))
    list_name = df_train_val['name'].unique()
    list_train, list_val = train_test_split(list_name, test_size=0.14, shuffle=shuffle)
    df_train = df_train_val.set_index('name').loc[list_train[:]].reset_index()
    df_val = df_train_val.set_index('name').loc[list_val[:]].reset_index()

    # Prepare dataframe for testing by test.csv
    df_test = pd.read_csv(os.path.join(folder_label_path, 'test.csv'))

    return df_train, df_val, df_test


def load_list_data(dataframe: pandas.DataFrame, folder_image_path: str,
                   label_off_set: int = 1, norm: bool = True)\
                                     -> Tuple[list, list, list]:
    # Clean error bounding box (area <= 100)
    dataframe = dataframe[(dataframe['x2']-dataframe['x1']) * (dataframe['y2']-dataframe['y1']) > 100].reset_index(
        drop=True)
    dataframe['name'] = dataframe['name'].apply(lambda name: os.path.join(folder_image_path, name))
    if norm:
        dataframe['x1'] = dataframe['x1'] / dataframe['width']
        dataframe['x2'] = dataframe['x2'] / dataframe['width']
        dataframe['y1'] = dataframe['y1'] / dataframe['height']
        dataframe['y2'] = dataframe['y2'] / dataframe['height']
    dataframe['bbox'] = dataframe.iloc[:][['x1', 'y1', 'x2', 'y2']].values.tolist()
    dataframe['id_category'] = dataframe['id_category'] - label_off_set

    # Join necessary data, of same image, into a list
    # TODO: Explain the code bellow
    list_image_path = dataframe.groupby(['name'])['name'].apply(list).index.tolist()
    list_classes = dataframe.groupby(['name'])['id_category'].apply(list).values.tolist()
    list_boxes = dataframe.groupby(['name'])['bbox'].apply(list).values.tolist()

    return list_image_path, list_boxes, list_classes


def create_yolo_labels(folder_image_path: str, folder_label_path: str) -> None:
    def create_labels_txt(dataframe: pandas.DataFrame, folder_image_path: str, folder_label_path: str) -> None:
        list_image_path, list_boxes, list_classes = load_list_data(dataframe, folder_image_path)
        for image, boxes, classes in zip(list_image_path, list_boxes, list_classes):
            image_file = os.path.join(folder_label_path, os.path.basename(image).split('.')[0] + '.txt')

            file = open(image_file, "w")
            for box, cat in zip(boxes, classes):
                file.write(str(cat) + ' ')
                file.write(str((box[2]+box[0]) / 2) + ' ')
                file.write(str((box[3]+box[1]) / 2) + ' ')
                file.write(str(box[2] - box[0]) + ' ')
                file.write(str(box[3] - box[1]) + '\n')
            file.close()

    # Create labels for yolo
    for dir in ["train", "test"]:
        if (not os.path.isdir(os.path.join(folder_label_path, dir))):
            os.mkdir(os.path.join(folder_label_path, dir))
            dataframe = pd.read_csv(os.path.join(folder_label_path, dir + ".csv"))
            create_labels_txt(dataframe, os.path.join(folder_image_path, dir), os.path.join(folder_label_path, dir))
