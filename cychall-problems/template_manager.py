import os
import json
from flask import request
from werkzeug.utils import secure_filename

from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.base import id_checker
from abc import ABC

from . import utils

class TemplateManager(INGIniousAdminPage):

	path_to_exercise_templates = ""
	
	@classmethod
	def add_path_to_exercise_templates(cls, path):
		if os.path.exists(path):
			if not path.endswith("/"):
				path += "/"
			cls.path_to_exercise_templates = path
	
	def get_template_fs(self, courseid, templateid):
		template_fs = self.course_factory.get_course(courseid).get_fs().from_subfolder("templates/"+templateid)
		# verify that the dir exists
		if not template_fs.exists():
			template_fs = LocalFSProvider(self.path_to_exercise_templates + templateid)
			if not template_fs.exists():
				return None
		return template_fs
		

	def get_template_filelist(self, courseid, templateid):
		""" Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
			It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
		"""
		template_fs = self.get_template_fs(courseid, templateid)
		if template_fs is None:
			return []

		tmp_out = {}
		entries = template_fs.list(True, True, True)
		for entry in entries:

			data = entry.split("/")
			is_directory = False
			if data[-1] == "":
				is_directory = True
				data = data[0:len(data)-1]
			cur_pos = 0
			tree_pos = tmp_out
			while cur_pos != len(data):
				if data[cur_pos] not in tree_pos:
					tree_pos[data[cur_pos]] = {} if is_directory or cur_pos != len(data) - 1 else None
				tree_pos = tree_pos[data[cur_pos]]
				cur_pos += 1

		def recur_print(current, level, current_name):
			iteritems = sorted(current.items())
			# First, the files
			recur_print.flattened += [(level, False, f, current_name+"/"+f) for f, t in iteritems if t is None]
			# Then, the dirs
			for name, sub in iteritems:
				if sub is not None:
					recur_print.flattened.append((level, True, name, current_name+"/"+name+"/"))
					recur_print(sub, level + 1, current_name + "/" + name)
		recur_print.flattened = []
		recur_print(tmp_out, 0, '')
		return recur_print.flattened
	

class TemplatesList(TemplateManager):
	
	def __init__(self):
		super().__init__()
	
	def save_files(self, files, template_folder):
		for file in files:
			file_folder = template_folder
			file_path = "/".join(file.filename.strip("/").split('/')[1:])
			dir_struct = os.path.dirname(file_path)
			filename = os.path.basename(file_path)
			
			if dir_struct != '':
				file_folder = file_folder.from_subfolder(dir_struct)
				file_folder.ensure_exists()
			
			file.save(os.path.join(file_folder.prefix, filename))
	
	def get_output_dir(self, courseid, template_id, is_public):
		
		
		output_dir = self.course_factory.get_course_fs(courseid).from_subfolder("templates") # Default output to course templates
		
		if is_public:
			output_dir = LocalFSProvider(TemplateManager.path_to_exercise_templates)
		
		output_dir.ensure_exists() # Create templates folder
		
		template_folder = output_dir.from_subfolder(template_id)
		
		if template_folder.exists():
			return None
		
		template_folder.ensure_exists() # Create folder for template
		return template_folder
	
	def get_all_templates(self, course):
		course_templates_path = course.get_fs().from_subfolder("templates").prefix
		templates =  [[], []]
		for public_template in utils.get_dirs(self.path_to_exercise_templates):
			templates[0].append((os.path.join(TemplateManager.path_to_exercise_templates), public_template))
		
		for course_template in utils.get_dirs(course_templates_path):
			templates[1].append((os.path.join(course_templates_path), course_template))
		
		return templates

	def GET_AUTH(self, courseid):
		self.get_course_and_check_rights(courseid, allow_all_staff=False)

		return self.show_page(courseid)
	
	def show_page(self, courseid, error=None):
		course = self.course_factory.get_course(courseid)
		templates = self.get_all_templates(course)
		return self.template_helper.render("template_manager.html", template_folder=utils.PATH_TO_TEMPLATES, course=course, public_templates=templates[0], course_templates=templates[1], error=error)
	
	def upload_template(self, courseid, templateid, files, is_public):
		course = self.course_factory.get_course(courseid)
		template_folder = self.get_output_dir(courseid, templateid, is_public)
		self.save_files(files, template_folder)
		
		templates = self.get_all_templates(course)
		
		return self.show_page(courseid)
	
	def delete_template(self, courseid, templateid):
		template_fs = self.get_template_fs(courseid, templateid)
		if template_fs is not None:
			template_fs.delete()
	
	def POST_AUTH(self, courseid):
		self.get_course_and_check_rights(courseid, allow_all_staff=False)	
		
		if "upload" in request.form:
			files = request.files.getlist("file")
			is_public = request.form.get("public", False)
			templateid = request.form.get("template_id", None)
			
			if templateid is None or id_checker(templateid):
				return self.show_page(courseid, _("Invalid template id"))
			return self.upload_template(courseid, templateid, files, is_public)
		
		elif "delete" in request.form:
			templateid = request.form.get("template_id", None)
			if templateid is None or id_checker(templateid):
				return self.show_page(courseid, _("Invalid template id"))
			self.delete_template(courseid, templateid)
		
		return self.show_page(courseid)

		
