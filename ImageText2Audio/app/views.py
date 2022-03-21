from flask import render_template, request, redirect, session
from app import app
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import cv2
import numpy as np
import time
import azure.cognitiveservices.speech as speechsdk
from flask import send_from_directory

# import nltk


def allowed_image(filename):

    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False
    
def automatic_brightness_and_contrast(image, clip_hist_percent=1):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate grayscale histogram
    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_size = len(hist)
    
    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index -1] + float(hist[index]))
    
    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum/100.0)
    clip_hist_percent /= 2.0
    
    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1
    
    # Locate right cut
    maximum_gray = hist_size -1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1
    
    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha
    
    '''
    # Calculate new histogram with desired range and show histogram 
    new_hist = cv2.calcHist([gray],[0],None,[256],[minimum_gray,maximum_gray])
    plt.plot(hist)
    plt.plot(new_hist)
    plt.xlim([0,256])
    plt.show()
    '''

    auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    auto_result = cv2.cvtColor(auto_result, cv2.COLOR_BGR2GRAY)
    return (auto_result, alpha, beta)


# words = set(nltk.corpus.words.words())

def convertToAudio(text):
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get("SPEECH_KEY"), region=os.environ.get("REGION_LOCATION"))
    speech_config.speech_synthesis_language = "en-US"
    speech_config.speech_synthesis_voice_name ="en-US-ChristopherNeural"
    outputFilePath = f'./audio/text_{int(time.time())}.wav'
    audio_config = speechsdk.audio.AudioOutputConfig(filename=outputFilePath)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text(text)

    time.sleep(2)

    return outputFilePath

def getText(file):
    img = cv2.imread(file)
    auto_result, alpha, beta = automatic_brightness_and_contrast(img)
    print('alpha', alpha)
    print('beta', beta)
    # cv2_imshow(auto_result)
    img = auto_result
    filtered = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 41)
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    img = cv2.bitwise_or(img, closing)
    text = pytesseract.image_to_string(img)
    # return list(" ".join(w for w in nltk.wordpunct_tokenize(text) \
    #      if w.lower() in words or not w.isalpha()).split('\n'))
    return list(text.split('\n'))

"""
    Views
"""

app.config["IMAGE_UPLOADS"] = "./uploads"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG"]

@app.route("/", methods=["GET"])
def index():
    return render_template("upload_image.html")

@app.route("/upload-image", methods=["POST"])
def upload_image():
    if request.files:
        images = request.files.getlist("image")
        for image in images:
            if image.filename == "":
                return redirect(request.url)

            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                ImageName = os.path.join(app.config["IMAGE_UPLOADS"], filename)
                session['ImageFiles'].append(ImageName)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

            else:
                return redirect(request.url)
        
        return redirect("/result")

    return redirect("/")

@app.route("/result")
def result():
    textCombined = ""
    for ImageName in session['ImageFiles']:
        if os.path.isfile(ImageName):
            textList = getText(ImageName)
            textCombined += textList
    if textCombined:
        return render_template("result.html", text=textCombined, audioFilePath=convertToAudio("\n".join(textCombined)))
    return redirect('/upload-image')
    
@app.route('/audio/<path:filename>')
def download_file(filename):
    return send_from_directory(f'/home/gaurang/projects/ImageText-to-Audio/ImageText2Audio/audio', filename)

"""
    Application wide 404 error handler
"""
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

