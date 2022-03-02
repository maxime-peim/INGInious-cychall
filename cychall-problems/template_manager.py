import os
import json
from re import template
from flask import request, redirect
from werkzeug.utils import secure_filename

from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.base import id_checker, load_json_or_yaml
from inginious.common import custom_yaml
from werkzeug.exceptions import NotFound

from . import utils

class TemplateStructureException(Exception):
	""" Helper exception raised when a template does not have the right structure """
	pass

class TemplateIDExists(Exception):
	""" Helper exception raised when a template id already exists. """
	
	def __init__(self, template_id, path):
		self.message = f"{template_id} already in used in {path}."
		super().__init__(self.message)


class Template:
	""" Class associated with templates.
	It checks a template structure from a path to a template folder
	and eases template files manipulation """

	def __init__(self, path):
		self._path = path
		self._fs = LocalFSProvider(path)
		self._id = os.path.basename(os.path.normpath(path))
		self._config = None

		self.validation()

	@property
	def id(self):
		return self._id

	@property
	def fs(self):
		return self._fs

	@property
	def path(self):
		return self._path

	@property
	def unique_id(self):
		return hash(self._path)

	@property
	def name(self):
		return self._config["name"]

	def get_option(self, option_name):
		options = self._config.get("options", {})
		option = options.get(option_name, {})
		
		option_type = option.get("type", None)
		option_values = option.get("values", None)

		return option_type, option_values

	def delete(self):
		self._fs.delete()

	def validation(self):
		if not self._fs.exists():
			raise TemplateStructureException(f"Path to template {self._path} does not exists.")

		if not id_checker(self._id):
			raise TemplateStructureException(f"Template id {self._id} from {self._path} is not valid.")

		configuration_path = os.path.join(self._path, "configuration.yaml")
		try:
			self._config = load_json_or_yaml(configuration_path)
		except Exception:
			raise TemplateStructureException(f"{configuration_path} not found.")

		if "name" not in self._config:
			raise TemplateStructureException(f"Template name not set in {configuration_path}.")

	@classmethod
	def validation_from_files(cls, template_id, files):
		if not id_checker(template_id):
			raise TemplateStructureException(f"Template id {template_id} is not valid.")
		
		configuration_correct = False
		for file in files:
			if os.path.basename(file.filename) == "configuration.yaml":
				content = custom_yaml.load(file.stream)
				# place the cursor to the beginning if stream
				# else we will save nothing in the file
				file.stream.seek(0)
				if "name" in content:
					configuration_correct = True
					break

		if not configuration_correct:
			raise TemplateStructureException(f"Configuration file not found or template name not set.")

class TemplateFolder:
	""" Class associated with folder containing templates.
	Eases template files manipulation and template access. """

	def __init__(self, path):
		self._path = path
		self._fs = LocalFSProvider(path)
		self._templates = {}

		if not self._fs.exists():
			raise ValueError(f"Path to templates folder {path} does not exists.")

		for template_folder_name in self._fs.list(folders=True, files=False):
			template_path = os.path.join(self._path, template_folder_name)
			template = Template(template_path)
			self._templates[template.id] = template

	def add_template_from_files(self, template_id, files):
		# Check if the template id is available in the folder
		if template_id in self._templates:
			raise TemplateIDExists(template_id, self._path)
		
		# Check if the files have the right structure
		# let the exception be propagated
		Template.validation_from_files(template_id, files)

		# if all is good, copy files
		template_fs = self._fs.from_subfolder(template_id)
		template_fs.ensure_exists()

		# TODO: there is surely a better way
		for file in files:
			file_folder = template_fs
			file_path = "/".join(file.filename.strip("/").split('/')[1:])
			dir_struct = os.path.dirname(file_path)
			filename = os.path.basename(file_path)
			
			if dir_struct != '':
				file_folder = file_folder.from_subfolder(dir_struct)
				file_folder.ensure_exists()
			
			file.save(os.path.join(file_folder.prefix, filename))

		template = Template(template_fs.prefix)
		self._templates[template.id] = template

	def delete_template(self, template_id):
		template = self.get_template(template_id)
		template.delete()
		del self._templates[template_id]

	def get_template(self, template_id):
		return self._templates.get(template_id, None)

	def get_all_templates(self):
		return self._templates.values()


