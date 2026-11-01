import logging
from collections import OrderedDict

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.awsis import helpers, validators
from ckanext.awsis.vocabularies import (
    TYPE_OF_RESOURCE,
    create_vocabularies,
    type_of_resource_list,
)

log = logging.getLogger(__name__)

YEAR_OF_PUBLICATION = 'year_of_publication'


class AwsisPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    """AWSIS Theme Plugin for CKAN."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'awsis')

    # IConfigurable
    def configure(self, config_):
        # The DB may not be initialised yet (e.g. during `ckan db init`)
        try:
            create_vocabularies()
        except Exception as e:
            log.warning(f'Could not create AWSIS vocabularies: {e}')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'awsis_get_stats': helpers.get_stats,
            'awsis_get_featured_datasets': helpers.get_featured_datasets,
            'awsis_get_thematic_areas': helpers.get_thematic_areas,
            'awsis_get_recent_datasets': helpers.get_recent_datasets,
            'awsis_get_resource_types': helpers.get_resource_types,
            'awsis_hide_dataset_field': helpers.hide_dataset_field,
            'awsis_default_license_id': helpers.default_license_id,
            'awsis_year_of_publication_options': (
                helpers.year_of_publication_options
            ),
            'awsis_current_year': helpers.current_year,
            'awsis_type_of_resource_options': lambda: type_of_resource_list,
        }

    # IFacets
    def _add_facets(self, facets_dict):
        ordered = OrderedDict()
        ordered[f'vocab_{TYPE_OF_RESOURCE}'] = toolkit._('Type of Resource')
        ordered[YEAR_OF_PUBLICATION] = toolkit._('Year of Publication')
        ordered.update(facets_dict)
        return ordered

    def dataset_facets(self, facets_dict, package_type):
        return self._add_facets(facets_dict)

    def organization_facets(
        self, facets_dict, organization_type, package_type
    ):
        return self._add_facets(facets_dict)

    def group_facets(self, facets_dict, group_type, package_type):
        return self._add_facets(facets_dict)

    # IValidators
    def get_validators(self):
        return {
            'awsis_year_of_publication': validators.year_of_publication,
        }

    # IPackageController
    def before_dataset_index(self, pkg_dict):
        # Extras are indexed as tokenized text; copy the year into a plain
        # string field (Solr's "*" dynamic field) so it facets cleanly
        year = pkg_dict.get(f'extras_{YEAR_OF_PUBLICATION}')
        if year:
            pkg_dict[YEAR_OF_PUBLICATION] = year
        return pkg_dict

    # IDatasetForm
    def is_fallback(self):
        return True

    def package_types(self):
        return ['dataset']

    def _modify_package_schema(self, schema):
        schema.update(
            {
                TYPE_OF_RESOURCE: [
                    toolkit.get_validator('not_empty'),
                    toolkit.get_converter('convert_to_tags')(TYPE_OF_RESOURCE),
                ],
                YEAR_OF_PUBLICATION: [
                    # ignore_empty (not ignore_missing): "Not specified"
                    # clears the year
                    toolkit.get_validator('ignore_empty'),
                    toolkit.get_validator('awsis_year_of_publication'),
                    toolkit.get_converter('convert_to_extras'),
                ],
            }
        )
        return schema

    def create_package_schema(self):
        schema = super(AwsisPlugin, self).create_package_schema()
        return self._modify_package_schema(schema)

    def update_package_schema(self):
        schema = super(AwsisPlugin, self).update_package_schema()
        return self._modify_package_schema(schema)

    def show_package_schema(self):
        schema = super(AwsisPlugin, self).show_package_schema()
        # Keep vocabulary tags out of the free-text tag list
        schema['tags']['__extras'].append(
            toolkit.get_converter('free_tags_only')
        )
        schema.update(
            {
                TYPE_OF_RESOURCE: [
                    toolkit.get_converter('convert_from_tags')(
                        TYPE_OF_RESOURCE
                    ),
                    toolkit.get_validator('ignore_missing'),
                ],
                YEAR_OF_PUBLICATION: [
                    toolkit.get_converter('convert_from_extras'),
                    toolkit.get_validator('ignore_missing'),
                ],
            }
        )
        return schema
