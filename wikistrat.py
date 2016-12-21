
import datetime
import hashlib
import os
import random

import requests
from bs4 import BeautifulSoup
from pprint import pprint as pp
from collections import defaultdict
from operator import itemgetter
from PIL import Image, ImageDraw, ImageFont
from dateutil import parser as dtparser


START_YEAR = 2000
END_YEAR = 2017
RAW_DATA_DIR = 'wikixml'
IMAGE_DIR = 'img'

seq_colours = ["#242a42", "#252e46", "#26324b", "#27364f", "#283a53", "#293f58", "#2a435c", "#2b4760", "#2c4c64", "#2d5068", "#2e546c", "#30596f", "#315d73", "#336276", "#35667a", "#376b7d", "#396f80", "#3b7483", "#3e7986", "#417d89", "#45828c", "#48868e", "#4c8b91", "#508f93", "#559496", "#599898", "#5e9d9a", "#63a29c", "#68a69e", "#6eaba0", "#74afa2", "#7ab4a4", "#80b8a6", "#86bca7", "#8cc1a9", "#93c5ab", "#9acaad", "#a1ceaf", "#a8d2b1", "#afd6b3", "#b6dbb5", "#bedfb7", "#c5e3b9", "#cde7bb", "#d5ebbe", "#ddefc0", "#e5f3c3", "#edf7c6", "#f5fbc9", "#fdffcc"]
qual_colours = ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"]

def file_exists(fname):
    if os.path.isfile(fname):
        return True
    return False

def write_text(data, f_path):
        with open(f_path, 'w') as outfile:
            outfile.write(data)
        print('{} written.').format(f_path)

def read_text(f_path):
    with open (f_path, "r") as infile:
        txt=infile.read()
    print('Read {}.'.format(f_path))
    return txt

def get_resource(url):
        print('Fetching: {}'.format(url))
        r = requests.get(url)
        if r.status_code != 200:
            print('Error: {}.'.format(r.status_code))
        return r


