"""
https://github.com/mnoukhov/tf-estimator-mnist

accuracy = 0.9889, global_step = 2700, loss = 0.034140434
- 25.3106 sec. 

MULTI-GPU:
NUM_GPUS = 2
accuracy = 0.9899, global_step = 3000, loss = 0.035298657
- 31.8924 sec.

NUM_GPUS = 3
accuracy = 0.9908, global_step = 3200, loss = 0.03562759
- 25.2826 sec.

"""

import tensorflow as tf
import mnist_dataset as dataset
from utils.timer import timer

flags = tf.app.flags
flags.DEFINE_string('data_dir', '/tmp/mnist/data',
					'Directory where mnist data will be downloaded'
					' if the data is not already there')
flags.DEFINE_string('model_dir', '/tmp/mnist/model',
					'Directory where all models are saved')
flags.DEFINE_integer('batch_size', 100, 'Batch size.')
flags.DEFINE_integer('num_epochs', 1,
					 'Num of batches to train (epochs).')
flags.DEFINE_float('learning_rate', 0.001, 'Learning Rate')
FLAGS = flags.FLAGS


def train_data():
	data = dataset.train(FLAGS.data_dir)
	data = data.cache()
	data = data.batch(FLAGS.batch_size)
	return data

def eval_data():
	data = dataset.test(FLAGS.data_dir)
	data = data.cache()
	data = data.batch(FLAGS.batch_size)
	return data

def lenet():
	layers = tf.keras.layers

	model = tf.keras.Sequential([
		layers.Reshape(
			target_shape=[28, 28, 1],
			input_shape=(28 * 28,)),

		layers.Conv2D(
			filters=20,
			kernel_size=[5,5],
			padding='same',
			activation=tf.nn.relu),

		layers.MaxPooling2D(
			pool_size=[2,2]),

		layers.Conv2D(
			filters=50,
			kernel_size=[5,5],
			padding='same',
			activation=tf.nn.relu),

		layers.MaxPool2D(
			pool_size=[2,2]),

		layers.Flatten(),

		layers.Dense(
			units=500,
			activation=tf.nn.relu),

		layers.Dense(
			units=10),
	])

	return model


def model_function(features, labels, mode):
	# get the model
	model = lenet()

	if mode == tf.estimator.ModeKeys.TRAIN:
		# pass the input through the model
		logits = model(features)

		# get the cross-entropy loss and name it
		loss = tf.losses.sparse_softmax_cross_entropy(
			labels=labels,
			logits=logits)
		tf.identity(loss, 'train_loss')

		# record the accuracy and name it
		accuracy = tf.metrics.accuracy(
			labels=labels,
			predictions=tf.argmax(logits, axis=1))
		tf.identity(accuracy[1], name='train_accuracy')

		# use Adam to optimize
		optimizer = tf.train.AdamOptimizer(learning_rate=FLAGS.learning_rate)
		tf.identity(FLAGS.learning_rate, name='learning_rate')

		# create an estimator spec to optimize the loss
		estimator_spec = tf.estimator.EstimatorSpec(
			mode=tf.estimator.ModeKeys.TRAIN,
			loss=loss,
			train_op=optimizer.minimize(loss, tf.train.get_or_create_global_step()))

	elif mode == tf.estimator.ModeKeys.EVAL:
		# pass the input through the model
		logits = model(features, training=False)

		# get the cross-entropy loss
		loss = tf.losses.sparse_softmax_cross_entropy(
			labels=labels,
			logits=logits)

		# use the accuracy as a metric
		accuracy = tf.metrics.accuracy(
			labels=labels,
			predictions=tf.argmax(logits, axis=1))

		# create an estimator spec with the loss and accuracy
		estimator_spec = tf.estimator.EstimatorSpec(
			mode=tf.estimator.ModeKeys.EVAL,
			loss=loss,
			eval_metric_ops={
				'accuracy': accuracy
			})

	return estimator_spec


def main(_):
	hooks = [
		tf.train.LoggingTensorHook(
			['train_accuracy', 'train_loss'],
			every_n_iter=10)
	]

	NUM_GPUS = 3
	strategy = tf.contrib.distribute.MirroredStrategy(num_gpus=NUM_GPUS)
	config = tf.estimator.RunConfig(train_distribute=strategy)
	#estimator = tf.keras.estimator.model_to_estimator(model, config=config)

	mnist_classifier = tf.estimator.Estimator(
		model_fn=model_function,
		model_dir=FLAGS.model_dir,
		config=config
		)

	timer('TRAIN_AND_EVALUATE')

	for _ in range(FLAGS.num_epochs):
		mnist_classifier.train(
			input_fn=train_data,
			hooks=hooks,
		)
		mnist_classifier.evaluate(
			input_fn=eval_data)

	timer()

if __name__ == '__main__':
	tf.logging.set_verbosity(tf.logging.INFO)
	tf.app.run()
