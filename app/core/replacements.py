import re

def perform_replacements(text: str, task_replacements: dict = None) -> str:
    """
    Performs safe regex replacements on the text based on task config.

    Args:
        text: The original text.
        task_replacements: A dictionary containing 'find_user', 'replace_user',
                           'find_link', 'replace_link'.
    """
    if not text:
        return text

    if not task_replacements:
        return text

    # User Replacement
    find_user = task_replacements.get('find_user')
    replace_user = task_replacements.get('replace_user')

    if find_user and replace_user:
        escaped_find = re.escape(find_user)
        # Pattern: (?<!\w)@username\b
        # We handle @ symbol explicitly in the input usually, but let's be safe
        pattern = r'(?<!\w)' + escaped_find + r'\b'
        text = re.sub(pattern, replace_user, text, flags=re.IGNORECASE)

    # Link Replacement
    find_link = task_replacements.get('find_link')
    replace_link = task_replacements.get('replace_link')

    if find_link and replace_link:
        escaped_link = re.escape(find_link)
        # Pattern: (?<!\w)link(?!\w)
        pattern = r'(?<!\w)' + escaped_link + r'(?!\w)'
        text = re.sub(pattern, replace_link, text, flags=re.IGNORECASE)

    return text
