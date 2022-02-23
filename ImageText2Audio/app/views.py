from flask import render_template, request, redirect, session
from app import app
import os
from werkzeug.utils import secure_filename

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
    return ["The path of the righteous man is beset on all sides","By the inequities of the selfish and the tyranny of evil men","Blessed is he who, in the name of charity and good will","Shepherds the weak through the valley of darkness"," \
            For he is truly his brother's keeper and the finder of lost children","And I will strike down upon thee","With great vengeance and furious anger","Those who attempt to poison and destroy my brothers","And you will know my name is the Lord","When I lay my vengeance upon thee"]

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
    return render_template("result.html", text=getText(session['ImageName']))
    

"""
    Application wide 404 error handler
"""
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

