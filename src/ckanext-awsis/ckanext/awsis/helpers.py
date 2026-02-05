"""Template helper functions for AWSIS theme."""

import logging
from ckan.plugins import toolkit

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
