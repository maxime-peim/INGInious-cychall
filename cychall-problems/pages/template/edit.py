import json

from flask import redirect

from .base_page import TemplateManagerPage 

from ... import constants


class TemplateEdit(TemplateManagerPage):
	
	def GET_AUTH(self, courseid, templateid):
		course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

		try:
			template = self._template_manager_singleton.get_template(courseid, templateid)
		except FileNotFoundError as e:
			return redirect(f'/admin/{courseid}/templates')
		
		return self.template_helper.render("template_edit.html",
					template_folder=constants.PATH_TO_TEMPLATES, 
					course=course, 
					templateid=templateid,
					file_list=self._template_manager_singleton.get_template_filelist(courseid, templateid))
	
	def POST_AUTH(self, courseid, templateid):
		return json.dumps({'status': 'ok'})