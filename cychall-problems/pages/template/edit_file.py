from flask import request

from .base_page import TemplateManagerPage

from ... import constants


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
											template_folder=constants.PATH_TO_TEMPLATES,
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