class TemplateManager:
	""" Singleton used to manage all templates from all courses and common ones. """

	def __init__(self, course_factory, common_path=None):
		self._course_factory = course_factory
		self._template_folders = {}

		self.add_path_to_templates(common_path, courseid="$common")

	def add_path_to_templates(self, path, courseid):
		if os.path.exists(path):
			if not path.endswith("/"):
				path += "/"

			template_folder = TemplateFolder(path)
			self._template_folders[courseid] = template_folder

	def get_course_template_folder(self, courseid, ensure_exists=False):
		if courseid not in self._template_folders:
			course_fs = self._course_factory.get_course(courseid).get_fs()
			course_template_fs = course_fs.from_subfolder("templates")

			if not ensure_exists and not course_template_fs.exists():
				raise NotFound(f"Template folder for course {courseid} not found.")
			
			course_template_fs.ensure_exists()
			self.add_path_to_templates(course_template_fs.prefix, courseid)
		
		return self._template_folders[courseid]

	def get_template(self, courseid, template_id):
		try:
			template_folder = self.get_course_template_folder(courseid)
		except NotFound:
			template_folder = self._template_folders["$common"]
		return template_folder.get_template(template_id)

	def get_template_fs(self, courseid, template_id):
		return self.get_template(courseid, template_id).fs

	def get_public_templates(self):
		return self._template_folders["$common"].get_all_templates()

	def get_all_templates(self, courseid=None):
		common = self.get_public_templates()

		if courseid is None:
			return common, []

		try:
			course_template_folder = self.get_course_template_folder(courseid)
			course_specific = course_template_folder.get_all_templates()
		except NotFound:
			course_specific = []
		
		return common, course_specific

	def get_template_filelist(self, courseid, template_id):
		""" Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
			It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
		"""
		template_fs = self.get_template_fs(courseid, template_id)
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


class TemplateManagerPage(INGIniousAdminPage):
	""" Base class for all template management pages. """

	_template_manager_singleton = None

	@classmethod
	def set_template_manager(cls, template_manager):
		if cls._template_manager_singleton is not None:
			raise ValueError("Template manager singleton already set.")
		cls._template_manager_singleton = template_manager


class TemplatesList(TemplateManagerPage):

	def show_page(self, courseid, error=None):
		course = self.course_factory.get_course(courseid)
		public_templates, course_templates = self._template_manager_singleton.get_all_templates(courseid)

		return self.template_helper.render("template_manager.html", 
					template_folder=utils.PATH_TO_TEMPLATES, course=course,
					public_templates=public_templates,
					course_templates=course_templates, error=error)

	def GET_AUTH(self, courseid):
		self.get_course_and_check_rights(courseid, allow_all_staff=False)
		
		return self.show_page(courseid)
	
	def POST_AUTH(self, courseid):
		self.get_course_and_check_rights(courseid, allow_all_staff=False)	

		error = None
		if "upload" in request.form:
			files = request.files.getlist("file")
			if files:
				is_public = request.form.get("public", False)
				template_id = request.form.get("template_id", None)

				try:
					template_folder = self._template_manager_singleton.get_course_template_folder("$common" if is_public else courseid, ensure_exists=True)
					template_folder.add_template_from_files(template_id, files)
				except TemplateStructureException as e:
					error = str(e)
			else:
				error = "No template selected."
		
		elif "delete" in request.form:
			template_id = request.form.get("template_id", None)
			try:
				template_folder = self._template_manager_singleton.get_course_template_folder(courseid)
				template_folder.delete_template(template_id)
			except Exception as e:
				error = str(e)
		
		return self.show_page(courseid, error)

		
class TemplateEdit(TemplateManagerPage):
	
	def GET_AUTH(self, courseid, template_id):
		self.get_course_and_check_rights(courseid, allow_all_staff=False)
		course = self.course_factory.get_course(courseid)
		template_fs = self.get_template_fs(courseid, template_id)
		
		if template_fs is None:
			return redirect(f'/admin/{courseid}/edit/templates')
			
		path = template_fs.prefix
		
		return self.template_helper.render("template_edit.html", 
		template_folder=utils.PATH_TO_TEMPLATES, 
		course=course, 
		template_id=template_id, 
		file_list=self.get_template_filelist(courseid, template_id))
	
	def POST_AUTH(self, courseid, template_id):
		return json.dumps({'status': 'ok'})