class TemplateEdit(TemplateManager):

	def __init__(self):
		super().__init__()
	
	def GET_AUTH(self, courseid, templateid):
		if not id_checker(templateid):
			raise NotFound(description=_("Invalid task id"))
		self.get_course_and_check_rights(courseid, allow_all_staff=False)
		course = self.course_factory.get_course(courseid)
		template_fs = self.get_template_fs(courseid, templateid)
		
		if template_fs is None:
			return redirect(f'/admin/{courseid}/edit/templates')
			
		path = template_fs.prefix
		
		return self.template_helper.render("template_edit.html", 
		template_folder=utils.PATH_TO_TEMPLATES, 
		course=course, 
		templateid=templateid, 
		file_list=self.get_template_filelist(courseid, templateid))
	
	def POST_AUTH(self, courseid, templateid):
		return json.dumps({'status': 'ok'})

class TemplateFiles(TemplateManager):
	
	def __init__(self):
		super().__init__()
	
	def GET_AUTH(self, courseid, templateid):  # pylint: disable=arguments-differ
		""" Edit a task """
		if not id_checker(templateid):
			raise NotFound(description=_("Invalid task id"))
		
		self.get_course_and_check_rights(courseid, allow_all_staff=False)

		user_input = request.args
		if user_input.get("action") == "delete" and user_input.get('path') is not None:
			return self.action_delete(courseid, templateid, user_input.get('path'))
		elif user_input.get("action") == "rename" and user_input.get('path') is not None and user_input.get('new_path') is not None:
			return self.action_rename(courseid, templateid, user_input.get('path'), user_input.get('new_path'))
		elif user_input.get("action") == "create" and user_input.get('path') is not None:
			return self.action_create(courseid, templateid, user_input.get('path'))
		elif user_input.get("action") == "edit" and user_input.get('path') is not None:
			return self.action_edit(courseid, templateid, user_input.get('path'))
	
	def POST_AUTH(self, courseid, templateid):
		""" Upload or modify a file """
		if not id_checker(templateid):
			raise NotFound(description=_("Invalid task id"))

		self.get_course_and_check_rights(courseid, allow_all_staff=False)

		user_input = request.form.copy()
		user_input["file"] = request.files.get("file")

		if user_input.get("action") == "upload" and user_input.get('path') is not None and user_input.get('file') is not None:
			return self.action_upload(courseid, templateid, user_input.get('path'), user_input.get('file'))
		elif user_input.get("action") == "edit_save" and user_input.get('path') is not None and user_input.get('content') is not None:
			return self.action_edit_save(courseid, templateid, user_input.get('path'), user_input.get('content'))
	
	def verify_path(self, courseid, templateid, path):
		""" Return the real wanted path (relative to the INGInious root) or None if the path is not valid/allowed """
		
		# all path given to this part of the application must start with a "/", let's remove it
		if not path.startswith("/"):
			return None
		path = path[1:len(path)]
		
		if ".." in path:
			return None
		
		# do not allow hidden dir/files
		if path != ".":
			for i in path.split(os.path.sep):
				if i.startswith("."):
					return None
		return path
	
	def show_tab_file(self, courseid, templateid, error=None):
		""" Return the file tab """
		return self.template_helper.render("files.html",
											template_folder=utils.PATH_TO_TEMPLATES,
											course=self.course_factory.get_course(courseid), 
											templateid=templateid, 
											file_list=self.get_template_filelist(courseid, templateid), 
											error=error)

	def action_edit(self, courseid, templateid, path):
		""" Edit a file """
		template_fs = self.get_template_fs(courseid, templateid)
		wanted_path = self.verify_path(courseid, templateid, path)
		if template_fs is None or wanted_path is None:
			return json.dumps({"error": "internal-error"})"
		try:
			content = template_fs.get(wanted_path).decode("utf-8")
			return json.dumps({"content": content})
		except:
			return json.dumps({"error": "not-readable"})
	
	def action_edit_save(self,courseid, templateid, path, content):
		""" Save an edited file """
		template_fs = self.get_template_fs(courseid, templateid)
		wanted_path = self.verify_path(courseid, templateid, path)
		if template_fs is None or wanted_path is None:
			return json.dumps({"error": True})
		try:
			template_fs.put(wanted_path, content.encode("utf-8"))
			return json.dumps({"ok": True})
		except:
			return json.dumps({"error": True})
	
	def action_delete(self, courseid, templateid, path):
		""" Delete a file or a directory """
		# normalize
		path = path.strip()
		if not path.startswith("/"):
			path = "/" + path
		
		template_fs = self.get_template_fs(courseid, templateid)
		if template_fs is None:
			return self.show_tab_file(courseid, templateid, _("Internal error"))

		wanted_path = self.verify_path(courseid, templateid, path)
		if wanted_path is None:
			return self.show_tab_file(courseid, templateid, _("Internal error"))

		# special case: cannot delete current directory of the task
		if "/" == wanted_path:
			return self.show_tab_file(courseid, templateid, _("Internal error"))

		try:
			template_fs.delete(wanted_path)
			return self.show_tab_file(courseid, templateid)
		except:
			return self.show_tab_file(courseid, templateid, _("An error occurred while deleting the files"))
	
	def action_rename(self, courseid, templateid, path, new_path):
		""" Delete a file or a directory """
		# normalize
		path = path.strip()
		new_path = new_path.strip()
		if not path.startswith("/"):
			path = "/" + path
		if not new_path.startswith("/"):
			new_path = "/" + new_path
		
		template_fs = self.get_template_fs(courseid, templateid)
		if template_fs is None:
			return self.show_tab_file(courseid, templateid, _("Internal error"))

		old_path = self.verify_path(courseid, templateid, path)
		if old_path is None:
			return self.show_tab_file(courseid, templateid, _("Internal error"))

		wanted_path = self.verify_path(courseid, templateid, new_path)
		if wanted_path is None:
			return self.show_tab_file(courseid, templateid, _("Invalid new path"))
		
		if template_fs.exists(wanted_path):
			return self.show_tab_file(courseid, templateid, _("Invalid new path"))
		
		try:
			template_fs.move(old_path, wanted_path)
			return self.show_tab_file(courseid, templateid)
		except:
			return self.show_tab_file(courseid, templateid, _("An error occurred while moving the files"))
		
	def action_create(self, courseid, templateid, path):
		""" Create a file or a directory """
		# the path is given by the user. Let's normalize it
		path = path.strip()
		if not path.startswith("/"):
			path = "/" + path

		want_directory = path.endswith("/")
		
		template_fs = self.get_template_fs(courseid, templateid)
		if template_fs is None:
			return self.show_tab_file(courseid, taskid, _("Internal error"))

		wanted_path = self.verify_path(courseid, templateid, path)
		if wanted_path is None:
			return self.show_tab_file(courseid, taskid, _("Invalid new path"))
		
		if template_fs.exists(wanted_path):
			return self.show_tab_file(courseid, taskid, _("Invalid new path"))

		if want_directory:
			template_fs.from_subfolder(wanted_path).ensure_exists()
		else:
			template_fs.put(wanted_path, b"")
		return self.show_tab_file(courseid, templateid)

def templates_menu(course):
	return ('templates', 'Challenge templates')

