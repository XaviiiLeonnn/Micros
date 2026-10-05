import tensorflow as tf
(xt, yt), (xv, yv) = tf.keras.datasets.mnist.load_data()
xt = xt[..., None]/255.0; xv = xv[..., None]/255.0
m = tf.keras.Sequential([
    tf.keras.layers.Input((28,28,1)),
    tf.keras.layers.Conv2D(32,3,activation='relu'), tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(64,3,activation='relu'), tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(), tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')])
m.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
m.fit(xt, yt, epochs=8, validation_data=(xv, yv))
m.save("modelo_digitos.h5")