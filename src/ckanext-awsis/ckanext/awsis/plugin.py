import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.awsis import helpers


class AwsisPlugin(plugins.SingletonPlugin):
    """AWSIS Theme Plugin for CKAN."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'awsis')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'awsis_get_stats': helpers.get_stats,
            'awsis_get_featured_datasets': helpers.get_featured_datasets,
            'awsis_get_thematic_areas': helpers.get_thematic_areas,
            'awsis_get_recent_datasets': helpers.get_recent_datasets,
        }
