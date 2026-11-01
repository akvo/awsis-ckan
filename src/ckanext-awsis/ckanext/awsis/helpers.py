"""Template helper functions for AWSIS theme."""

import logging
from ckan.plugins import toolkit

from ckanext.awsis.dataset_form import DEFAULT_LICENSE_ID, HIDDEN_FIELDS
from ckanext.awsis.vocabularies import TYPE_OF_RESOURCE, type_of_resource_list

log = logging.getLogger(__name__)


def get_stats():
    """Get statistics for the portal.

    Returns:
        dict: Statistics including dataset count, organization count,
              resource count, and group count.
    """
    try:
        # Get dataset count
        dataset_count = toolkit.get_action('package_search')(
            {}, {'rows': 0}
        )['count']

        # Get organization count
        org_list = toolkit.get_action('organization_list')({}, {})
        org_count = len(org_list)

        # Get group count
        group_list = toolkit.get_action('group_list')({}, {})
        group_count = len(group_list)

        # Estimate resource count (get from recent packages)
        resource_count = 0
        try:
            result = toolkit.get_action('package_search')(
                {}, {'rows': 100, 'include_private': False}
            )
            for pkg in result.get('results', []):
                resource_count += len(pkg.get('resources', []))
        except Exception:
            resource_count = 0

        return {
            'datasets': dataset_count,
            'organizations': org_count,
            'groups': group_count,
            'resources': resource_count,
        }
    except Exception as e:
        log.warning(f'Error getting stats: {e}')
        return {
            'datasets': 0,
            'organizations': 0,
            'groups': 0,
            'resources': 0,
        }


def get_featured_datasets(limit=6):
    """Get featured/recent datasets for the homepage carousel.

    Args:
        limit: Maximum number of datasets to return.

    Returns:
        list: List of dataset dictionaries.
    """
    try:
        result = toolkit.get_action('package_search')(
            {},
            {
                'rows': limit,
                'sort': 'metadata_modified desc',
                'include_private': False,
            }
        )
        return result.get('results', [])
    except Exception as e:
        log.warning(f'Error getting featured datasets: {e}')
        return []


def get_recent_datasets(limit=5):
    """Get most recently updated datasets.

    Args:
        limit: Maximum number of datasets to return.

    Returns:
        list: List of dataset dictionaries.
    """
    try:
        result = toolkit.get_action('package_search')(
            {},
            {
                'rows': limit,
                'sort': 'metadata_modified desc',
                'include_private': False,
            }
        )
        return result.get('results', [])
    except Exception as e:
        log.warning(f'Error getting recent datasets: {e}')
        return []


def get_thematic_areas():
    """Get thematic areas for the Sundarbans water security project.

    Returns:
        list: List of thematic area dictionaries with title, description,
              icon, and link.
    """
    return [
        {
            'title': 'Water Quality',
            'description': 'Monitor salinity levels, arsenic contamination, and other water quality parameters across the Sundarbans region.',
            'icon': 'water-quality',
            'link': '/dataset?tags=water-quality',
            'color': '#03AD8C',
        },
        {
            'title': 'Climate & Weather',
            'description': 'Track rainfall patterns, temperature changes, and extreme weather events affecting water availability.',
            'icon': 'climate',
            'link': '/dataset?tags=climate',
            'color': '#1E5F74',
        },
        {
            'title': 'Infrastructure',
            'description': 'Map water supply infrastructure, treatment facilities, and distribution networks.',
            'icon': 'infrastructure',
            'link': '/dataset?tags=infrastructure',
            'color': '#8B7355',
        },
    ]


# Card copy and Heroicons (outline) path for each Type of Resource option
_RESOURCE_TYPE_CARDS = {
    'Case study': {
        'description': 'Documented experiences and lessons learned from water security interventions on the ground.',
        'icon': 'M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18',
    },
    'Regional and Thematic Overview': {
        'description': 'Syntheses of the state of water security across regions and key themes.',
        'icon': 'M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418',
    },
    'Handbooks and manuals': {
        'description': 'Practical guidance and step-by-step references for practitioners.',
        'icon': 'M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25',
    },
    'Tools and frameworks': {
        'description': 'Methods, models and assessment frameworks to plan and evaluate water security work.',
        'icon': 'M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z',
    },
    'Policy briefs': {
        'description': 'Concise, evidence-based recommendations for decision makers.',
        'icon': 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    },
}


def get_resource_types():
    """Get Type of Resource cards for the homepage.

    Returns:
        list: One dictionary per vocabulary option, in vocabulary order,
              with title, description, icon (SVG path) and link.
    """
    cards = []
    for name in type_of_resource_list:
        card = _RESOURCE_TYPE_CARDS.get(name, {})
        cards.append({
            'title': name,
            'description': card.get('description', ''),
            'icon': card.get('icon'),
            'link': toolkit.url_for(
                'dataset.search', **{f'vocab_{TYPE_OF_RESOURCE}': name}
            ),
        })
    return cards


def hide_dataset_field(name):
    """Whether a dataset form field group is hidden.

    Args:
        name: Field group key in dataset_form.HIDDEN_FIELDS, e.g.
              'maintainer' or 'custom_fields'.

    Returns:
        bool: True when the field group should be hidden.
    """
    return HIDDEN_FIELDS.get(name, False)


def default_license_id():
    """License id preselected on the new dataset form."""
    return DEFAULT_LICENSE_ID
