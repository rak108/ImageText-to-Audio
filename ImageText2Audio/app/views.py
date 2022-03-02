from flask import render_template, request, redirect, session
from app import app
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import cv2
import numpy as np

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



def getText(file):
    img = Image.open(file)
    # auto_result, alpha, beta = automatic_brightness_and_contrast(img)
    # print('alpha', alpha)
    # print('beta', beta)
    # cv2_imshow(auto_result)
    # img = auto_result
    # filtered = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 41)
    # kernel = np.ones((1, 1), np.uint8)
    # opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    # closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    # img = cv2.bitwise_or(img, closing)
    return list(pytesseract.image_to_string(img).split('\n'))

"""
    Views
"""

app.config["IMAGE_UPLOADS"] = "./uploads"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "HEIC"]

@app.route("/", methods=["GET"])
def index():
    return render_template("upload_image.html")

@app.route("/upload-image", methods=["POST"])
def upload_image():
    if request.files:
        image = request.files["image"]

        if image.filename == "":
            return redirect(request.url)

        if allowed_image(image.filename):
            filename = secure_filename(image.filename)
            session['ImageName'] = os.path.join(app.config["IMAGE_UPLOADS"], filename)
            image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
            return redirect("/result")

        else:
            return redirect(request.url)

    return redirect("/")

@app.route("/result")
def result():
    if os.path.isfile(session['ImageName']):
        return render_template("result.html", text=getText(session['ImageName']))
    return redirect('/upload-image')
    

"""
    Application wide 404 error handler
"""
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

