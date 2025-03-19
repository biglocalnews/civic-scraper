"""
BoardDocs parser implementation for civic-scraper.
"""
from bs4 import BeautifulSoup
import json
from typing import Dict, Any


class BoardDocsParser:
    """Parser for BoardDocs HTML content"""

    def parse_minutes_content(self, html_content: str) -> str:
        """
        Parse minutes HTML content and extract meaningful text.

        Args:
            html_content: HTML content from BoardDocs minutes page

        Returns:
            Parsed minutes content as plain text
        """
        if not html_content:
            return "No minutes content available"

        soup = BeautifulSoup(html_content, 'html.parser')
        output_text = []

        for element in soup.find_all(['p', 'li']):
            text = element.get_text(separator='\n', strip=True)
            if text:
                if element.name == 'li':
                    output_text.append("  * " + text)
                else:
                    output_text.append(text)

        return "\n\n".join(output_text)

    def parse_agenda_html(self, html_content: str) -> Dict[str, Any]:
        """
        Parse agenda HTML content and extract structured information.

        Args:
            html_content: HTML content from BoardDocs agenda page

        Returns:
            Dictionary with structured agenda information
        """
        if not html_content:
            return {"categories": []}

        # Try to parse as JSON first
        try:
            return json.loads(html_content)
        except json.JSONDecodeError:
            # If not valid JSON, parse as HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            structured_agenda = {'categories': []}

            # Find all category containers
            category_containers = soup.find_all('dl', class_='wrap-category')

            for category in category_containers:
                # Extract category header
                category_header = category.find('dt', class_='category')
                if not category_header:
                    continue

                category_order = category_header.find('span', class_='order')
                category_order = category_order.text.strip() if category_order else ""

                category_name = category_header.find('span', class_='category-name')
                category_name = category_name.text.strip() if category_name else ""

                category_id = category_header.get('id', '')
                category_unique = category_header.get('unique', '')

                # Find agenda items for this category
                items = []
                agenda_items = soup.find_all('li', class_='item')
                for item in agenda_items:
                    if item.get('categoryid') == category_id or item.get('categoryunique') == category_unique:
                        item_order = item.find('span', class_='order')
                        item_order = item_order.text.strip() if item_order else ""

                        item_title = item.find('span', class_='title')
                        item_title = item_title.text.strip() if item_title else ""

                        action_type_div = item.find('div', class_='actiontype')
                        action_type = action_type_div.text.strip() if action_type_div else ""

                        has_attachment = bool(item.find('i', class_='fa-file-text-o'))

                        items.append({
                            'order': item_order,
                            'title': item_title,
                            'action_type': action_type,
                            'has_attachment': has_attachment,
                            'item_id': item.get('id', ''),
                            'item_unique': item.get('unique', '')
                        })

                structured_agenda['categories'].append({
                    'order': category_order,
                    'name': category_name,
                    'id': category_id,
                    'unique': category_unique,
                    'items': items
                })

            return structured_agenda

    def format_structured_agenda(self, structured_agenda: Dict[str, Any]) -> str:
        """
        Format structured agenda as a readable text string.

        Args:
            structured_agenda: Structured agenda dictionary

        Returns:
            Formatted agenda text
        """
        formatted_text = []

        for category in structured_agenda.get('categories', []):
            formatted_text.append(f"{category.get('order', '')} {category.get('name', '')}")

            for item in category.get('items', []):
                attachment_indicator = "[Has Attachment]" if item.get('has_attachment') else ""
                action_type = f"({item.get('action_type', '')})" if item.get('action_type') else ""
                formatted_text.append(
                    f"  {item.get('order', '')} {item.get('title', '')} {action_type} {attachment_indicator}"
                )

            formatted_text.append("")  # Empty line between categories

        return "\n".join(formatted_text)
