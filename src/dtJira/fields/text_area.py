import json
import mistune
import subprocess
import json
import base64

def convert_markdown_to_adf(markdown_text):
    """Converts Markdown to JIRA Atlassian Document Format (ADF) using Node.js"""

    try:
        base64_bytes = base64.b64encode(markdown_text.encode("utf-8"))
        base64_string = base64_bytes.decode("utf-8")

        js = f"""import fnTranslate from 'md-to-adf';const inputMarkdown = atob("{base64_string}");const translatedADF = fnTranslate( inputMarkdown );console.log(JSON.stringify(translatedADF, null, 2));"""
        result = subprocess.run(
            ["node", "-e", js],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the JSON output from Node.js
        adf_output = json.loads(result.stdout)
        return adf_output

    except subprocess.CalledProcessError as e:
        print(f"Error running Node.js script: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON output from Node.js")
        return None

class TextAreaContent:

    def __init__(self, content='', json_content=None):
        self.original_content = content
        if not isinstance(content, str):
            content = self.format_content(content)

        if len(content) == 0:
            content = 'No Content'
        if json_content:
            self.content = {
                "content": [
                    {
                        "type": "codeBlock",
                        "attrs": {"language": "json"},
                        "content": [{"type": "text", "text": json_content}]
                    }
                ],
                "type": "doc",
                "version": 1
            }
        else:
            self.content = convert_markdown_to_adf(content)

    def __str__(self):
        return json.dumps(self.content, indent=2)

    @staticmethod
    def format_markdown_list(items):
        """Formats a list of strings into a markdown list."""
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def format_content(content):
        if isinstance(content, list):
            return TextAreaContent.format_markdown_list(content)
