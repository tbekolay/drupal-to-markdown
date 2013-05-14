Convert a Drupal 7 site to Markdown files
=========================================

We had a big, clunky Drupal 7 site with lots of content
that we wanted to migrate to a site
generated with a Python static site generator.
This repository contains a Python script
that converts the data in a Drupal 7 site
to a set of Markdown pages organized in various directories.

I made this to fit with what content we had,
and what our desired output format was.
A lot of this (node handling, for example)
will work in the general case,
but the more customized your Drupal site,
the more you'll need to know what tables contain
the data you need.
The functions in this repository should form
a good template for you to make your own
functions to extract the data you want.

Here's how to get this working:

1. Dump the Drupal database using the
   [Backup and Migrate module](http://drupal.org/project/backup_migrate).
   This may work with raw database dumps, but this is how I did it.
2. Make a local copy of the Drupal database by installing mysql server
   and loading the database dump with
     ```mysql.server start
     mysql -u root
     mysql> CREATE DATABASE drupal;
     mysql> exit
     mysql -u root drupal < /path/to/file.mysql
     ```
3. Install the dependencies: SQLAlchemy, mysql-python, and html2text.
   `pip install SQLAlchemy mysql-python html2text`.
4. Run `convert.py` and provide a string  pointing to the Drupal database
   (see
   [SQLAlchemy docs](http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#mysql)).
   E.g., `python convert.py "mysql://root@localhost/drupal"`
5. Your content should now be in the `content` directory.

Feel free to use this code for whatever;
it's [MIT licensed](http://tbekolay.mit-license.org/).
