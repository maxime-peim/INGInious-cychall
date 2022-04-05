import os

from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.base import id_checker, load_json_or_yaml
from inginious.common import custom_yaml
from . import constants

class TemplateStructureException(Exception):
    """ Helper exception raised when a template does not have the right structure """
    pass

class TemplateIDExists(Exception):
    """ Helper exception raised when a template id already exists. """
    
    def __init__(self, templateid, path):
        self.message = f"{templateid} already in used in {path}."
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
        self._path = os.path.abspath(os.path.normpath(path))
        self._fs = LocalFSProvider(path)
        self._id = os.path.basename(self._path)
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

    @property
    def elements(self):
        return self._options.get("elements", [])

    @property
    def difficulties(self):
        return self._options.get("difficulties", ["Easy"])
    
    @property
    def next_step_switch(self):
        return self._options.get("next-step-switch", "custom")

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
    def validation_from_files(cls, templateid, files):
        """ Check whether template's files have the valid structure on upload. """

        if not id_checker(templateid):
            raise TemplateStructureException(f"Template id {templateid} is not valid.")
        
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
        self._path = os.path.abspath(os.path.normpath(path))
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

    def add_template_from_files(self, templateid, files):
        # Check if the template id is available in the folder
        if templateid in self._templates:
            raise TemplateIDExists(templateid, self._path)
        
        # Check if the files have the right structure
        # let the exception be propagated
        Template.validation_from_files(templateid, files)

        # if all is good, copy files
        template_fs = self._fs.from_subfolder(templateid)
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
        
        self.add_default_setup_file(template_fs)
        template = Template(template_fs.prefix)
        self._templates[template.id] = template
    
    def add_default_setup_file(self, template_fs):
        setup_path = os.path.join(template_fs.prefix, "setup")
        if not os.path.exists(setup_path):
            template_fs.put("setup", constants.DEFAULT_SETUP)

    def template_exists(self, templateid):
        return templateid in self._templates

    def delete_template(self, templateid):
        template = self.get_template(templateid)
        template.delete()
        del self._templates[templateid]

    def get_template(self, templateid):
        if templateid not in self._templates:
            raise FileNotFoundError(f"Template {templateid} not found in {self._path}.")
        return self._templates[templateid]

    def get_all_templates(self):
        return self._templates.values()


class TemplateManager:
    """ Singleton used to manage all templates from all courses and common ones. """

    __singleton = None

    def __new__(cls):
        if cls.__singleton is None:
            cls.__singleton = super().__new__(cls)
            cls.__singleton.__initialized = False
        return cls.__singleton

    def __init__(self):
        pass

    @classmethod
    def init_singleton(cls, course_factory, common_path=None):
        singleton = cls.__singleton

        if singleton.__initialized:
            return

        singleton.__initialized = True
        singleton._course_factory = course_factory
        singleton._template_folders = {}

        singleton.add_path_to_templates(common_path, courseid="$common")

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

    def get_template(self, courseid, templateid):
        try:
            template_folder = self.get_course_template_folder(courseid)
            return template_folder.get_template(templateid)
        except FileNotFoundError:
            template_folder = self._template_folders["$common"]
            return template_folder.get_template(templateid)

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

    def add_template_from_files(self, courseid, templateid, files):
        # we must not add template with id already in course or common folder
        # else there can be problem on editing a template since we don't know
        # if the template is public or course specific.
        course_template_folder = self.get_course_template_folder(courseid, ensure_exists=True)
        common_template_folder = self._template_folders["$common"]

        # Check if the template id is available in the folder
        if course_template_folder.template_exists(templateid):
            raise TemplateIDExists(templateid, course_template_folder.path)
        
        if common_template_folder.template_exists(templateid):
            raise TemplateIDExists(templateid, common_template_folder.path)

        course_template_folder.add_template_from_files(templateid, files)

    def get_template_filelist(self, courseid, templateid):
        """ Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
            It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
        """
        template = self.get_template(courseid, templateid)
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

class TemplateManagerHandler:
    
    _template_manager = None

    def __init_subclass__(cls):
        cls._template_manager = TemplateManager()
