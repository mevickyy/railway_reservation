Please Follow the Steps
-----------------------------
1. Please make clone the project from the github and here the URL
  https://github.com/mevickyy/railway_reservation
2. Now make a virtual environment for that project to activate and Please find the requirements to install the dependencies(File location: /reservation/requirements.txt)
3. Please Find the Sql folder and import into your local db (File location: /reservation/sql/railway_reservation.sql)
4. In settings page change Database configuration as you made in local
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.mysql',
        'NAME': 'railway_reservation',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
}
5. Run a project in default port 8000(Example:http://127.0.0.1:8000). 

6. If you want to get API URL's. Please find the API documentation

7. And If you want to test the project with UI run directly to the html file (File Location:/reservation/html/index.html). Please find the HTML folder into the project folder.

Note: Dont run the project in different PORT Number. Because Ajax request call made in 8000 Port
