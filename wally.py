"""
Mask R-CNN

Usage: import the module (see Jupyter notebooks for examples), or run from
       the command line as such:

       # Train a new model starting from pre-trained HOTDOG weights
       To train model: python3 samples\hotdog\hotdog.py train --dataset=datasets\hotdog\train --model=coco
"""

import os

import args as args
import numpy as np
import sys
import json
import datetime
import skimage.draw
import logging

# root directory of the project
ROOT_DIR = os.getcwd()
if (ROOT_DIR.endswith("src/wally")) :
    # go back two directories to the repo root
    ROOT_DIR = os.path.dirname(os.path.dirname((ROOT_DIR)))

# import Mask RCNN
sys.path.append(ROOT_DIR)
from config import Config
import utils
import model as modellib

# path to trained weights file
COCO_WEIGHTS_PATH = os.path.join(ROOT_DIR, "mask_rcnn_wally.h5")

# directory to save the logs and model checkpoints, if not provided through the command line argument --logs
DEFAULT_LOGS_DIR = os.path.join(ROOT_DIR, "logs")


# Configurations ---------------------------------------------------------------------
class WallyConfig(Config) :
    """
        Configuration for training on wallys.
        Derives from the base Config class and overrides values specific to the wally dataset.
    """
    # give the configuration a recognizable name
    NAME = "wally"
    # depending on the memory our gpu has, we change the number of images we can fit at once.
    # 128GB = 2 images
    IMAGES_PER_GPU = 2

    # number of classes (including background)
    NUM_CLASSES = 1 + 1 # wally has 1 class
    STEPS_PER_EPOCH = 100
    DETECTION_MIN_CONFIDENCE = 0.9


# Dataset ----------------------------------------------------------------------------
class WallyDataset(utils.Dataset) :
    # load the train wally set
    def loadWally(self, datasetDir, subset) :
        self.add_class("wally", "1", "wally")
        # assert subset in ["train", "val"]
        datasetDir = os.path.join(datasetDir, subset)
        annotations = json.load(open(os.path.join(datasetDir, "via_region_data.json")))
        annotations = list(annotations.values())

        annotations = [a for a in annotations if a['regions']]

        # add images
        for a in annotations :
            # get the x, y coords of points of the polygons that make up the outline of
            # each object instance. There are stored in the shape_attributes
            polygons = [r['shape_attributes'] for r in a['regions'].values()]

            image_path = os.path.join(datasetDir, a['filename'])
            height, width = self.getHeightWidth(image_path)

            self.add_image(
                "wally",
                # use the file name as a unique image id
                image_id = a['filename'],
                path = image_path,
                width = width,
                height = height,
                polygons = polygons
            )

    def getHeightWidth(self, image_path) :
        image = skimage.io.imread(image_path)
        height, width = image.shape[:2]

        return height, width

    def loadMask(self, image_id) :
        image_info = self.image_info[image_id]
        if (image_info['source'] != 'wally') :
            return super(self.__class__, self).loadMask(image_id)

        info = self.image_info[image_id]
        mask = np.zeros([info['height'], info['width'], len(info['polygons'])], dtype=np.uint8)

        for i, p in enumerate(info['polygons']) :
            # get the indexes of pixels inside the polygon and set them to 1
            rr, cc = skimage.draw.polygon(p['all_points_y'], p['all_points_x'])
            mask[rr, cc, i] = 1

        # return the mask and array of classification IDs of each instance. Since we have one class ID only, we return
        # an array of 1s
        return mask, np.ones([mask.shape[-1]], dtype=np.int32)

    # get the path of a wally image
    def imageReference(self, image_id) :
        info = self.image_info[image_id]
        if (info['source'] == 'wally') :
            return info['path']
        else :
            super(self.__class__, self).imageReference(image_id)


def train(model) :
    """
    Train the model
    """
    # training dataset
    dataset_train = WallyDataset()
    dataset_train.loadWally(args.dataset, "train")
    dataset_train.prepare()

    # validation dataset
    dataset_val = WallyDataset()
    dataset_val.loadWally(args.dataset, "val")
    dataset_val.prepare()

    # since we're using a small dataset, and starting from COCO trained weights, we dont need to train for too long.
    # also, there is no need to train all of the layers, just the heads should work fine.
    print("Training network heads")

    model.train(dataset_train, dataset_val,
                learning_rate=Config.LEARNING_RATE,
                epochs=30,
                layers='heads')

if __name__ == '__main__' :
    import argparse

    # parse the command line arguments
    parser = argparse

























