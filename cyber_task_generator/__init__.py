import json
import os
import flask
from jinja2 import Environment, FileSystemLoader

_BASE_RENDERER_PATH = 'frontend/plugins/cyber_task_generator'

_PROBLEM_TEMPLATE_PATH = '' # SET PATH TO TASK TEMPLATE FOLDER


from inginious.frontend.pages.utils import INGIniousPage
from inginious.common.exceptions import InvalidNameException, TaskAlreadyExistsException

def get_available_templates():
	dirs = next(os.walk(_PROBLEM_TEMPLATE_PATH))[1]
	return dirs
	
def check_if_template_exists(template_list, available_templates):
	return list(set(template_list) - set(available_templates)) == []

def menu(course):
	""""
	Callback function: add link to page in course admin menu
	"""
	return ('task_generator', 'Task generator')

def default_run_file_content():
	# Temporary function
	return '#!/bin/bash\n# Configuration has to be done directly onto the student container\nssh_student --user step1 --script-as-root --setup-script "generate-steps"\ncheck-flag --student-flag-path /task/student/answer --correct-flag-path /task/student/end/flag'

class TaskGenerator(INGIniousPage):
    """ A simple task generation page """
    
    def get_default_task_descriptor(self, task_name):
    	"""Get default task.yaml content for cybersecurity task"""
    	return {
    	"name": task_name, 
    	"accessible": False, 
    	"author": '', 
    	"categories": [], 
    	"contact_url": '', 
    	"context": '', 
    	"environment_id": 'cychall-binary', 
    	"environment_parameters":
	    	{"limits": 
	    		{
	    		"time": '3600', 
	    		"hard_time": '', 
	    		"memory": '100'
	    		}, 
	    	"network_grading": 'on', 
	    	"ssh_allowed": 'on', 
	    	"run_cmd": ''}, 
    	"environment_type": "kata", 
    	"evaluate": 'best', 
    	"file": '', 
    	"groups": '', 
    	"input_random": '0', 
    	"network_grading": False, 
    	"problems": {}, 
    	"stored_submissions": 0, 
    	"submission_limit": 
    		{"amount": -1, 
    		"period": -1}, 
    	"weight": 1.0}
    
    def add_next_step(self, step_number, template_name, scripts_dir_fs, jinja_env, last_step=False):
    	current_user = f'step{step_number}'
    	next_user = f'step{step_number+1}' if not last_step else 'end'
    
    	step_dir_fs = scripts_dir_fs.from_subfolder(current_user)
    	step_dir_fs.ensure_exists() # Create step dir
    	
    	template_path = _PROBLEM_TEMPLATE_PATH + "/" + template_name
    	
    	step_dir_fs.copy_to(template_path) # Copy template files to step dir
    	
    	if step_dir_fs.exists("post"): # Set file owner(s) in post script
    		post_script_template = jinja_env.get_template(f'{current_user}/post')
    		post_script_parsed = post_script_template.render(current_user=current_user, next_user=next_user)
    		
    		step_dir_fs.put("post", post_script_parsed)
    	

    def GET(self, courseid):
        """ GET request """
        course = self.course_factory.get_course(courseid)
        dirs = get_available_templates()
        return self.template_helper.render("problem_generator.html", template_folder=_BASE_RENDERER_PATH, course=course, problem_templates=dirs)
        
    def POST(self, courseid):
    	# TODO: cleanup files on error
    	course = self.course_factory.get_course(courseid)
    	dirs = get_available_templates()
    	
    	new_data = flask.request.form
    	
    	task_name = new_data["task-name"]
    	template_list = new_data["problems"].split(',')
    	
    	if not check_if_template_exists(template_list, dirs):
    		return "Error: chosen template does not exist" # TODO: redirect to generator with error message
    	
    	task_factory = self.course_factory.get_task_factory()
    	try: # Create task
    		task_factory.create_task(course, task_name,  self.get_default_task_descriptor(task_name))
    	except (InvalidNameException, TaskAlreadyExistsException) as e: # TODO: add error message
    		return self.template_helper.render("problem_generator.html", template_folder=_BASE_RENDERER_PATH, course=course, problem_templates=dirs)
    	
    	task_dir_fs = task_factory.get_task_fs(courseid, task_name)
    	
    	student_dir_fs = task_dir_fs.from_subfolder("student")
    	student_dir_fs.ensure_exists() # Create student dir
    	
    	scripts_dir_fs = student_dir_fs.from_subfolder("scripts")
    	scripts_dir_fs.ensure_exists() # Create scripts dir
    	
    	jinja_env = Environment(loader=FileSystemLoader(scripts_dir_fs.prefix))
    	
    	for i in range(len(template_list)): # Create steps dir and move files
    		self.add_next_step(i+1, template_list[i], scripts_dir_fs, jinja_env, i==len(template_list)-1)
    	
    	task_dir_fs.put("run", default_run_file_content())
    	
    	return flask.redirect(f'/admin/{courseid}/tasks')


def init(plugin_manager, course_factory, client, config):
	plugin_manager.add_page('/admin/<courseid>/task_generator', TaskGenerator.as_view('taskgeneratorpage'))
	plugin_manager.add_hook('course_admin_menu', menu)
