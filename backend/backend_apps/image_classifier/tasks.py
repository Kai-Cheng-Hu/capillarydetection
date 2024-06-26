import json
import os
import timeit
from io import BytesIO

import cv2
import imutils
import numpy as np
import requests
from celery import shared_task
from django.core.files import File
from numpy import asarray
from PIL import Image, ImageEnhance
from skimage.exposure import histogram

from image_classifier.algorithm_v2 import classify_image_using_algorithm_v2
from . import models

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import tensorflow as tf
from tensorflow.python.ops.numpy_ops import np_config

np_config.enable_numpy_behavior()

# Start docker
# docker run -p 8501:8501 --name tfserving_classifier --mount type=bind,source=C:\Users\maged\Desktop\Projects\PyCharm_Projects\21_Django_ML\backend\algorithms\SSIM_Model\,target=/models/img_classifier -e MODEL_NAME=SSIM_Model -t tensorflow/serving
# https://neptune.ai/blog/how-to-serve-machine-learning-models-with-tensorflow-serving-and-docker

# model_test = tf.keras.models.load_model("algorithms/SSIM_Model/1")

# server URL
url = 'http://tensorflow-servings:8501/v1/models/model:predict'


def make_prediction_tensorflow(instances):
    data = json.dumps({"signature_name": "serving_default", "instances": instances.tolist()})
    headers = {"content-type": "application/json"}
    json_response = requests.post(url, data=data, headers=headers)
    predictions = json.loads(json_response.text)['predictions']
    return predictions


def make_prediction_ray(instances):
    resp = requests.get(
        "http://localhost:8000/mnist",
        json={"array": instances.tolist()})

    print(resp.json())
    return resp.json()


class ImageEnhancement(object):
    def __init__(self):
        pass

    def __call__(self, image):
        init_dtype = image.dtype

        if np.max(image) <= 1.0:
            print(f"My np.max is low")
            image = (image * 255.0).astype(np.uint8)
        enhanced_image = self.enhance_image(image)

        if init_dtype == np.uint8:
            enhanced_image = (enhanced_image * 255.0).astype(np.uint8)

        return enhanced_image

    def enhance_image(self, image):
        # Calculate intensity histogram
        hist, hist_centers = histogram(image)

        # Find min intensity
        percentage_to_drop = 0.01
        nr_of_pixels = image.shape[0] * image.shape[1]
        min_intensity = 0
        max_intensity = 255
        for i in range(1, len(hist)):  # Skip zero intensity pixels
            if hist[i] > nr_of_pixels * percentage_to_drop:
                min_intensity = hist_centers[i]
                break

        # Find end intensity
        for i in range(len(hist) - 1, 0, -1):
            if hist[i] > nr_of_pixels * percentage_to_drop:
                max_intensity = hist_centers[i]
                break

        image = image.astype(np.float32)
        image = np.clip(image, min_intensity, max_intensity)
        image = (image - min_intensity) / (max_intensity - min_intensity)

        return image


def enhance_image(img_orig):
    frame_en = Image.fromarray(img_orig)
    enh_col = ImageEnhance.Color(frame_en)
    color = 1.5

    image_en = enh_col.enhance(color)
    enh_con = ImageEnhance.Contrast(image_en)

    contrast = 1.5
    image_contrasted = enh_con.enhance(contrast)
    img_contrasted = np.array(image_contrasted)

    return img_contrasted


def extract_frame_from_video(video_dir, frame_number):
    print(f" Video Name: {video_path}")
    capture = cv2.VideoCapture(video_path)

    counter = 0
    while True:
        ret, frame = capture.read()

        if counter == frame_number:
            image = cv2.imwrite("frame.png", frame)
            break

        counter += 1

    return frame


def return_channel(frame_multi):
    b, g, r = cv2.split(frame_multi)
    # COLOR_RGB2BGR

    return g


def denoise_frame(noisy_frame):
    return cv2.fastNlMeansDenoising(noisy_frame, None, 11, 11, 21)


def segment_background(img_unseg, frame_to_blend_with):
    thresh1 = cv2.adaptiveThreshold(img_unseg, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY_INV, 199, 5)
    original_masked = cv2.bitwise_and(frame_to_blend_with, frame_to_blend_with, mask=thresh1)

    return original_masked


def remove_high_green_pixels(masked_image):
    masked_image_copy = masked_image.copy()

    green_value = masked_image_copy[:, :, 1]
    red_value = masked_image_copy[:, :, 0]
    q = green_value > red_value

    masked_image_copy[q] = [0, 0, 0]

    area = capillary_density(masked_image_copy)

    return masked_image_copy, area


