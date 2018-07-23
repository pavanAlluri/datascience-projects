"""
Some methods which make the VOC dataset easier to explore
"""

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
import copy

from pathlib import Path
import xml.etree.ElementTree as ET


def load_image(image_path):
    """
    opencv returns the image in blue green red, not red green blue
    This function corrects for this
    """
    image_array = cv2.imread(image_path.as_posix())

    # [2, 1, 0] compared to ::-1 prevents a stride problem with pytorch
    return image_array[:, :, [2, 1, 0]]


def xml_to_dict(file_path, image_folder_path=Path('VOC2007/JPEGImages')):
    """
    Given a VOC xml annotation, turn it into a dictionary
    we can manipulate
    """
    tree = ET.parse(file_path)  # create an ElementTree object
    root = tree.getroot()
    object_id = 0

    # first, get the image filename
    image_filename = root.find('filename').text
    xml_dict = {'image_path': image_folder_path/image_filename}

    # Then, get all the bounding box coordinates
    xml_dict['objects'] = {}
    for child in root:
        if child.tag == 'object':
            object_name = child.find('name').text
            bounding_box = child.find('bndbox')

            xml_dict['objects'][object_id] = {'name': object_name,
                                              'coordinates':
                                                  [int(bounding_box.find('xmin').text),
                                                   int(bounding_box.find('ymin').text),
                                                   int(bounding_box.find('xmax').text),
                                                   int(bounding_box.find('ymax').text)]}
            object_id += 1
    return xml_dict


def show_annotation(annotation):
    """
    Given a dictionary of the annotation,
    plots the corresponding image with the bounding boxes
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    # first, load up the image
    image_path = annotation['image_path']
    image_to_plot = load_image(image_path)
    ax.imshow(image_to_plot)

    # then, all the bounding boxes
    for anno_id, anno in annotation['objects'].items():
        bounding_box = anno['coordinates']
        label = anno['name']
        xmin, ymin, xmax, ymax = bounding_box
        width = xmax - xmin
        height = ymax - ymin
        rect = patches.Rectangle((xmin, ymin),
                                 width, height,
                                 linewidth=1, edgecolor='xkcd:bright green',
                                 facecolor='none', label=label)
        ax.add_patch(rect)
        ax.text(xmin, ymin, label, color='xkcd:bright green', fontsize=12)

    # finally, remove the axes
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)

    plt.show()


def show_random_example(VOC_path=Path('VOC2007'), return_annotation=False):
    """
    Given the VOC directory, plot a random example
    """
    annotations = VOC_path / 'Annotations'
    images = VOC_path / 'JPEGImages'

    random_annotation = random.choice([x for x in annotations.iterdir()])
    print("Showing {}".format(str(random_annotation)))
    annotation = xml_to_dict(random_annotation, image_folder_path=images)
    show_annotation(annotation)
    if return_annotation:
        return annotation


def box_size(bounding_box):
    xmin, ymin, xmax, ymax = bounding_box
    return (xmax - xmin) * (ymax - ymin)


def keep_largest_box(annotation):
    """
    Given an annotation, keep only the largest bounding box
    """
    return_annotation = copy.deepcopy(annotation)
    largest_item_idx = max(annotation['objects'],
                           key=(lambda key: box_size(annotation['objects'][key]['coordinates'])))

    largest_item = annotation['objects'][largest_item_idx]

    return_annotation['objects'] = {0: largest_item}
    return return_annotation