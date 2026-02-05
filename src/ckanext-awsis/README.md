# ckanext-awsis

AWSIS (Akvo Water Security Information System) theme extension for CKAN.

## Overview

This extension provides a custom theme for the AWSIS data portal, focusing on water management in the Sundarbans region. It features:

- Custom landing page with hero section
- Animated statistics counters
- Thematic area cards
- Featured datasets carousel
- Partner logos section
- Responsive design using Bulma CSS framework

## Installation

1. Activate your CKAN virtual environment
2. Install the extension:
   ```
   pip install -e src/ckanext-awsis
   ```
3. Add `awsis` to `CKAN__PLUGINS` in your `.env` file (should be first in the list)

## Configuration

No additional configuration is required. The theme will automatically apply when the plugin is enabled.

## Partners

- [Akvo](https://akvo.org)
- [Oak Foundation](https://oakfnd.org)

## License

AGPL-3.0
