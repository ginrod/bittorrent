import flask
import wtforms


app = flask.Flask(__name__)


#Bootstrap fix code
def bootstrap_find_resource(filename, cdn, use_minified=None, local=True):
    return flask.url_for('static', filename=filename)

def is_hidden_field_filter(field):
    return isinstance(field, wtforms.HiddenField)

app.jinja_env.globals['bootstrap_find_resource'] = bootstrap_find_resource
app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter


#Endpoints
@app.route('/')
def index():
    return flask.render_template("index.html")

if __name__ == "__main__":
    app.run("0.0.0.0", 8000)
