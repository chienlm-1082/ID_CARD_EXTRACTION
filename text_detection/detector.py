import tensorflow as tf
import numpy as np
import cv2
from tensorflow.python.ops.gen_math_ops import imag
from .object_detection.utils import label_map_util
from .object_detection.utils import config_util
from .object_detection.builders import model_builder


class Detector(object):
    def __init__(self, path_config, path_ckpt, path_to_labels):
        self.path_config = path_config
        self.path_ckpt = path_ckpt
        self.label_path = path_to_labels

        self.category_index = label_map_util.create_category_index_from_labelmap(path_to_labels, use_display_name=True)
        self.detection_model = self.load_model()
        self.detection_scores = None
        self.detection_boxes = None
        self.detection_classes = None
        self.id_boxes = []

    def detect_fn(self, image):
        """Detect objects in image."""
        image, shapes = self.detection_model.preprocess(image)
        prediction_dict = self.detection_model.predict(image, shapes)
        detections = self.detection_model.postprocess(prediction_dict, shapes)
        return detections

    def load_model(self):
        # Load pipeline config and build a detection model
        configs = config_util.get_configs_from_pipeline_file(self.path_config)
        model_config = configs['model']
        detection_model = model_builder.build(model_config=model_config, is_training=False)

        # Restore checkpoint
        ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
        ckpt.restore(self.path_ckpt).expect_partial()

        return detection_model

    def predict(self, image):
        image = np.asarray(image)

        input_tensor = tf.convert_to_tensor(np.expand_dims(image, 0), dtype=tf.float32)
        detections = self.detect_fn(input_tensor)

        # All outputs are batches tensors.
        # Convert to numpy arrays, and take index [0] to remove the batch dimension.
        # We're only interested in the first num_detections.
        num_detections = int(detections.pop('num_detections'))
        # num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy() for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        self.detection_scores = detections['detection_scores']
        self.detection_classes = detections['detection_classes']
        self.detection_boxes = detections['detection_boxes']

        # draw bounding boxes and labels
        image = self.draw(image)
        return image

    def draw(self, img):
        height, width, _ = img.shape
        for i, score in enumerate(self.detection_scores):
            if score < 0.5:
                continue

            self.detection_classes[i] += 1
            # if background, ignore
            if self.detection_classes[i] == 0:
                continue

            label = str(self.category_index[self.detection_classes[i]]['name'])
            print(label)
            ymin, xmin, ymax, xmax = self.detection_boxes[i]
            real_xmin, real_ymin, real_xmax, real_ymax = int(xmin * width), int(ymin * height), int(xmax * width), int(
                ymax * height)
            if label == 'id':
                id_regions = img[real_ymin:real_ymax, real_xmin:real_xmax]
                self.id_boxes.append(id_regions)
            cv2.rectangle(img, (real_xmin, real_ymin), (real_xmax, real_ymax), (0, 255, 0), 2)
            cv2.putText(img, label, (real_xmin, real_ymin), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255), fontScale=0.5)

        return img
    def get_bb_detection(self, img):
        id_boxes = []
        height, width, _ = img.shape
        for i, score in enumerate(self.detection_scores):
            if score < 0.5:
                continue

            self.detection_classes[i] += 1
            # if background, ignore
            if self.detection_classes[i] == 0:
                continue

            label = str(self.category_index[self.detection_classes[i]]['name'])
            print(label)
            if label == 'id':
                ymin, xmin, ymax, xmax = self.detection_boxes[i]
                real_xmin, real_ymin, real_xmax, real_ymax = int(xmin * width), int(ymin * height), int(xmax * width), int(
                    ymax * height)
                id_regions = img[real_xmin:real_xmax, real_ymin:real_ymax]
                id_boxes.append(id_regions)
        if id_boxes is not None:
            return id_boxes


print("testtt")