class WikiStrat:
    def __init__(self, data_dir='wikixml', img_dir='img'):
        self.base_url = 'https://en.wikipedia.org/wiki/Special:Export/'
        self.data_dir = data_dir
        self.img_dir = img_dir
        print self.data_dir
        #self.differ = difflib.Differ()

    def get_history(self, title):
        dstfile = '{}/{}.xml'.format(self.data_dir, title.lower())
        url = '{}{}?history'.format(self.base_url, title)
        r = get_resource(url)
        write_text(r.content, dstfile)

    def extract_article_text(self, s, title):
        title = title.lower()
        title = title.replace('_', ' ')
        s = s.lower()
        parts = s.split(title)
        s = title.join(parts[1:-1])
        s = title + s
        lines = s.splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line:
                result.append(line)
        return result

    def parse(self, title, refresh=False, y_scale=1.0):
        self.y_scale = y_scale
        self.revisions = defaultdict(list)
        self.author_count = defaultdict(int)
        self.hash_authors = {}
        self.max_y_val = 0
        self.min_dt_val = dtparser.parse('2100-12-22T00:43:58Z')
        self.max_dt_val = dtparser.parse('1800-12-22T00:43:58Z')
        srcfile = '{}/{}.xml'.format(self.data_dir, title.lower())
        if not file_exists(srcfile) or refresh:
            self.get_history(title)
        txt = read_text(srcfile)
        soup = BeautifulSoup(txt, 'lxml-xml')
        revisions = soup.find_all('revision')

        last_date = datetime.datetime.now()
        revision_num = 1
        for i, rev in enumerate(revisions):
            try:
                next_dt = revisions[i+1].timestamp.get_text()
            except IndexError:
                next_dt = rev.timestamp.get_text()
            row = {
                'id':rev.id.get_text(),
                'timestamp':rev.timestamp.get_text(),
                'dt':dtparser.parse(rev.timestamp.get_text()),
                'next_dt':dtparser.parse(next_dt),
                'length':len(rev.text),
                'user_name':'',
                'revision_num':revision_num,
                'line_num':None
            }

            try:
                row['user_name'] = rev.contributor.ip.get_text()
            except AttributeError:
                try:
                    user = rev.contributor.username.get_text()
                    row['user_name'] = user.encode('utf-8')
                except AttributeError:
                    continue

            txt = self.extract_article_text(rev.text, title)

            line_num = 0

            for line in txt:
                row['line_num'] = line_num
                line_hash = hashlib.sha224(line.encode('utf-8')).hexdigest()
                if line_hash not in self.hash_authors:
                    self.hash_authors[line_hash] = row['user_name']
                self.author_count[row['user_name']] += 1
                self.revisions[line_hash].append(dict(row))
                if line_num > self.max_y_val:
                    self.max_y_val = line_num
                line_num += 1
            if row['dt'] < self.min_dt_val:
                self.min_dt_val = row['dt']
            if row['dt'] > self.max_dt_val:
                self.max_dt_val = row['dt']
            self.max_revision_num = revision_num
            revision_num += 1

        self.make_qual_colours()
        self.max_y_val *= self.y_scale
        dst_base_fname = dst_fname='{}/{}_'.format(self.img_dir, title.lower())
        self.viz_revisions(dst_fname='{}r.png'.format(dst_base_fname))
        self.viz_revisions(dst_fname='{}p.png'.format(dst_base_fname), viz_type='people')
        self.viz_revisions(dst_fname='{}a.png'.format(dst_base_fname), viz_type='anon')

    def make_qual_colours(self):
        src_cols = list(qual_colours)
        self.auth_colours = {}
        for auth in dict(self.author_count).keys():
            random.seed(auth.lower())
            self.auth_colours[auth] = (
                random.randint(0,255),
                random.randint(0,255),
                random.randint(0,255),
            )

    def export_revisions(self, title):
        report = []
        for k, vals in dict(self.revisions).items():
            for obs in vals:
                obs['first_added'] = vals[0]['revision_num']
                #obs['line_hash'] = k
                report.append(obs)
        sort_report = sorted(report, key=itemgetter('revision_num', 'line_num'))
        print len(sort_report)
        farmer.write_json(sort_report, 'data/{}.json'.format(title.lower()))

    def viz_revisions(self, dst_fname="test.png", viz_type='time', img_width=900, img_height=350, sf=8):
        img_width *= sf
        img_height *= sf
        img = Image.new("RGB", (img_width, img_height), (255,255,255))
        draw = ImageDraw.Draw(img)

        block_height = self.scale(1, (0, self.max_y_val), (0, img_height))
        num_cols = min(len(seq_colours) - 1, self.max_revision_num)

        self.max_x_val = self.seconds_delta(self.min_dt_val, self.max_dt_val)
        font = ImageFont.truetype("Arial.ttf", 12 * sf)

        # draw the years
        for year in range(START_YEAR, END_YEAR):
            dt_year = dtparser.parse('{}-01-01T00:00:00Z'.format(year))
            if dt_year < self.min_dt_val:
                continue
            px_year = self.scale(
                self.seconds_delta(self.min_dt_val, dt_year),
                (0, self.max_x_val),
                (0, img_width)
            )
            pos = [px_year,0, px_year + sf / 2,img_height]
            draw.rectangle(pos, fill='#bbb')

        # draw the histories
        for k, revision in dict(self.revisions).items():
            col_ind = self.scale(
                revision[0]['revision_num'],
                (0, self.max_revision_num),
                (0, num_cols)
            )

            if viz_type == 'time':
                col = seq_colours[col_ind]
            for obs in revision:
                x = self.scale(
                    self.seconds_delta(self.min_dt_val, obs['dt']),
                    (0, self.max_x_val),
                    (0, img_width)
                )

                block_width = self.scale(
                    self.seconds_delta(obs['dt'], obs['next_dt']),
                    (0, self.max_x_val),
                    (0, img_width)
                )
                y = self.scale(
                    obs['line_num'],
                    (0, self.max_y_val),
                    (0, img_height)
                )

                pos = [x, y, x + block_width, y + block_height]
                first_user = self.hash_authors[k]
                if viz_type == 'people':
                    '''random.seed(first_user)
                    col = (
                        random.randint(0,255),
                        random.randint(0,255),
                        random.randint(0,255),
                    )'''
                    col = self.auth_colours[first_user]
                if viz_type == 'anon':
                    col = '#dcdcdc'
                    # assumes IPv4
                    if first_user.count('.') == 3:
                        try:
                            int(first_user.replace('.', ''))
                            col = 'indianred'
                        except ValueError:
                            pass
                draw.rectangle(pos,fill=col)

        # label the years
        for year in range(START_YEAR, END_YEAR):
            dt_year = dtparser.parse('{}-01-01T00:00:00Z'.format(year))
            if dt_year < self.min_dt_val:
                continue
            px_year = self.scale(
                self.seconds_delta(self.min_dt_val, dt_year),
                (0, self.max_x_val),
                (0, img_width)
            )
            draw.text((px_year + (5 * sf), img_height - (15 * sf)), str(year) , '#555' ,font=font)

        img.thumbnail((img_width/sf, img_height/sf), Image.ANTIALIAS)
        img.save(dst_fname)

    def seconds_delta(self, a, b):
        return abs(int((b-a).total_seconds()))

    def scale(self, val1, _range, domain):
        delta_range = _range[1] - _range[0]
        delta_domain = domain[1] - domain[0]
        val2 = (((val1 - _range[0]) * delta_domain) / delta_range) + domain[0]
        return val2

def main():
    wikistrat = WikiStrat(data_dir=RAW_DATA_DIR, img_dir=IMAGE_DIR)
    wikistrat.parse('Tirau', refresh=True)

if __name__ == '__main__':
    main()
