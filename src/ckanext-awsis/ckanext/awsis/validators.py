"""Validators for AWSIS dataset fields."""

import datetime
import re

from ckan.plugins import toolkit

from ckanext.awsis.dataset_form import YEAR_OF_PUBLICATION_MIN


def year_of_publication(value):
    """Accept a 4-digit year from YEAR_OF_PUBLICATION_MIN to this year.

    Empty values become None so the field stays optional. Returns the year
    as a string, e.g. '2024'.
    """
    if value is None or str(value).strip() == '':
        return None
    value = str(value).strip()
    max_year = datetime.date.today().year
    if not re.fullmatch(r'\d{4}', value) or not (
        YEAR_OF_PUBLICATION_MIN <= int(value) <= max_year
    ):
        raise toolkit.Invalid(
            toolkit._(
                'Year must be a 4-digit year between {min} and {max}'
            ).format(min=YEAR_OF_PUBLICATION_MIN, max=max_year)
        )
    return value