class TemplateFiles(TemplateManagerPage):
	
	def GET_AUTH(self, courseid, template_id):  # pylint: disable=arguments-differ
		""" Edit a task """
		if not id_checker(template_id):
			raise NotFound(description=_("Invalid task id"))
		
		self.get_course_and_check_rights(courseid, allow_all_staff=False)

		user_input = request.args
		if user_input.get("action") == "delete" and user_input.get('path') is not None:
			return self.action_delete(courseid, template_id, user_input.get('path'))
		elif user_input.get("action") == "rename" and user_input.get('path') is not None and user_input.get('new_path') is not None:
			return self.action_rename(courseid, template_id, user_input.get('path'), user_input.get('new_path'))
		elif user_input.get("action") == "create" and user_input.get('path') is not None:
			return self.action_create(courseid, template_id, user_input.get('path'))
		elif user_input.get("action") == "edit" and user_input.get('path') is not None:
			return self.action_edit(courseid, template_id, user_input.get('path'))
	
	def POST_AUTH(self, courseid, template_id):
		""" Upload or modify a file """
		if not id_checker(template_id):
			raise NotFound(description=_("Invalid task id"))

		self.get_course_and_check_rights(courseid, allow_all_staff=False)

		user_input = request.form.copy()
		user_input["file"] = request.files.get("file")

		if user_input.get("action") == "upload" and user_input.get('path') is not None and user_input.get('file') is not None:
			return self.action_upload(courseid, template_id, user_input.get('path'), user_input.get('file'))
		elif user_input.get("action") == "edit_save" and user_input.get('path') is not None and user_input.get('content') is not None:
			return self.action_edit_save(courseid, template_id, user_input.get('path'), user_input.get('content'))
	
	def verify_path(self, courseid, template_id, path):
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
	
	def show_tab_file(self, courseid, template_id, error=None):
		""" Return the file tab """
		return self.template_helper.render("files.html",
											template_folder=utils.PATH_TO_TEMPLATES,
											course=self.course_factory.get_course(courseid), 
											template_id=template_id, 
											file_list=self.get_template_filelist(courseid, template_id), 
											error=error)

	def action_edit(self, courseid, template_id, path):
		""" Edit a file """
		template_fs = self.get_template_fs(courseid, template_id)
		wanted_path = self.verify_path(courseid, template_id, path)
		if template_fs is None or wanted_path is None:
			return "Internal error"
		try:
			content = template_fs.get(wanted_path).decode("utf-8")
			return json.dumps({"content": content})
		except:
			return json.dumps({"error": "not-readable"})
	
	def action_edit_save(self,courseid, template_id, path, content):
		""" Save an edited file """
		template_fs = self.get_template_fs(courseid, template_id)
		wanted_path = self.verify_path(courseid, template_id, path)
		if template_fs is None or wanted_path is None:
			return json.dumps({"error": True})
		try:
			template_fs.put(wanted_path, content.encode("utf-8"))
			return json.dumps({"ok": True})
		except:
			return json.dumps({"error": True})
	
	def action_delete(self, courseid, template_id, path):
		""" Delete a file or a directory """
		# normalize
		path = path.strip()
		if not path.startswith("/"):
			path = "/" + path
		
		template_fs = self.get_template_fs(courseid, template_id)
		if template_fs is None:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		wanted_path = self.verify_path(courseid, template_id, path)
		if wanted_path is None:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		# special case: cannot delete current directory of the task
		if "/" == wanted_path:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		try:
			template_fs.delete(wanted_path)
			return self.show_tab_file(courseid, template_id)
		except:
			return self.show_tab_file(courseid, template_id, _("An error occurred while deleting the files"))
	
	def action_rename(self, courseid, template_id, path, new_path):
		""" Delete a file or a directory """
		# normalize
		path = path.strip()
		new_path = new_path.strip()
		if not path.startswith("/"):
			path = "/" + path
		if not new_path.startswith("/"):
			new_path = "/" + new_path
		
		template_fs = self.get_template_fs(courseid, template_id)
		if template_fs is None:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		old_path = self.verify_path(courseid, template_id, path)
		if old_path is None:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		wanted_path = self.verify_path(courseid, template_id, new_path)
		if wanted_path is None:
			return self.show_tab_file(courseid, template_id, _("Invalid new path"))
		
		if template_fs.exists(wanted_path):
			return self.show_tab_file(courseid, template_id, _("Invalid new path"))
		
		try:
			template_fs.move(old_path, wanted_path)
			return self.show_tab_file(courseid, template_id)
		except:
			return self.show_tab_file(courseid, template_id, _("An error occurred while moving the files"))
		
	def action_create(self, courseid, template_id, path):
		""" Create a file or a directory """
		# the path is given by the user. Let's normalize it
		path = path.strip()
		if not path.startswith("/"):
			path = "/" + path

		want_directory = path.endswith("/")
		
		template_fs = self.get_template_fs(courseid, template_id)
		if template_fs is None:
			return self.show_tab_file(courseid, template_id, _("Internal error"))

		wanted_path = self.verify_path(courseid, template_id, path)
		if wanted_path is None:
			return self.show_tab_file(courseid, template_id, _("Invalid new path"))
		
		if template_fs.exists(wanted_path):
			return self.show_tab_file(courseid, template_id, _("Invalid new path"))

		if want_directory:
			template_fs.from_subfolder(wanted_path).ensure_exists()
		else:
			template_fs.put(wanted_path, b"")
		return self.show_tab_file(courseid, template_id)

def templates_menu(course):
	return ('templates', 'Challenge templates')

