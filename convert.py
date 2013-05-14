from datetime import datetime
import os
import re
import sys

import sqlalchemy as sa
import html2text


### Helper functions
outdir = 'content'
def subdir(sd, parent=outdir):
    sd = os.path.join(parent, sd)
    if not os.path.exists(sd):
        os.mkdir(sd)
    return sd


def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)


def to_date(time_integer):
    date = datetime.fromtimestamp(float(time_integer))
    return date.strftime("%Y-%m-%d %H:%M")


def to_markdown(text, t_format):
    if 'html' in t_format:
        if t_format == 'filtered_html':
            html = text.replace('\n', '<br>')
        else:
            html = text
        return html2text.html2text(html.decode('utf-8')).encode('utf-8')

    return text


### DB to file functions
def save_users(meta, directory='people'):
    userdir = subdir(directory)

    # Get tables
    users = meta.tables['users']
    field_body = meta.tables['field_data_body']
    field_aboutme = meta.tables['field_data_field_aboutme']
    field_name = meta.tables['field_data_field_name']
    field_position = meta.tables['field_data_field_position']
    taxonomy_term_data = meta.tables['taxonomy_term_data']

    # Do DB magic
    activeusers = users.select(users.c.status > 0).alias('active')
    aboutme = field_aboutme.alias('aboutme')
    fullname = field_name.alias('fullname')
    position = field_position.alias('_position')
    position = position.join(taxonomy_term_data,
        taxonomy_term_data.c.tid==position.c.field_position_tid
    ).alias('position')
    biographies = activeusers.join(aboutme,
        aboutme.c.entity_id==activeusers.c.uid)
    biographies = biographies.join(fullname,
        biographies.c.active_uid==fullname.c.entity_id)
    biographies = biographies.join(position,
        biographies.c.active_uid==position.c._position_entity_id)

    # Write to disk
    for bio in biographies.select().execute():
        userfile = os.path.join(userdir,
                                bio.field_name_value.replace(' ', '-') + '.md')
        with open(userfile, 'w') as f:
            f.write('name: ' + bio.field_name_value + '\n')
            f.write('email: ' + bio.mail + '\n')
            f.write('position: ' + bio.taxonomy_term_data_name + '\n')
            f.write('\n')
            f.write(to_markdown(bio.field_aboutme_value,
                                bio.field_aboutme_format) + '\n')


def save_articles(meta, directory='blog'):
    articledir = subdir(directory)

    # Get tables
    node = meta.tables['node']
    users = meta.tables['users']
    field_body = meta.tables['field_data_body']

    # Do DB magic
    articles = node.select(node.c.type == 'article').alias('article')
    usersubset = sa.sql.select([users.c.uid, users.c.mail]).alias('userinfo')
    articles = articles.join(usersubset, articles.c.uid==usersubset.c.uid)
    articles = articles.join(field_body,
                             articles.c.article_nid==field_body.c.entity_id)

    # Write out to disk
    for article in articles.select().execute():
        articlefile = os.path.join(articledir,
                                   slugify(article.title) + '.md')

        with open(articlefile, 'w') as f:
            f.write('title: ' + article.title + '\n')
            f.write('author: ' + article.mail + '\n')
            f.write('created: ' + to_date(article.created) + '\n')
            if article.created != article.changed:
                f.write('updated: ' + to_date(article.changed) + '\n')
            f.write('\n')
            f.write(to_markdown(article.body_value, article.body_format) + '\n')


def save_book(meta, directory, bookid):
    bookdir = subdir(directory)

    # Get tables
    node = meta.tables['node']
    users = meta.tables['users']
    field_body = meta.tables['field_data_body']
    book = meta.tables['book']
    menu_links = meta.tables['menu_links']

    # Do DB magic
    parent_ml = sa.sql.select(
        [menu_links.c.mlid, menu_links.c.link_title]
    ).alias('parent')
    menu_links = sa.sql.select([menu_links.c.plid, menu_links.c.mlid]
        ).alias('menu_links')
    menu_links = menu_links.join(
        parent_ml, menu_links.c.plid == parent_ml.c.mlid).alias('ml')

    bookpages = node.select(node.c.type == 'book').alias('bookpages')
    usersubset = sa.sql.select([users.c.uid, users.c.mail]).alias('userinfo')
    bookpages = bookpages.join(usersubset, bookpages.c.uid==usersubset.c.uid)
    bookpages = bookpages.join(
        field_body, bookpages.c.bookpages_nid==field_body.c.entity_id)
    bookpages = bookpages.join(book,
                               bookpages.c.bookpages_nid==book.c.nid)
    bookpages = bookpages.join(menu_links,
                             book.c.mlid==menu_links.c.menu_links_mlid)

    # Write out to disk
    for page in bookpages.select(book.c.bid==bookid).execute():
        fn = os.path.join(bookdir, slugify(page.title) + '.md')

        with open(fn, 'w') as f:
            f.write('title: ' + page.title + '\n')
            f.write('parent: ' + slugify(page.parent_link_title) + '\n')
            f.write('author: ' + page.mail + '\n')
            f.write('created: ' + to_date(page.created) + '\n')
            if page.created != page.changed:
                f.write('updated: ' + to_date(page.changed) + '\n')
            f.write('\n')
            f.write(to_markdown(page.body_value, page.body_format) + '\n')


def save_books(meta):
    node = meta.tables['node']
    book = meta.tables['book']

    # Books are top-level if nodeid (nid) == bookid (bid)
    for b in book.select(book.c.nid == book.c.bid).execute():
        n = node.select(node.c.nid == b.nid).execute().fetchone()

        # Defer to save_book function
        save_book(meta, slugify(n.title), b.bid)


def save_other(meta, directory='other'):
    otherdir = subdir(directory)

    # Get tables
    node = meta.tables['node']
    users = meta.tables['users']
    field_body = meta.tables['field_data_body']

    # Do DB magic
    pages = node.select(node.c.type == 'page').alias('pages')
    usersubset = sa.sql.select([users.c.uid, users.c.mail]).alias('userinfo')
    pages = pages.join(usersubset, pages.c.uid==usersubset.c.uid)
    pages = pages.join(field_body,
                       pages.c.pages_nid==field_body.c.entity_id)

    # Write out to disk
    for page in pages.select().execute():
        pagefile = os.path.join(otherdir,
                                slugify(page.title) + '.md')

        with open(pagefile, 'w') as f:
            f.write('title: ' + page.title + '\n')
            f.write('author: ' + page.mail + '\n')
            f.write('created: ' + to_date(page.created) + '\n')
            if page.created != page.changed:
                f.write('updated: ' + to_date(page.changed) + '\n')
            f.write('\n')
            f.write(to_markdown(page.body_value, page.body_format) + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: python convert.py "engine URL"'
        sys.exit()

    meta = sa.MetaData(sys.argv[1])
    meta.reflect()

    # Prep for output
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    # Save stuff
    save_articles(meta)
    save_users(meta)
    save_books(meta)
    save_other(meta)
