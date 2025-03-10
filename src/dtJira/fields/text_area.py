
class TextAreaContent:

    def __init__(self, content):
        if isinstance(content, str):
            self.content = content
        else:
            self.content = self.format_content(content)

    @staticmethod
    def format_markdown_list(items):
        """Formats a list of strings into a markdown list."""
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def format_content(content):
        if isinstance(content, list):
            return TextAreaContent.format_markdown_list(content)
