import os
import pathlib
from time import sleep
from threading import Thread

import docker
from colored import fg, bg, attr
from progress.spinner import Spinner

from duckiter.config import get_config
from duckiter.validation import pre_validation, docker_engine_status_checker, check_dockerfile
from duckiter.utility import (
	get_django_project_name, 
	create_docker_configuration_file, 
	create_dockerfile, 
	random_string, 
)

class Duckiter:
	def __init__(self):
		self.__project_path = os.getcwd()
		self.__MODULE_PATH = str(pathlib.Path(__file__).resolve().parent)
		self.__docker_client = None
		self.__project_name = ''
		self.__config = {}
		self.__project_name = get_django_project_name(project_path=self.__project_path)

	def initialize(self):
		pre_validation(project_path=self.__project_path)
		print("%s[ INITIALIZING ]%s" % (fg(2), attr(0)))

		print(" [ 3/6 ] getting project name ......%s[passed] %s" % (fg(2), attr(0)))

		self.__config = get_config()
		print(" [ 4/6 ] getting configuration ......%s[passed] %s" % (fg(2), attr(0)))

		create_docker_configuration_file(config=self.__config, project_name=self.__project_name,
										 project_path=self.__project_path)
		print(" [ 5/6 ] creating configuration file ......%s[passed] %s" % (fg(2), attr(0)))

		create_dockerfile(project_path=self.__project_path)
		print(" [ 6/6 ] creating Dockerfile ......%s[passed] %s" % (fg(2), attr(0)))
		print(
			"%s%s[ NOTE ]%s if there is gunicorn or daphne in your requirements.txt, Duckiter run your project with them"
			", else your project will be run with runserver." % (fg(2), bg(15), attr(0)))

		print(
			"%s%s[ NOTE ]%s if you didn't provide --build, you can edit Dockerfile or config.cfg and then run --build ." % (
				fg(2), bg(15), attr(0)))

	def build(self):
		self.__project_path = os.getcwd()

		docker_engine_status_checker()
		check_dockerfile(project_path=self.__project_path)

		print("%s[ BUILDING IMAGE ]%s" % (fg(2), attr(0)))
		print("it is going to take a while, please be patient...")

		self.__image_name = self.__project_name + "-" + random_string()
		self.__state = True

		create_image_thread = Thread(target=self.__build)
		create_image_thread.start()

		spinner = Spinner('BUILDING .....')

		while self.__state:
			sleep(0.1)
			spinner.next()

		print("\n")
		print(" [ 3/3 ] creating image ......%s[passed] %s" % (fg(2), attr(0)))
		print("%s%s[ NOTE ]%s you can run your image :" % (fg(2), bg(15), attr(0)))
		print(f'docker run -d -p 8000:8000 {self.__image_name}')
		print("you can hit '127.0.0.1:8000' in your browser.")

	def __build(self):
		client = docker.from_env()
		client.images.build(path=self.__project_path,tag=self.__image_name, rm=True, forcerm=True)
		self.__state = False
