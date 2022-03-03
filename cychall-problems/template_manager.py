import os

from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.base import id_checker, load_json_or_yaml
from inginious.common import custom_yaml


class TemplateStructureException(Exception):
	""" Helper exception raised when a template does not have the right structure """
	pass

class TemplateIDExists(Exception):
	""" Helper exception raised when a template id already exists. """
	
	def __init__(self, template_id, path):
		self.message = f"{template_id} already in used in {path}."
		super().__init__(self.message)


class Template:
	""" 
		Class associated with templates management.
		It checks a template structure from a path to a template folder
		and eases template files manipulation.
	"""

	def __init__(self, path):
		"""
			From a path to a folder containing template's files,
			we check from the template's structure.
		"""
		self._path = path
		self._fs = LocalFSProvider(path)
		self._id = os.path.basename(os.path.normpath(path))
		self._name = None
		self._options = None

		self.validation()

	@property
	def id(self):
		""" Returns the template id, unique in the parent folder. """
		return self._id

	@property
	def fs(self):
		""" Returns the file system pointing to the template files. """
		return self._fs

	@property
	def path(self):
		""" Returns the path to the templates files. """
		return self._path

	@property
	def unique_id(self):
		""" Returns a unique id over all templates. """
		return hash(self._path)

	@property
	def name(self):
		""" Returns the template name from the template configuration. """
		return self._name

	def get_option(self, option_name):
		""" Returns option type and possible values from configuration. """
		option = self._options.get(option_name, {})
		
		option_type = option.get("type", None)
		option_values = option.get("values", None)

		return option_type, option_values

	def delete(self):
		""" Delete the template's files """
		self._fs.delete()

	def validation(self):
		""" 
			Check for template structure.
			Raise a TemplateStructureException if not valid.
		"""

		# if the path to the files does not exists, stop
		if not self._fs.exists():
			raise TemplateStructureException(f"Path to template {self._path} does not exists.")

		# the template id need to be valid
		if not id_checker(self._id):
			raise TemplateStructureException(f"Template id {self._id} from {self._path} is not valid.")

		configuration_path = os.path.join(self._path, "configuration.yaml")
		try:
			# a configuration file is mandatory in the folder
			config = load_json_or_yaml(configuration_path)
			# load the options
			self._options = config.get("options", {})
			# and the mandatory template name
			self._name = config.get("name", None)
		except Exception:
			raise TemplateStructureException(f"{configuration_path} not found.")

		# if the name is not set, raise an exception
		if self._name is None:
			raise TemplateStructureException(f"Template name not set in {configuration_path}.")
	

	@classmethod
	def validation_from_files(cls, template_id, files):
		""" Check whether template's files have the valid structure on upload. """

		if not id_checker(template_id):
			raise TemplateStructureException(f"Template id {template_id} is not valid.")
		
		configuration_correct = False
		for file in files:
			if os.path.basename(file.filename) == "configuration.yaml":
				content = custom_yaml.load(file.stream)
				# place the cursor to the beginning of stream
				# else we will save nothing in the file
				file.stream.seek(0)
				if "name" in content:
					configuration_correct = True
					break

		if not configuration_correct:
			raise TemplateStructureException(f"Configuration file not found or template name not set.")

class TemplatesFolder:
	"""
		Class associated with folder containing several templates.
		Eases template files manipulation and template access.
	"""

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

	@property
	def path(self):
		return self._path

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

	def template_exists(self, template_id):
		return template_id in self._templates

	def delete_template(self, template_id):
		template = self.get_template(template_id)
		template.delete()
		del self._templates[template_id]

	def get_template(self, template_id):
		if template_id not in self._templates:
			raise FileNotFoundError(f"Template {template_id} not found in {self._path}.")
		return self._templates[template_id]

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

			template_folder = TemplatesFolder(path)
			self._template_folders[courseid] = template_folder

	def get_course_template_folder(self, courseid, ensure_exists=False):
		if courseid not in self._template_folders:
			course_fs = self._course_factory.get_course(courseid).get_fs()
			course_template_fs = course_fs.from_subfolder("templates")

			if not ensure_exists and not course_template_fs.exists():
				raise FileNotFoundError(f"Template folder for course {courseid} not found.")
			
			course_template_fs.ensure_exists()
			self.add_path_to_templates(course_template_fs.prefix, courseid)
		
		return self._template_folders[courseid]

	def get_template(self, courseid, template_id):
		template = None

		try:
			template_folder = self.get_course_template_folder(courseid)
			template = template_folder.get_template(template_id)
		except FileNotFoundError:
			template_folder = self._template_folders["$common"]
			template = template_folder.get_template(template_id)
		
		return template

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
		except FileNotFoundError:
			course_specific = []
		
		return common, course_specific

	def add_template_from_files(self, courseid, template_id, files):
		# we must not add template with id already in course or common folder
		# else there can be problem on editing a template since we don't know
		# if the template is public or course specific.
		course_template_folder = self.get_course_template_folder(courseid, ensure_exists=True)
		common_template_folder = self._template_folders["$common"]

		# Check if the template id is available in the folder
		if course_template_folder.template_exists(template_id):
			raise TemplateIDExists(template_id, course_template_folder.path)
		
		if common_template_folder.template_exists(template_id):
			raise TemplateIDExists(template_id, common_template_folder.path)

		course_template_folder.add_template_from_files(template_id, files)

	def get_template_filelist(self, courseid, template_id):
		""" Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
			It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
		"""
		template = self.get_template(courseid, template_id)
		if template is None:
			return []

		template_fs = template.fs

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

