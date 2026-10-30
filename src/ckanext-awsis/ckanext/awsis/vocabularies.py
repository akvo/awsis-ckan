"""Controlled tag vocabularies used as dataset categories."""

import logging
from ckan.plugins import toolkit

log = logging.getLogger(__name__)

TYPE_OF_RESOURCE = 'type_of_resource'

type_of_resource_list = [
    'Case study',
    'Regional and Thematic Overview',
    # Tag names cannot contain "/", so "Handbook / Manuals" is spelled out
    'Handbooks and manuals',
    'Tools and frameworks',
    'Policy briefs',
]

VOCABULARIES = {
    TYPE_OF_RESOURCE: type_of_resource_list,
}


def create_vocabularies():
    """Create each vocabulary and any of its tags that are missing.

    Safe to run on every startup; existing vocabularies and tags are kept.
    """
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    for name, tags in VOCABULARIES.items():
        try:
            vocab = toolkit.get_action('vocabulary_show')(context, {'id': name})
        except toolkit.ObjectNotFound:
            vocab = toolkit.get_action('vocabulary_create')(
                context, {'name': name}
            )
        existing = {tag['name'] for tag in vocab.get('tags', [])}
        for tag in tags:
            if tag not in existing:
                toolkit.get_action('tag_create')(
                    context, {'name': tag, 'vocabulary_id': vocab['id']}
                )
