from flask import request

from .base_page import TemplateManagerPage 

from ... import constants


class TemplatesList(TemplateManagerPage):

	def show_page(self, course, error=None):
		public_templates, course_templates = self._template_manager_singleton.get_all_templates(course.get_id())

		return self.template_helper.render("template_manager.html", 
					template_folder=constants.PATH_TO_TEMPLATES, course=course,
					public_templates=public_templates,
					course_templates=course_templates, error=error)

	def GET_AUTH(self, courseid):
		course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
		
		return self.show_page(course)
	
	def POST_AUTH(self, courseid):
		course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)	

		error = None
		if "upload" in request.form:
			files = request.files.getlist("file")
			if files:
				is_public = request.form.get("public", False)
				template_id = request.form.get("template_id", None)

				try:
					effective_courseid = "$common" if is_public else courseid
					self._template_manager_singleton.add_template_from_files(effective_courseid, template_id, files)
				except (TemplateStructureException, TemplateIDExists) as e:
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
		
		return self.show_page(course, error)
