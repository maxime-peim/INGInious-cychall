from flask import request

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

from ...template_manager import TemplateManagerHandler, TemplateIDExists, TemplateStructureException
from ... import constants


class TemplatesList(INGIniousAdminPage, TemplateManagerHandler):

    def show_page(self, course, error=None):
        public_templates, course_templates = self._template_manager.get_all_templates(course.get_id())

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
                templateid = request.form.get("templateid", None)

                try:
                    effective_courseid = "$common" if is_public else courseid
                    self._template_manager.add_template_from_files(effective_courseid, templateid, files)
                except (TemplateStructureException, TemplateIDExists) as e:
                    error = str(e)
            else:
                error = "No template selected."
        
        elif "delete" in request.form:
            templateid = request.form.get("templateid", None)
            try:
                template_folder = self._template_manager.get_course_template_folder(courseid)
                template_folder.delete_template(templateid)
            except Exception as e:
                error = str(e)
        
        return self.show_page(course, error)
