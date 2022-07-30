from datetime import datetime

from flask import Flask, render_template
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from blueprints.helper.common import render_tag, render_entry, db
from blueprints.entry import entry_blueprint
from blueprints.model import model_blueprint
from blueprints.auth import auth_blueprint


app = Flask(__name__)
app.register_blueprint(model_blueprint)
app.register_blueprint(entry_blueprint)
app.register_blueprint(auth_blueprint)
app.secret_key = 'something unique and secret'
CORS(app)
CSRFProtect(app)


@app.context_processor
def inject_default_render_context():
    model_names = db().get_all_model_names()
    return {'model_names': model_names, 'now': datetime.utcnow(), 'render_tag': render_tag, 'render_entry': render_entry}


# add a route for the root URL
@app.route('/')
def index():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)