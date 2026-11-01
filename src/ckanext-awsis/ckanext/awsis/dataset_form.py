"""Dataset form settings.

Set a field group to True to hide it from the dataset form, False to show it.
Hidden fields keep any stored values; they are posted back as hidden inputs.
"""

HIDDEN_FIELDS = {
    # Maintainer and Maintainer Email
    'maintainer': True,
    # The three "Custom Field" (extras) key/value rows
    'custom_fields': True,
}

# License preselected on the new dataset form (an id from license_list).
# Existing datasets keep whatever license they already have.
DEFAULT_LICENSE_ID = 'other-pd'  # Other (Public Domain)

# Year of Publication dropdown runs from the current year back to this year;
# the validator rejects anything outside that range.
YEAR_OF_PUBLICATION_MIN = 1960
