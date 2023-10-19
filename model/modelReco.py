from tensorflow.keras.models import load_model
import cv2
import numpy as np

def state(img):

    model = load_model('/Users/athena/Documents/ecole/vintedLikeComputingVision/model/rnn/my_Fmodel.h5')


    imga = cv2.imread(img)
    image_resized = cv2.resize(imga, (150, 150))
    image_normalized = image_resized / 255.0
    image_batch = np.expand_dims(image_normalized, axis=0)
    predictions = model.predict(image_batch)
    predicted_class = np.argmax(predictions[0])

    print("Classe prédite:", predicted_class)

    classes = ['bon etat', 'satisfaisant', 'très bon etat']

    # Vous pourriez aussi utiliser un tableau pour rendre cela plus propre
    pred = classes[predicted_class]
    return pred