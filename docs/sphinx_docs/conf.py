# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('../../'))
sys.path.insert(0, os.path.abspath('../../backend'))
sys.path.insert(0, os.path.abspath('../../backend/app'))

# Set environment variable to prevent relative import errors
os.environ['PYTHONPATH'] = ':'.join([
    os.path.abspath('../../'),
    os.path.abspath('../../backend'),
    os.path.abspath('../../backend/app'),
    os.environ.get('PYTHONPATH', '')
])

# Set the working directory for imports
os.chdir(os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
project = 'GameChat AI'
copyright = '2025, GameChat AI Team'
author = 'GameChat AI Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.githubpages',
    'myst_parser',  # Markdownサポート
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# AutoDoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# More comprehensive autodoc settings
autodoc_default_flags = ['members', 'undoc-members']

# Additional autodoc settings to handle duplicates
autodoc_preserve_defaults = True
autodoc_class_signature = "separated"

# Suppress warnings for missing modules
autodoc_mock_imports = [
    'openai',
    'upstash_vector',
    'requests',
    'aiohttp',
    'pydantic',
    'fastapi',
    'starlette',
    'uvicorn',
    'redis',
    'sqlalchemy',
    'alembic',
    'pytest',
    'httpx'
]

# Special handling for Pydantic v2 field validators
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented_params"

# Mock difficult imports
autodoc_mock_imports.extend([
    'pydantic.field_validator',
    'pydantic_core'
])

# Ignore import errors during autodoc
autodoc_type_aliases = {}
autodoc_inherit_docstrings = True

# Suppress specific warnings
suppress_warnings = [
    'autodoc.import_object',
    'toc.not_readable',
    'ref.doc',
    'duplicate_object_description',
    'toc.excluded',
    'misc.highlighting_failure',
    'autodoc',
    'autodoc.import_object',
    'py.class_reference'
]

# Templates path
templates_path = ['_templates']

# Source file suffixes
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# Exclude patterns
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'preamble': '',
    'fncychap': '',
    'printindex': '',
}

# -- Options for manual page output ------------------------------------------
man_pages = [
    ('index', 'gamechat-ai', 'GameChat AI Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    ('index', 'GameChatAI', 'GameChat AI Documentation',
     author, 'GameChatAI', 'AI-powered game strategy assistant.',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    # Remove pydantic as the URL is currently 404
    # 'pydantic': ('https://docs.pydantic.dev/', None),
}

# Todo extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True

# Ignore specific warning types
nitpicky = False
nitpick_ignore = [
    ('py:class', 'classmethod'),
    ('py:obj', 'field_validator'),
    ('py:class', 'field_validator'),
]

# Handle Pydantic field validators specifically
def skip_field_validators(app, what, name, obj, skip, options):
    """Skip Pydantic field validators to avoid signature errors"""
    if hasattr(obj, '__name__') and 'field_validator' in str(type(obj)):
        return True
    if name in ['question_not_blank', 'top_k_range']:
        return True
    return skip

def setup(app):
    app.connect('autodoc-skip-member', skip_field_validators)
