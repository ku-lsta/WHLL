# -*- coding: utf-8 -*-

import glob
import gzip
import tarfile
import json
import tqdm
import tqdm.contrib.concurrent
import os
import re
import bs4

RE_spacelike = re.compile(r'\s+')
RE_brackets = re.compile(r'\(.*?\)')

coord = {}

RE_spacelike = re.compile(r'\s+')
RE_brackets = re.compile(r'\(.*?\)')

def pick_coordinates(cirrussearch_dump, output_dir):

    global coord

    with gzip.open(cirrussearch_dump, 'rt') as f, open(f'{output_dir}/coord.tsv', 'w') as wf:

        #for i, line in enumerate(f):
        i_line = 0
        while line := f.readline():
            i_line += 1
            json_data = json.loads(line)

            if 'index' in json_data:
                id = json_data['index']['_id']
            else:
                try:
                    c = json_data['coordinates']
                except:
                    print(f'Skip line {i_line}: No "coordinates" field')
                    continue
                
                if c != []:
                    t = json_data['title']
                    try:
                        c = c[0]['coord']
                    except:
                        print(f'Skip line {i_line}: No "Coord" field in "coordinates"')
                        continue

                    text = f'{t}\t{float(c["lat"]):.5f}\t{float(c["lon"]):.5f}\t{id}\t{0}\n'
                    wf.write(text)
                    coord[t] = (float(c["lat"]), float(c["lon"]), id, 0)

                    try:
                        redirect = json_data['redirect']
                    except:
                        print(f'Warning {i_line}: No "redirect" field')
                        continue
                                        
                    for r in redirect:
                        text = f'{r["title"]}\t{float(c["lat"]):.5f}\t{float(c["lon"]):.5f}\t{id}\t{1}\n'
                        wf.write(text)
                        coord[r['title']] = (float(c["lat"]), float(c["lon"]), id, 1)

def load_coord_dict(coord_file, key=0):

    global coord

    with open(coord_file, 'r') as f:
        coord_list = [l.strip().split('\t') for l in f]
        coord = {l[key]: (float(l[1]), float(l[2]), int(l[3]), int(l[4])) for l in coord_list}

def WHLL(html_dump, output_dir, max_worker=8):

    job_list = []
    if html_dump.endswith('.tar.gz'):
        with tarfile.open(html_dump, 'r') as tarf:
            for member in tarf.getmembers():
                if member.name.endswith('.ndjson'):
                    job_list.append((tarf.extractfile(member), f'{output_dir}/{os.path.basename(member.name)}.jsonl'))
    else:
        job_list = [(fname, f'{output_dir}/{os.path.basename(fname)}') for fname in glob.glob(f'{html_dump}/*.ndjson')]

    tqdm.contrib.concurrent.process_map(
        WHLL_file,
        job_list,
        max_workers=max_worker,
        chunksize=1,
        ncols=0,
    )

def WHLL_file(args):

    input_file_pointer, output_filename = args

    if isinstance(input_file_pointer, str):
        input_file_pointer = open(input_file_pointer, 'r')
    
    with open(output_filename, 'w') as output_file_pointer:

        for line in input_file_pointer:
            json_data = json.loads(line)
            title = json_data['name']

            if title in coord and coord[title][3] == 0:

                soup = bs4.BeautifulSoup(json_data['article_body']['html'], 'html.parser')
                p_list = soup.find_all(name='p')
                ret_d = WHLL_article(p_list, title)

                if len(ret_d['text'].strip()) > 0:
                    d = {'id': json_data['identifier'], 'title': title}
                    d.update(ret_d)
                    output_file_pointer.write(json.dumps(d, ensure_ascii=False) + '\n')

def WHLL_article(p_list, title):

    c = 0
    text = ''
    a_list = []

    for p in p_list:

        # one paragraph (<p> tag)
        if p.get_text().strip() == '':
            # empty paragraph
            continue

        if p.get('class') and 'asbox-body' in p.get('class'):
            # skip asbox-body ( https://en.wikipedia.org/wiki/Template:Asbox )
            continue

        if mw := p.get('data-mw'):
            if 'Template:' in mw:
                # skip template
                continue

        sentence, annotation = WHLL_paragraph(p, title)

        for a in annotation:
            a_list.append((c+a[0], c+a[1], *a[2:4]))

        c += len(sentence)+1

        text += sentence + ' '

    if len(text) > 0:
        text = text[:-1]

    return {'text': text, 'gold': a_list}

def WHLL_paragraph(p, title):

    self_coord = coord[title]

    for a in p.find_all(name='a', rel='mw:WikiLink'):
        link_title = a.get('title')
        if link_title in coord:
            c = coord[link_title]
            a.attrs['lat'] = c[0]
            a.attrs['lng'] = c[1]

    title_notation = alternatename(title)
    sentence = ''
    annotation = []
    c = 0

    for e in p:

        flg_anno_yet = True
        text = e.get_text()
        text = RE_spacelike.sub(' ', text)

        if len(text) == 0:
            continue

        if isinstance(e, bs4.element.Tag):

            if e.get('class') and 'mw-ref' in e.get('class'):
                # skip reference
                continue

            if e.name == 'style':
                # skip <style> tag
                continue

            if e.get('data-mw') and 'Template:' in e.get('data-mw'):
                # skip template
                continue

            if span_list := e.find_all(name='span'):
                all_mw = ''.join([span.get('data-mw') for span in span_list if span.get('data-mw')])
                if 'Template:' in all_mw:
                    # skip template
                    continue

            if style_list := e.find_all(name='style'):
                all_mw = ''.join([style.get('data-mw') for style in style_list if style.get('data-mw')])
                if 'Template:' in all_mw:
                    # skip template
                    continue

            if e.get('lat'):
                annotation.append([c, c+len(text), text, (e.get('lat'), e.get('lng'))])
                flg_anno_yet = False

        if flg_anno_yet:
            for notation in title_notation:
                try:
                    #spans = [(m.start(), m.end()) for m in re.finditer(notation, text)]
                    spans = find_string_list(notation, text)
                except:
                    print(notation, text)
                    exit()
                if len(spans) > 0:
                    for span in spans:
                        annotation.append([c+span[0], c+span[1], notation, (self_coord[0], self_coord[1])])
                    break
                
        sentence += text
        c += len(text)

    return sentence, annotation

def find_string_list(target, text):

    out = []
    c = 0
    while c < len(text):
        i = text[c:].find(target)
        if i == -1:
            break
        out.append((c+i, c+i+len(target)))
        c += i+len(target)
    return out

def alternatename(title):

    out = [title]

    if '(' in title:
        # remove brackets and content
        out.append(RE_brackets.sub('', title).strip())

    if ',' in title:
        # string before comma
        out.append(title.rsplit(',', maxsplit=1)[0].rstrip())

    return out

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='WHLL: A Python package for Wikipedia Hyperlink-based Location Linking')

    parser.add_argument('cirrussearch_dump', type=str,
                        help='Path to the CirrusSearch dump file')
    parser.add_argument('html_dump', type=str,
                        help='Path to the HTML dump files')
    parser.add_argument('output_dir', type=str,
                        help='Path to the output directory')
    parser.add_argument('--make_coord', action='store_true',
                        help='Make coord.tsv file')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.make_coord:
        print('Pick coordinates')
        pick_coordinates(args.cirrussearch_dump, args.output_dir)
        print('Done')
        
    load_coord_dict(f'{args.output_dir}/coord.tsv')
    
    print('WHLL')
    WHLL(args.html_dump, args.output_dir)
    print('Done')
    
