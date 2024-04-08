def customTextToHtml(text):
    css_styles = '''
    <style>
        * {
            /* css reset */
            margin: 0;
            padding: 0;
            box-sizing: border-box;

            font-size: 14px;
            font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif; /* Common font for readability */

            margin-bottom: 10px; /* Consistent bottom margin */
        }

        pre, code {
            font-size: 14px;
            background-color: #f4f4f4; /* Light grey background for code elements */
            white-space: pre-wrap; /* Ensure long lines of code wrap */
            word-wrap: break-word;
        }

        a, a:hover {
            color: #0645ad; /* Hyperlink color */
            text-decoration: none; /* No underline */
        }

        a:hover {
            text-decoration: underline; /* Underline on hover */
        }

        ul, ol {
            padding-left: 20px; /* Indent list items */
        }

        table {
            border-collapse: collapse; /* Collapses border */
        }

        th, td {
            border: 1px solid #ddd; /* Border for table cells */
            padding: 8px; /* Padding within cells */

        }
    </style>
    '''

    html_lines = []
    in_code_block = False

    for line in text.split('\n'):
        if line.strip() == '```':  # Code block delimiter
            if in_code_block:
                html_lines.append('</pre>')
                in_code_block = False
            else:
                html_lines.append('<pre>')
                in_code_block = True
        elif in_code_block:  # Inside a code block
            html_lines.append(line)
        elif line.startswith('- '):  # List item
            html_lines.append(f'<li>{line[2:]}</li>')
        else:  # Regular text
            html_lines.append(f'{line}<br>')

    return css_styles + '\n'.join(html_lines)
