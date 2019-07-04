#!/usr/bin/python
# coding: UTF-8

import subprocess
import os
import re
import sys

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

heading = [0, 0, 0]

def toc():
    os.chdir('book')
    cmd = 'book sm'
    subprocess.call(cmd.split(), shell=True)
    os.chdir('../')
    return

def find_textboxes_recursively(layout_obj):
    if isinstance(layout_obj, LTTextBox):
        return [layout_obj]

    if isinstance(layout_obj, LTContainer):
        boxes = []
        for child in layout_obj:
            boxes.extend(find_textboxes_recursively(child))
        return boxes
    return []

def chapterGet(chp):
    for i in range(len(heading)):
        if i == chp:
            heading[chp] = heading[chp] + 1
        elif i > chp:
            heading[i] = 0
    return heading

    pdftext = pdftext + txt + '\n'

def makeSummary(summaryInfo):
    lines = []
    lines.append('{% extends "./page.html" %}')
    lines.append('{% block title %}{{ "SUMMARY"|t }}{% endblock %}')
    lines.append('{% macro articles(_articles) %}')
    lines.append('{% for article in _articles %}')
    lines.append('<a href="{{ article.path|contentURL }}{{ article.anchor }}">')
    lines.append('</a>')
    lines.append('{% if article.articles.length > 0 %}')
    lines.append('{{ articles(article.articles) }}')
    lines.append('{% endif %}')
    lines.append('{% endfor %}')
    lines.append('{% endmacro %}')
    lines.append('{% block page %}')
    lines.append('<div class="section toc">')
    lines.append('<h1>{{ "SUMMARY"|t }}</h1>')
    lines.append('{% for part in summary.parts %}')
    lines.append('{{ articles(part.articles) }}')
    lines.append('{% endfor %}')

    index = 0
    for i, j in summaryInfo.items():
        if index < re.sub(r'^((\d|\.)+?)\s.*?$', '\\1', i).count('.') + 1:
            lines.append('<ol>')
        if index > re.sub(r'^((\d|\.)+?)\s.*?$', '\\1', i).count('.') + 1:
            lines.append('</ol>')
        index = re.sub(r'^((\d|\.)+?)\s.*?$', '\\1', i).count('.') + 1
        lines.append('<li>')
        lines.append('<span class="inner">')
        if index != 3:
            lines.append('<a href="{0}">{1}</a>'.format(j.replace('README.md', 'index.html').replace('.md', '.html'), i))
        else:
            lines.append('<a href="{0}#{1}">{2}</a>'.format(j.replace('README.md', '').replace('.md', '.html'), re.sub(r'^(\d|\.)+?\s', '', i),i))
        lines.append('<span class="page">@@@</span>')
        lines.append('</span>')
        lines.append('</span>')
        lines.append('</li>')
    lines.append('</ol>')
    lines.append('</div>')
    lines.append('{% endblock %}')
    f = open('../node_modules/gitbook-plugin-theme-default-extended/_layouts/ebook/summary.html', 'w', encoding='UTF-8')
    f.write('\n'.join(lines))
    f.close()

def createPdf():
    os.chdir('book')
    f = open('SUMMARY.md', 'r', encoding='UTF-8')
    lines = f.readlines()
    f.close()

    filesPath = []
    if os.path.exists('./README.md'):
        filesPath.append('README.md')
    for line in lines:
        if re.search(r'\[[^\]]*?\]\(\)*?', line):
            filesPath.append(re.search(r'\[[^\]]*?\]\(([^\]]*?)\)', line).group(1))

    summaryInfo = {}
    for filePath in filesPath:
        bl = False
        f = open(filePath, 'r', encoding='UTF-8')
        lines = f.readlines()
        f.close
        for line in lines:
            if re.match(r'```', line):
                if bl == False:
                    bl = True
                else:
                    bl == False
            if bl:
                continue
            if re.match(r'^#{1,2}\s.+?$', line):
                chpNumber = ''
                for i, j in enumerate(chapterGet(len(re.match(r'^(#{1,2})', line).group(1)) - 1)):
                    if i == 0:
                        chpNumber = str(j)
                    elif j != 0:
                        chpNumber = chpNumber + '.' + str(j)
                summaryInfo[str(chpNumber) + re.sub(r'^#+', '', line).rstrip()] = filePath

    makeSummary(summaryInfo)

    os.chdir('../')
    cmd = 'gitbook pdf'
    subprocess.call(cmd.split())

    laparams = LAParams(detect_vertical=True)
    resource_manager = PDFResourceManager()
    device = PDFPageAggregator(resource_manager, laparams=laparams)
    interpreter = PDFPageInterpreter(resource_manager, device)
    pdftext = ''

    chpNum = {}

    summary = []
    for k in summaryInfo.keys():
        summary.append(re.sub(r'^([^\s]*?)\s.+?$', '\\1', k))

    keys = []
    for k in summaryInfo.keys():
        keys.append(k)
    print(keys)


    with open('book.pdf', 'rb') as f:
        pageNumber = 0
        for page in PDFPage.get_pages(f):
            pageNumber = pageNumber + 1
            interpreter.process_page(page)
            layout = device.get_result()

            boxes = find_textboxes_recursively(layout)
            boxes.sort(key=lambda b: (-b.y1, b.x0))

            chpText = []
            bl = False
            for box in boxes:
                if '@@@'in box.get_text():
                    bl = True
            if bl:
                continue
            for index, box in enumerate(boxes):
                for lineText in box.get_text().split('\n'):
                    if len(keys) == 0:
                        break
                    if len(lineText) == len(keys[0]) and re.sub(r'((\d|\.))+?\s[^\s]+?$', '\\1', lineText) == re.sub(r'((\d|\.))+?\s[^\s]+?$', '\\1', keys[0]):
                        chpText.append(keys.pop(0))

                if index == len(boxes) -1 and len(chpText) > 0:
                    for text in chpText:
                        chpNum[text] = str(pageNumber)

    for k, v in chpNum.items():
        print(k,v)

    f = open('node_modules/gitbook-plugin-theme-default-extended/_layouts/ebook/summary.html', 'r', encoding='UTF-8')
    text = f.read()
    f.close()

    for k, v in chpNum.items():
        text = re.sub(r'(<a href[^>]*?>' + k + r'</a>[^<]*?<span class=\"page\">)@@@', '\g<1>' + str(v), text)

    f = open('node_modules/gitbook-plugin-theme-default-extended/_layouts/ebook/summary.html', 'w', encoding='UTF-8')
    f.write(text)
    f.close()

    cmd = 'gitbook pdf'
    subprocess.call(cmd.split())

    return

def localServer():
    cmd = 'yarn serve'
    subprocess.call(cmd.split())

def buildFile():
    cmd = 'yarn build'
    subprocess.call(cmd.split())

def parser():
    usage = 'Usage: python {} [--version] [--serve] [--build] [--pdf]'.format(__file__)
    arguments = sys.argv
    if len(arguments) == 1:
        return usage
    arguments.pop(0)
    fname = arguments[0]
    if not fname.startswith('-'):
        return usage
    options = [option for option in arguments if option.startswith('-')]

    if '-h' in options or '--help' in options:
        return usage
    elif '-v' in options or '--version' in options:
        return '{}: version 1.0.0'.format(__file__)

    toc()

    if '-s' in options or '--serve' in options:
        localServer()
        sys.exit()
    elif '-b' in options or '--build' in options:
        buildFile()
        return 'published web-contents in _book'
    elif '-p' in options or '--pdf' in options:
        createPdf()
        return 'published book.pdf'
    return usage

if __name__ == '__main__':
    createPdf()
