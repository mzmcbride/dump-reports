#! /usr/bin/env python
# Public domain; MZMcBride; 2015

# This script is pretty horrible. But then again, so is XML.
# The following snippet can be useful for testing page text logic:
# bzcat file.xml.bz2 | head -1000000 | grep "<sha1>" | sed -e 's#      <sha1>\([a-z0-9]\+\)</sha1>#\1#'

debug = False
limit = None
pattern = r'style[ ]*=[ ]*"(.+?)"'
input_file_name = ('/data/scratch/dumps/enwiki/20151002/' +
                   'enwiki-20151002-pages-meta-current.xml.bz2')

import bz2
import hashlib
import re
from xml.sax.saxutils import unescape

def hasher(content):
    # Credit to Dispenser and Wikipedia for this function.
    # One day I'll understand why the revision table uses base 36 SHA-1.

    def base36encode(number):
        alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
        base36 = ''
        sign = ''

        if number < 0:
            sign = '-'
            number = -number

        if 0 <= number < len(alphabet):
            return sign + alphabet[number]

        while number != 0:
            number, i = divmod(number, len(alphabet))
            base36 = alphabet[i] + base36

        return sign + base36

    hash = hashlib.sha1(content).hexdigest()
    return base36encode(int(hash, 16)).zfill(31)

def better_unescape(content):
    return unescape(content, {"&quot;": '"'})

def find_all_pattern(page_text):
    found_patterns = []
    for match in re.findall(pattern_re, page_text):
        found_patterns.append(match)
    return found_patterns

text = []
loop = False
pages_processed = 0
pattern_re = re.compile(pattern)
input_file = bz2.BZ2File(input_file_name)
all_main_namespace_pages_log = open('enwiki-20151002-all-main-namespace-pages.txt', 'w')
main_namespace_pages_containing_pattern_log = open('enwiki-20151002-main-namespace-pages-containing-pattern.txt', 'w')
main_namespace_pattern_instances_log = open('enwiki-20151002-main-namespace-pattern-instances.txt', 'w')

for line in input_file:
    if line.startswith('    <title>'):
        title = line.strip().replace('<title>', '').replace('</title>', '')
    if line.startswith('    <ns>'):
        isolated_ns = line.strip().replace('<ns>', '').replace('</ns>', '')
        namespace_id = int(isolated_ns)
        if namespace_id == 0:
            all_main_namespace_pages_log.write(title + '\n')
        pages_processed += 1
        if limit and pages_processed > limit:
            break
        if pages_processed % 1000 == 0:
            print(pages_processed)
    if loop:
        if line.find('</text>') == -1:
            if line == '\n':
                text.append('')
            else:
                text.append(line.rstrip('\n'))
            loop = True
        elif line.find('</text>') != -1:
            loop = False
            line = line.replace('</text>\n', '')
            if line == '\n':
                text.append('')
            else:
                text.append(line.rstrip('\n'))
            page_text = better_unescape('\n'.join(text))
            if debug:
                hash = hasher(page_text)
                print(hash)
            if namespace_id == 0:
                patterns = find_all_pattern(page_text)
                if patterns:
                    main_namespace_pages_containing_pattern_log.write(title + '\n')
                    main_namespace_pattern_instances_log.write('\n'.join(patterns) + '\n')
            text = []
    if (line.startswith('      <text xml:space="preserve">') and
        line.find('</text>') != -1):
        page_text = line.strip()
        page_text = page_text.replace('<text xml:space="preserve">', '')
        page_text = better_unescape(page_text.replace('</text>', ''))
        if debug:
            hash = hasher(page_text)
            print(hash)
        loop = False
        if namespace_id == 0:
            patterns = find_all_pattern(page_text)
            if patterns:
                main_namespace_pages_containing_pattern_log.write(title + '\n')
                main_namespace_pattern_instances_log.write('\n'.join(patterns) + '\n')
            text = []
    elif line.startswith('      <text xml:space="preserve">'):
        line = line.rstrip('\n').lstrip(' ')
        line = line.replace('<text xml:space="preserve">', '')
        text.append(line)
        loop = True

input_file.close()
all_main_namespace_pages_log.close()
main_namespace_pages_containing_pattern_log.close()
main_namespace_pattern_instances_log.close()
