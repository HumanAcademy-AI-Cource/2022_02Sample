#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 必要なライブラリをインポート
import rospy
import cv2
import os
import subprocess
import shutil
import roslib.packages

import boto3
import wave
import random
import string
from cv_bridge import CvBridge
import numpy as np
from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from aws_demokit.srv import SceneRekognitionRequest, SceneRekognitionResponse, SceneRekognition


class SceneRekognitionNode(object):
    def __init__(self):
        rospy.Service('scene_rekognition', SceneRekognition, self.serviceCB)
        rospy.Subscriber("/usb_cam/image_raw", Image, self.imageCB)
        
        self.image = None

    def serviceCB(self, request):
        response = SceneRekognitionResponse()

        # カメラ画像保存
        pkg_path = roslib.packages.get_pkg_dir("aws_demokit")
        target_file = pkg_path + "/scripts/camera.jpg"
        cv2.imwrite(target_file, self.image)
        image = cv2.imread(target_file)

        # 顔検出
        detectface_data = self.detectFace(target_file)
        for d in detectface_data:
            x = int(d["BoundingBox"]["Left"] * image.shape[1])
            y = int(d["BoundingBox"]["Top"] * image.shape[0])
            w = int(d["BoundingBox"]["Width"] * image.shape[1])
            h = int(d["BoundingBox"]["Height"] * image.shape[0])
            image = cv2.rectangle(
                image, (x, y), (x + w, y + h), (255, 255, 255), 2)

        # シーン認識
        detect_data = self.detectLabels(target_file)
        for d in detect_data:
            for b in d["Instances"]:
                x = int(b["BoundingBox"]["Left"] * image.shape[1])
                y = int(b["BoundingBox"]["Top"] * image.shape[0])
                w = int(b["BoundingBox"]["Width"] * image.shape[1])
                h = int(b["BoundingBox"]["Height"] * image.shape[0])

                image = cv2.rectangle(
                    image, (x, y), (x + w, y + h), (0, 241, 255), 2)

                text_size = cv2.getTextSize(
                    d["Name"], cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
                image = cv2.rectangle(
                    image, (x, y - text_size[0][1] - 10), (x + text_size[0][0], y), (0, 241, 255), -1)
                image = cv2.putText(image, d["Name"], (x, y - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), thickness=2)

        # メッセージに変換
        response.detect_image = CompressedImage()
        response.detect_image.header.stamp = rospy.Time.now()
        response.detect_image.format = "jpeg"
        response.detect_image.data = np.array(
            cv2.imencode('.jpg', image)[1]).tostring()

        # 翻訳
        trans_text = ""
        for i in range(len(detect_data)):
            trans_text += detect_data[i]["Name"] + "\n"

        transrate_data = self.transrate(trans_text)
        sp_transrate_data = transrate_data.split("\n")[:-1]

        # 音声合成
        text = ""
        for i in range(len(sp_transrate_data)):
            text += sp_transrate_data[i]
            if i == 2:
                break
            else:
                text += ","
        text += "が見つかりました。"
        filename = self.generateName() + ".wav"
        speech_data = self.synthesizeSpeech(text)
        target_dir = pkg_path + "/scripts/audio"
        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir)
            os.mkdir(target_dir)
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        target_file = target_dir + "/" + filename
        wave_data = wave.open(target_file, 'wb')
        wave_data.setnchannels(1)
        wave_data.setsampwidth(2)
        wave_data.setframerate(16000)
        wave_data.writeframes(speech_data.read())

        for i in range(len(detect_data)):
            response.labels.append("{}({})".format(
                sp_transrate_data[i], detect_data[i]["Name"]))
            response.confidence.append(detect_data[i]["Confidence"])
            if i == 4:
                break

        response.audio_filename = filename
        return response

    def generateName(self):
        return "".join(
            [random.choice(string.digits + string.ascii_letters) for i in range(24)])

    def detectLabels(self, path):
        # AWSでシーン認識
        rekognition = boto3.client("rekognition")
        with open(path, 'rb') as f:
            return rekognition.detect_labels(
                Image={'Bytes': f.read()},
            )["Labels"]
        return []

    def detectFace(self, path):
        # AWSでシーン認識
        rekognition = boto3.client("rekognition")
        with open(path, 'rb') as f:
            return rekognition.detect_faces(
                Image={'Bytes': f.read()},
            )["FaceDetails"]
        return []

    def transrate(self, text):
        # AWSを使った翻訳の準備
        translate = boto3.client(service_name="translate")
        # 文章を翻訳
        return translate.translate_text(
            Text=text,
            SourceLanguageCode="en",
            TargetLanguageCode="ja"
        )["TranslatedText"]

    def synthesizeSpeech(self, text):
        # AWSでシーン認識
        polly = boto3.client(service_name="polly")
        return polly.synthesize_speech(
            Text=text,
            OutputFormat='pcm',
            VoiceId='Mizuki'
        )['AudioStream']

    def imageCB(self, msg):
        # rospy.loginfo("ReceiveImage")
        self.image = CvBridge().imgmsg_to_cv2(msg, "bgr8")

    def run(self):
        rate = rospy.Rate(1)
        while not rospy.is_shutdown():
            rate.sleep()
            # rospy.loginfo("Wait")


if __name__ == '__main__':
    # ノードを宣言
    rospy.init_node('scene_rekognition_node')
    SceneRekognitionNode().run()
