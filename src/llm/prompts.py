"""Custom prompt template system."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


@dataclass
class PromptTemplate:
    """Template for generating prompts."""

    template: str
    variables: dict[str, str] = field(default_factory=dict)
    required_vars: list[str] = field(default_factory=list)
    description: str | None = None

    def __post_init__(self):
        """Validate template and extract required variables."""
        # Extract required variables from template
        self.required_vars = re.findall(r'\{([^}]+)\}', self.template)

        # Remove any variables that have defaults
        self.required_vars = [
            var for var in self.required_vars
            if var not in self.variables
        ]

    def format(self, **variables) -> str:
        """Format the template with variables."""
        try:
            return self.template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Invalid variable reference: {e}") from e
        except (TypeError, AttributeError) as e:
            raise ValueError(f"Invalid template format: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error formatting template: {e}")
            raise ValueError(f"Unexpected template formatting error: {e}") from e

@dataclass
class PromptLibrary:
    """Library of prompt templates."""

    templates: dict[str, PromptTemplate] = field(default_factory=dict)

    def add_template(self,
                    name: str,
                    template: PromptTemplate) -> None:
        """Add template to library.

        Args:
            name: Template name
            template: Template instance
        """
        self.templates[name] = template

    def get_template(self, name: str) -> PromptTemplate:
        """Get template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate: Template instance

        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            raise KeyError(f"Template not found: {name}")
        return self.templates[name]

    def format_prompt(self,
                     name: str,
                     **kwargs) -> str:
        """Format prompt template.

        Args:
            name: Template name
            **kwargs: Variable values

        Returns:
            str: Formatted prompt
        """
        template = self.get_template(name)
        return template.format(**kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PromptLibrary':
        """Create library from dictionary.

        Args:
            data: Dictionary with templates

        Returns:
            PromptLibrary: Created library
        """
        templates = {}

        for name, template_data in data.items():
            try:
                template = PromptTemplate(
                    template=template_data['template'],
                    variables=template_data.get('variables', {}),
                    description=template_data.get('description')
                )
                templates[name] = template
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Invalid template data for '{name}': {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error creating template '{name}': {e}")
                continue

        return cls(templates=templates)

    def to_dict(self) -> dict[str, Any]:
        """Convert library to dictionary.

        Returns:
            dict: Library as dictionary
        """
        return {
            name: {
                'template': template.template,
                'variables': template.variables,
                'required_vars': template.required_vars,
                'description': template.description
            }
            for name, template in self.templates.items()
        }

    @classmethod
    def load_yaml(cls, path: Path) -> 'PromptLibrary':
        """Load templates from YAML file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f"Cannot access template file {path}: {e}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template file {path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading templates: {e}")
            raise ValueError(f"Unexpected error loading templates from {path}: {e}") from e

    def save_yaml(self, path: Path) -> None:
        """Save templates to YAML file."""
        try:
            data = self.to_dict()
            with open(path, 'w') as f:
                yaml.safe_dump(data, f, sort_keys=False)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot write to template file {path}: {e}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"YAML serialization error for {path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error saving templates: {e}")
            raise ValueError(f"Unexpected error saving templates to {path}: {e}") from e

# Default prompt templates
DEFAULT_TEMPLATES = {
    'rename': PromptTemplate(
        template="""Please suggest a new filename for this file.

Current filename: {filename}
File content preview:
{preview}

The new filename should:
1. Be descriptive and meaningful
2. Follow standard naming conventions
3. Use lowercase with underscores
4. Include relevant information from the content
5. Be concise but clear

Please provide:
1. The suggested new filename
2. A brief explanation of your reasoning""",
        variables={
            'preview': '(No preview available)'
        },
        description="Template for file rename suggestions"
    ),

    'batch_rename': PromptTemplate(
        template="""Please suggest new filenames for these files.

Files:
{file_list}

The new filenames should:
1. Be descriptive and meaningful
2. Follow standard naming conventions
3. Use lowercase with underscores
4. Include relevant information from the content
5. Be concise but clear
6. Maintain consistency across related files

Please provide for each file:
1. The suggested new filename
2. A brief explanation of your reasoning""",
        variables={
            'file_list': '(No files provided)'
        },
        description="Template for batch rename suggestions"
    )
}
