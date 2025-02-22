import tensorflow as tf
from tensorflow.keras import backend as K
K.set_learning_phase(0)
from absl import app, flags, logging
from absl.flags import FLAGS
from core.yolov4 import YOLO, decode, filter_boxes
import core.utils as utils
from core.config import cfg

flags.DEFINE_string('names', cfg.YOLO.CLASSES, 'path to weights file')
flags.DEFINE_string('weights', './data/yolov4.weights', 'path to weights file')
flags.DEFINE_string('output', './checkpoints/yolov4-416', 'path to output')
flags.DEFINE_boolean('tiny', False, 'is yolo-tiny or not')
flags.DEFINE_integer('input_size', 416, 'define input size of export model')
flags.DEFINE_float('score_thres', 0.2, 'define score threshold')
flags.DEFINE_string('framework', 'tf', 'define what framework do you want to convert (tf, trt, tflite)')
flags.DEFINE_string('model', 'yolov4', 'yolov3 or yolov4')

def save_tf():
  STRIDES, ANCHORS, NUM_CLASS, XYSCALE = utils.load_config(FLAGS)

  input_layer = tf.keras.layers.Input([FLAGS.input_size, FLAGS.input_size, 3], batch_size=1)
  feature_maps = YOLO(input_layer, NUM_CLASS, FLAGS.model, FLAGS.tiny)
  bbox_tensors = []
  prob_tensors = []
  print(feature_maps)
  if FLAGS.tiny:
    for i, fm in enumerate(feature_maps):
      if i == 0:
        output_tensors = decode(fm, FLAGS.input_size // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      else:
        output_tensors = decode(fm, FLAGS.input_size // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      bbox_tensors.append(output_tensors[0])
      prob_tensors.append(output_tensors[1])
  else:
    for i, fm in enumerate(feature_maps):
      if i == 0:
        output_tensors = decode(fm, FLAGS.input_size // 8, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      elif i == 1:
        output_tensors = decode(fm, FLAGS.input_size // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      else:
        output_tensors = decode(fm, FLAGS.input_size // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      bbox_tensors.append(output_tensors[0])
      prob_tensors.append(output_tensors[1])
  pred_bbox = tf.concat(bbox_tensors, axis=1, name="concat_bbox")
  pred_prob = tf.concat(prob_tensors, axis=1, name="concat_prob")
  print(f"framework: {FLAGS.framework}")
  if FLAGS.framework == 'tflite':
    pred = (pred_bbox, pred_prob)
  else:
    boxes, pred_conf = filter_boxes(pred_bbox, pred_prob, score_threshold=FLAGS.score_thres, input_shape=tf.constant([FLAGS.input_size, FLAGS.input_size]))
    pred = tf.concat([boxes, pred_conf], axis=-1, name="concat_pred",)
    # pred.type_spec.name = "abac"
    print(pred)
    print(pred.type_spec)
    print(dir(pred.type_spec))
  model = tf.keras.Model(inpu./t_layer, pred)
  # for l in model.layers:
    # l.trainable = False
    #print(dir(l.input))
    # if "set_shape" in dir(l.input) and l.input.shape[0] == None:
    #   l.input.set_shape((1, *l.input.shape[1:]))
    #print(l.input.shape)
    #exit(1)
  utils.load_weights(model, FLAGS.weights, FLAGS.model, FLAGS.tiny)
  model.summary()
  model.save(FLAGS.output)

def main(_argv):
  cfg.YOLO.CLASSES = FLAGS.names
  save_tf()

if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
