import re

token_spec = [
    ('break_tag', r'<br>'),
    ('open_tag', r'<[^/>]+>'),
    ('close_tag', r'</[^/>]+>'),
    ('standalone_tag', r'<[^/>]+/>'),
    ('open_braces', r'{{'),
    ('close_braces', r'}}'),
    ('open_double_square', r'\[\['),
    ('close_double_square', r'\]\]'),
    ('open_single_square', r'\['),
    ('close_single_square', r'\]'),
    ('open_comment', r'<!\-\-'),
    ('close_comment', r'\-\->'),
    ('bar', r'\|'),
    ('heading_tag', r'==+'),
    ('equal', r'='),
    ('punctuation', r'[.,;:\'\"!/\\()\-`]'),
    ('url', r"([a-z]+://)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"),
    ('word', r'[^ \t\n<>{}\[\]\|.;:,\'\"!/\\()`=]+')
]

pattern = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)

def tokenize(text):
    for mo in re.finditer(pattern, text):
        yield (mo.group(), mo.lastgroup)
