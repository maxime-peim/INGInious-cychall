from flask import redirect

from .base_page import TemplateManagerPage 

from ... import constants


class TemplateEdit(TemplateManagerPage):
	
	def GET_AUTH(self, courseid, template_id):
		course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
		template = self._template_manager_singleton.get_template(courseid, template_id)
		
		if template is None:
			return redirect(f'/admin/{courseid}/templates')
		
		return self.template_helper.render("template_edit.html",
					template_folder=constants.PATH_TO_TEMPLATES, 
					course=course, 
					template_id=template_id,
					file_list=self._template_manager_singleton.get_template_filelist(courseid, template_id))
	
	def POST_AUTH(self, courseid, template_id):
		return json.dumps({'status': 'ok'})