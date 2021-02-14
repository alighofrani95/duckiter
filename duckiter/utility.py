import os
import configparser
import string
import random


def get_django_project_name(project_path) -> str:
	"""
		get project name

	:param project_path: path of project
	"""
	# list of all files and dirs in root
	project_dirs = {}
	for r, d, f in os.walk(project_path):
		for file in f:
			project_dirs[file] = os.path.join(r, file)

	# get the path of settings.py file
	project_main_dir = str(project_dirs['settings.py'])

	return project_main_dir.split('/')[-2]


def get_project_server(project_path, project_name) -> str:
	"""
		get project server ( runserver , gunicorn , daphne ,..... )
		it looks through requirements.txt file

	:param project_path: path of project
	:param project_name: name of django project
	"""

	project_dirs = {}
	for r, d, f in os.walk(project_path):
		for file in f:
			project_dirs[file] = os.path.join(r, file)

	req_file_path = str(project_dirs['requirements.txt'])

	is_gunicorn = False
	is_daphne = False

	with open(req_file_path, 'r') as file:
		for line in file:
			if 'gunicorn' in line:
				is_gunicorn = True
			if 'daphne' in line:
				is_daphne = True

	if is_gunicorn:
		return f'CMD ["gunicorn", "--bind 0.0.0.0:8000", "{project_name}.wsgi"]'
	elif is_daphne:

		return f'CMD ["daphne","-b 0.0.0.0", "-p 8060", "--access-log", "- --proxy-headers", "{project_name}.asgi:application"]'
	else:
		return 'CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]'


def create_docker_configuration_file(config, project_name, project_path) -> None:
	"""
		create config.cfg file that Dockerfile read settings from this
	:param project_path: path of project
	:param config: configuration that user entered
	:param project_name: name of django project
	"""
	project_server = get_project_server(project_path=project_path, project_name=project_name)
	config = f"""
[project_info]
project_name = {project_name}
python_version= {config['python_version']}
is_migration= {config['is_migration']}

[project_server]
project_server = {project_server}
	"""
	with open(project_path + '/config.cfg', 'w+') as file:
		file.write(config)


def create_dockerfile(project_path) -> None:
	"""
		create dockerfile from config.cfg
	:param project_path: path of project
	"""
	config = configparser.RawConfigParser()
	config.read(f'{project_path}/config.cfg')

	project_info = dict(config.items('project_info'))
	project_server = dict(config.items('project_server'))
	is_migration = 'CMD ["python3","manage.py","migrate"]' if project_info['is_migration'] == 'True' else "\n"
	dockerfile = f"""FROM python:{project_info['python_version']}-alpine
	
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY . /app

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

{is_migration}

{project_server['project_server']}
"""
	with open(project_path + '/Dockerfile', 'w+') as file:
		file.write(dockerfile)


def random_string() -> str:
	"""
		create random string with 5 character
	"""
	letter = string.ascii_lowercase
	random_string = ''.join(random.choice(letter) for i in range(5))
	return random_string