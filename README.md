# Boun SWE 573
## This repository has been created by Zahra Atrvash for Bogaziçi university Software development practice.
###### It represents: 
- Raw content of finished and ongoing projects on [Project section](https://github.com/sahar-avsh/Zahra-Atrvash/projects).
- Content of research, discoveries and projects on [Wiki section](https://github.com/sahar-avsh/Zahra-Atrvash/wiki).
- List of barriers and milestones on [Milestone section](https://github.com/sahar-avsh/Zahra-Atrvash/milestones).
- List of solved and ongoing issues on [Issues section](https://github.com/sahar-avsh/Zahra-Atrvash/issues).
###### Mentioned sections get updated on regular basis

## How to run our code

1.  As it is not dockerized and deployed yet, in order to run the project, users shall pull the project from the repository

2. Then they shall create .env file under dj_bootcamp and put these commands into it:
3. 
(My Google Maps Key is AIzaSyDhGALDy3szFc4iKRYQ9Jl7zhKMnGpY78Y)

If you use your own Google Map Api key, Geocoding API, Maps Javascript API and Places API need to be connected.
​​GOOGLE_MAPS_API_KEY=your-google-maps-key

SECRET_KEY=django-insecure-dcl7ece))r^2w_cz01%%ot_@64lsp)*&tz!))s(md!*5@i1x

DATABASE_NAME=your-desire-data

DATABASE_USER=root

DATABASE_PASSWORD=37373737scR7

DATABASE_HOST=localhost

DATABASE_PORT=3306

3. For the third step they need to open the terminal and navigate to the project directory and create a virtual environment
### macOS
python3 -m venv .venv
source .venv/bin/activate
### Windows
py -3 -m venv .venv
.venv\scripts\activate

4. And after they shall run this command in the terminal

pip install -r requirements.txt

5. You should have GDAL library installed on your computer and specify the path to your GDAL library in settings.py file.
GDAL_LIBRARY_PATH = ‘path/to/gdal/on/your/computer’

6. Some dependencies we use have not been updated by the library developers and use the import command below
 “from django.utils.translation import ugettext_lazy as _”
In Django version > 2.0, this command is deprecated.
Thus, you should go to the source code of those libraries in the virtual environment folder and change the corresponding command to:
“from django.utils.translation import gettext_lazy as _”

7. Then again in the terminal run this commands:

Python manage.py makemigrations

Python manage.py migrate

Python manage.py runserver
