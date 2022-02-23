from flask import render_template, request, redirect, session
from app import app
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image

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
    
def getText(file):
    return list(pytesseract.image_to_string( Image.open(file)).split('\n'))

"""
    Views
"""

app.config["IMAGE_UPLOADS"] = "./uploads"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():

    if request.method == "POST":

        if request.files:

            image = request.files["image"]

            if image.filename == "":
                print("No filename")
                return redirect(request.url)

            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                
                session['ImageName'] = os.path.join(app.config["IMAGE_UPLOADS"], filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

                print("Image saved")

                return redirect("/result")

            else:
                print("That file extension is not allowed")
                return redirect(request.url)

    return render_template("upload_image.html")

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

