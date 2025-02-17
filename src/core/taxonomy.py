"""Taxonomy system for organizing files."""

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger
from markdown_it import MarkdownIt

from src.constants import TAXONOMY_BACKUP_FORMAT, TAXONOMY_BACKUP_PREFIX


@dataclass
class TaxonomyRule:
    """A rule for organizing files.

    Args:
        name: Rule name/identifier
        pattern: Pattern to match against file content
        target_dir: Target directory for matching files
        description: Description of the rule
        examples: Example files that match this rule
        priority: Rule priority (higher numbers take precedence)
        date_format: Date format to use (full or year)
    """
    name: str
    pattern: str
    target_dir: str
    description: str = ""
    examples: list[str] = None
    priority: int = 0
    date_format: str = "full"

    def __post_init__(self):
        """Initialize after creation."""
        if self.examples is None:
            self.examples = []
        self.pattern = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, content: str) -> bool:
        """Check if content matches this rule.

        Args:
            content: Content to check

        Returns:
            bool: True if content matches rule
        """
        return bool(self.pattern.search(content))


class TaxonomyParser:
    """Parser for taxonomy markdown files."""

    def __init__(self, path: Path):
        """Initialize parser.

        Args:
            path: Path to taxonomy markdown file
        """
        self.path = path
        self.rules: list[TaxonomyRule] = []
        self.md = MarkdownIt()
        self._content = None
        self._load_rules()

    @property
    def content(self) -> str:
        """Get the raw taxonomy content.

        Returns:
            str: Raw taxonomy content
        """
        if self._content is None:
            self._content = self.path.read_text() if self.path.exists() else ""
        return self._content

    def _load_rules(self) -> None:
        """Load rules from markdown file."""
        if not self.path.exists():
            logger.warning(f"Taxonomy file not found at {self.path}")
            return

        self._content = self.path.read_text()
        ast = self.md.parse(self._content)

        current_section = None
        current_rule = {}

        for token in ast:
            if token.type == "heading":
                # Start new section
                current_section = token.content.lower()
                if current_section == "rules":
                    current_rule = {}

            elif token.type == "bullet_list" and current_section == "rules":
                # Process rule definition
                for item in token.children:
                    if item.type == "list_item":
                        key, value = self._parse_list_item(item.content)
                        if key:
                            current_rule[key] = value

                # Create rule if we have required fields
                if all(k in current_rule for k in ["name", "pattern", "target_dir"]):
                    self.rules.append(TaxonomyRule(**current_rule))
                    current_rule = {}

    def _parse_list_item(self, content: str) -> tuple[str | None, str | None]:
        """Parse a list item into key-value pair.

        Args:
            content: List item content

        Returns:
            tuple[str | None, str | None]: Key-value pair or None if not valid
        """
        if ":" not in content:
            return None, None

        key, value = content.split(":", 1)
        return key.strip().lower(), value.strip()

    def find_matching_rule(self, content: str) -> TaxonomyRule | None:
        """Find the highest priority rule matching the content.

        Args:
            content: Content to match against rules

        Returns:
            TaxonomyRule | None: Matching rule or None if no match
        """
        matching_rules = [rule for rule in self.rules if rule.matches(content)]
        if not matching_rules:
            return None

        # Return highest priority rule
        return max(matching_rules, key=lambda r: r.priority)

    def backup(self) -> Path:
        """Create backup of taxonomy file.

        Returns:
            Path: Path to backup file
        """
        timestamp = datetime.now().strftime(TAXONOMY_BACKUP_FORMAT)
        backup_path = self.path.parent / f"{TAXONOMY_BACKUP_PREFIX}{timestamp}.md"

        shutil.copy2(self.path, backup_path)
        logger.info(f"Created taxonomy backup at {backup_path}")

        return backup_path

    def update_rules(self, new_rules: list[TaxonomyRule]) -> None:
        """Update taxonomy rules.

        Args:
            new_rules: New rules to add/update
        """
        # Create backup before modifying
        self.backup()

        # Update rules
        self.rules = new_rules

        # Write updated rules
        self._write_rules()

    def _write_rules(self) -> None:
        """Write rules back to markdown file."""
        content = ["# Taxonomy Rules", ""]

        # Write rules section
        content.append("## Rules")
        content.append("")

        for rule in sorted(self.rules, key=lambda r: (-r.priority, r.name)):
            content.extend([
                f"### {rule.name}",
                "",
                f"- Pattern: {rule.pattern.pattern}",
                f"- Target Directory: {rule.target_dir}",
                f"- Priority: {rule.priority}",
                f"- Date Format: {rule.date_format}",
                "",
                f"{rule.description}",
                "",
                "Examples:",
                *[f"- {example}" for example in rule.examples],
                ""
            ])

        # Write to file
        self.path.write_text("\n".join(content))
        logger.info(f"Updated taxonomy rules at {self.path}")

    def generate_diff(self, new_rules: list[TaxonomyRule]) -> str:
        """Generate diff between current and new rules.

        Args:
            new_rules: New rules to compare against

        Returns:
            str: Diff in readable format
        """
        current = {rule.name: rule for rule in self.rules}
        proposed = {rule.name: rule for rule in new_rules}

        diff = []

        # Find added rules
        added = set(proposed.keys()) - set(current.keys())
        if added:
            diff.append("Added Rules:")
            for name in sorted(added):
                rule = proposed[name]
                diff.extend([
                    f"+ {name}:",
                    f"  Pattern: {rule.pattern.pattern}",
                    f"  Target: {rule.target_dir}",
                    ""
                ])

        # Find removed rules
        removed = set(current.keys()) - set(proposed.keys())
        if removed:
            diff.append("Removed Rules:")
            for name in sorted(removed):
                rule = current[name]
                diff.extend([
                    f"- {name}:",
                    f"  Pattern: {rule.pattern.pattern}",
                    f"  Target: {rule.target_dir}",
                    ""
                ])

        # Find modified rules
        modified = set(current.keys()) & set(proposed.keys())
        changes = []
        for name in sorted(modified):
            old = current[name]
            new = proposed[name]
            if (old.pattern != new.pattern or
                old.target_dir != new.target_dir or
                old.priority != new.priority or
                old.date_format != new.date_format):
                changes.extend([
                    f"~ {name}:",
                    f"  Pattern: {old.pattern.pattern} -> {new.pattern.pattern}",
                    f"  Target: {old.target_dir} -> {new.target_dir}",
                    f"  Priority: {old.priority} -> {new.priority}",
                    f"  Date Format: {old.date_format} -> {new.date_format}",
                    ""
                ])

        if changes:
            diff.append("Modified Rules:")
            diff.extend(changes)

        return "\n".join(diff) if diff else "No changes"
