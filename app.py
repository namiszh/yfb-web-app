# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


from flask import Flask
app = Flask(__name__)
# read configuration from file config.py
app.config.from_object('config')

from yahoo.oauth import YOAuth
from yahoo.yhandler import YHandler


# Initialize a Yahoo OAuth object
yOauth = YOAuth(app.config['CREDENTIALS_FILE'])
yHandler = YHandler(yOauth)

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
app.logger.debug('++++++++ '+ app.config['CHINESE_FONT_FILE'])
cnFontProp = font_manager.FontProperties(fname=app.config['CHINESE_FONT_FILE'])
# cnFontProp.set_family('SimHei')
# cnFontProp.set_size(8)

from flask_login import LoginManager

# db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

# run application
# if __name__ == "__main__": 
    # app.run(ssl_context=('./cert/cert.pem', './cert/key.pem'), debug=True)
    # app.run()


from routes import views, auth
from routes.views import polling_bp
from routes.after_response import AfterResponse

with app.app_context():
    app.register_blueprint(polling_bp, url_prefix='/')
    AfterResponse(app)
    