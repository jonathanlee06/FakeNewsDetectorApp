from app import app
from flaskext.mysql import MySQL

mysql = MySQL()

# Database Configuration
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'fakenewsapp_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)