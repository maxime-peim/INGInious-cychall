from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class TemplateManagerPage(INGIniousAdminPage):
	""" Base class for all template management pages. """

	_template_manager_singleton = None

	@classmethod
	def set_template_manager(cls, template_manager):
		if cls._template_manager_singleton is not None:
			raise ValueError("Template manager singleton already set.")
		cls._template_manager_singleton = template_manager