def get_countours_apply_to_image(res_img, image_to_write_on, input_shape=(50, 50), accepted_accuracy=0.8):
    capillary_count = 0

    res_gray = cv2.cvtColor(res_img, cv2.COLOR_BGR2GRAY)
    cnts = cv2.findContours(res_gray.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    for i, c in enumerate(cnts):
        (x, y, w, h) = cv2.boundingRect(c)

        if cv2.contourArea(c) < 300 or cv2.contourArea(c) > 30000:
            continue

        startX = x - 20
        startY = y - 20
        endX = x + w + 20
        endY = y + h + 20

        if startX < 0:
            startX = 0

        if startY < 0:
            startY = 0

        if endX > 1920:
            endX = 1920

        if endY > 1080:
            endY = 1080

        # Make prediction using deep learning
        temp_image = cv2.resize(image_to_write_on[startY:endY, startX:endX], input_shape)

        reshaped_array = tf.expand_dims(temp_image, 0)

        # for performance comparison (Django / TFX restpoint / TFX gRC / Ray)
        TFX = True
        if TFX:
            prediction = make_prediction_tensorflow(reshaped_array)

            if prediction[0][0] < accepted_accuracy:
                capillary_count += 1
                # true_coords.append([startX, startY, endX, endY])
                cv2.rectangle(image_to_write_on, (x, y), (x + w, y + h), (0, 255, 0), 2)

            else:
                # false_coords.append([startX, startY, endX, endY])
                print(f"NOT capillary count is {capillary_count}")
                cv2.rectangle(image_to_write_on, (x, y), (x + w, y + h), (0, 0, 255), 2)

        use_ray = False
        if use_ray:
            prediction = make_prediction_ray(reshaped_array)

            if prediction[0][0] < accepted_accuracy:
                capillary_count += 1
                # true_coords.append([startX, startY, endX, endY])
                cv2.rectangle(image_to_write_on, (x, y), (x + w, y + h), (0, 255, 0), 2)

            else:
                # false_coords.append([startX, startY, endX, endY])
                cv2.rectangle(image_to_write_on, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return image_to_write_on, capillary_count


def capillary_density(image_to_calculate_density_from):
    temp_gray = cv2.cvtColor(image_to_calculate_density_from, cv2.COLOR_BGR2GRAY)
    height = temp_gray.shape[0]
    width = temp_gray.shape[1]
    density_count = cv2.countNonZero(temp_gray)

    area = density_count * 2.2 * 2.2 / (width * height)
    area = str(round(area, 2)) + " capillary/µm"

    return area


def classify_image(frame):
    img_temp = asarray(Image.open(frame))

    start_time = timeit.default_timer()

    image_enhancement = ImageEnhancement()
    org_enhanced = image_enhancement(img_temp)

    # load channel
    frame_ready = cv2.cvtColor(img_temp, cv2.COLOR_RGB2BGR)
    g = return_channel(frame_ready)

    # denoise frame
    denoised_img = denoise_frame(g)

    segmented_bg = segment_background(denoised_img, org_enhanced)

    segmented_image_clean, area_count = remove_high_green_pixels(segmented_bg)

    img, capillary_count = get_countours_apply_to_image(segmented_image_clean, org_enhanced)
    analyzed_im = Image.fromarray(img)
    segmented_im = Image.fromarray(segmented_bg)

    time_taken = str(round(timeit.default_timer() - start_time, 2)) + " seconds"

    return time_taken, analyzed_im, capillary_count, area_count, segmented_im

    # return time_taken, img, capillary_count, area_count, segmented_bg


@shared_task
def algorithm_image(serializer, image_name, test):
    if test:
        uploaded_pictures = "testSample.png"
        file_name = image_name

    else:
        uploaded_pictures = serializer
        file_name = image_name

    # time_taken, analyzed, number_of_capillaries, area_of_capillaries, segmented_image_clean = classify_image(
    #     uploaded_pictures)

    time_taken, analyzed, segmented, cap_dense, capillary_count = classify_image_using_algorithm_v2(uploaded_pictures)

    new_image_io = BytesIO()
    analyzed.save(new_image_io, format='PNG')
    analyzed_file_object = File(new_image_io, name=os.path.basename(file_name))

    new_image_io_segmented = BytesIO()
    segmented.save(new_image_io_segmented, format='PNG')
    segmented_file_object = File(new_image_io_segmented, name=os.path.basename(file_name))

    model_instance = models.Image.objects.create(
        picture=uploaded_pictures,
        time_to_classify=time_taken,
        number_of_cap=capillary_count,
        capillary_area=cap_dense,
        analyzed_picture=analyzed_file_object,
        segmented_image=segmented_file_object,
    )

    return {"picture": model_instance.picture.url,
            "time_to_classify": model_instance.time_to_classify,
            "number_of_capillaries": model_instance.number_of_cap,
            "capillary_area": model_instance.capillary_area,
            "analyzed_picture": model_instance.analyzed_picture.url,
            "segmented_image": model_instance.segmented_image.url,
            }


if __name__ == "__main__":
    pass
