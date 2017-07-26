# PyZip2Src2Tgt

This program will convert any text file(s) within a(the) specified zip archive(s) matching the specified "zip" and "source" file extensions to a(many) target file(s) with a specified "target" file extension.

The program features row-by-row, column-by-column, character transformations of the data to compensate for undesirable characters.  Character transformation tuples list is used for transforming characters from one character to another as some analytical tools are unable to handle mixed characters, e.g. Unicode and ASCII, during importation.

```python

# character transformation tuples list used for
# transforming characters from one character to another
# as some analytical tools are unable to handle mixed
# characters, e.g. Unicode and ASCII, during importation

char_xform_tuples_list = []

char_xform_tuples_list.append(('\r\n', ' ')) # carriage-return,
line-feed to single space
char_xform_tuples_list.append(('\n', ' ')) # line-feed to single space
char_xform_tuples_list.append(('\t', ' ')) # tab to single space
char_xform_tuples_list.append((u'\x91', "'")) # diacritic left single
quote to ASCII single quote
char_xform_tuples_list.append((u'\x92', "'")) # diacritic right single
quote to ASCII single quote
char_xform_tuples_list.append((u'\x93', '"')) # diacritic left double
quote to ASCII double quote
char_xform_tuples_list.append((u'\x94', '"')) # diacritic right double
quote to ASCII double quote
char_xform_tuples_list.append((u'\xa0', ' ')) # non-breaking space to
single space

# make sure this character transformation is always the last one added! 
char_xform_tuples_list.append(('  ', ' ')) # double-space to single
space

```
