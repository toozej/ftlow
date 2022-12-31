#!/usr/bin/env python2
"""
    For The Love of Wine (FTLOW)
    ~~~~~~

    A quick and dirty wine rating application based (heavily) off the 
    Flaskr Flask example by Armin Ronacher and sqlite3

    :copyright: (c) 2013 by James Tooze.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, Response
from flask_bcrypt import Bcrypt
import os, sys
import StringIO
import flickr
import urllib, urlparse


# create our little application :)
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.from_pyfile('settings.py')



""" Begin Database functions """
def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'],
                check_same_thread = False)
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
        for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv



""" functions dealing with users in DB """

def get_user(name):
    user = query_db('select * from users where username = ?', 
            [name], one=True)
    if user is None:
        return None
    else:
        return user['username']


def get_username(user_id):
    username = query_db('select username from users where id = ?',
            [user_id], one=True)
    return username['username']


def match_password(name, password):
    password_hash = query_db('select password from users where username = ?',
            [name], one=True)
    return bcrypt.check_password_hash(password_hash['password'], password)



""" Begin views """

@app.route('/index', endpoint='show_landing_page-alternative')
@app.route('/')
def show_landing_page():
    return render_template('index.html')


@app.route('/drink')
def show_entries_drink():
    if not session.get('logged_in'):
        error = "Please login or create an account"
        return render_template('login.html', error=error)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        cur = db.execute('select id, winery, location, vintage, style, vineyard, drank from entries where drank=? and username=? order by winery asc', ('0', user_name))
        entries = cur.fetchall()
        for entry in entries:
            get_photo_drink(entry[0])
            #os.remove('static/' + str(entry[0]) + '.jpg')
        cur.close()
        return render_template('show_drink.html', entries=entries, user_name=user_name)


@app.route('/static/<int:entry_id>.jpg')
def get_photo_drink(entry_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        db = get_db()
        cur = db.execute('select photo from entries where id=' + str(entry_id))
        ablob = cur.fetchone()
        cur.close()
        return Response(ablob[0])
        

@app.route('/drank')
def show_entries_drank():
    db = get_db()
    cur = db.execute('select winery, location, vintage, style, vineyard, rating, thoughts, flavours, drank, id from entries where drank=? order by winery asc', '1')
    entries = cur.fetchall()

    cur.close()
    return render_template('show_drank.html', entries=entries)



""" Begin adding entries """

@app.route('/drank/add', methods=['POST'])
def add_entry_drank():
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        db.execute('insert into entries (winery, location, vintage, style, vineyard, rating, thoughts, flavours, drank, username) values (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)',
                 [request.form['winery'], request.form['location'], request.form['vintage'], request.form['style'], request.form['vineyard'], request.form['rating'], request.form['thoughts'], request.form['flavours'], user_name])
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries_drank'))


@app.route('/drink/add', methods=['POST'])
def add_entry_drink():
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        tag = 'creativecommons'
        text = request.form['winery'] + ' ' + request.form['style']
        print 'Searching for: ', text
        photos = flickr.photos_search(text=text, tags=tag)
        urllist = [] #store a list of what was downloaded
        path = ''
        if not photos:
            photo = open("static/default.jpg", "rb").read()
            photobin = sqlite3.Binary(photo)
        else:
            flash('Downloading image, please be patient')
            url = photos[0].getURL(size='Medium', urlType='source')
            urllist.append(url)
            path = os.path.basename(urlparse.urlparse(url).path)
            photo = urllib.URLopener().retrieve(url, path)
            print 'downloading: ', url
            file, mime = urllib.urlretrieve(url)
            photo = open(file, "rb").read()
            photobin = sqlite3.Binary(photo)

        db = get_db()
        db.execute('insert into entries (winery, location, vintage, style, vineyard, drank, username, photo) values (?, ?, ?, ?, ?, 0, ?, ?)', [request.form['winery'], request.form['location'], request.form['vintage'], request.form['style'], request.form['vineyard'], user_name, photobin])
        db.commit()
        if (path):
            print 'removing photo at: ', path
            os.remove(path)
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries_drink'))


@app.route('/drank/remove/<int:entry_id>')
def remove_entry_drank(entry_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        db.execute('delete from entries where id =' + str(entry_id))
        db.commit()
        flash('Entry was successfully removed')
        return redirect(url_for('show_entries_drank'))


@app.route('/drink/remove/<int:entry_id>')
def remove_entry_drink(entry_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        db.execute('delete from entries where id =' + str(entry_id))
        db.commit()
        flash('Entry was successfully removed')
        return redirect(url_for('show_entries_drink'))


@app.route('/drank/move/<int:entry_id>')
def move_entry_drank(entry_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        db.execute('update entries set drank=0 where id =' + str(entry_id))
        db.commit()
        flash('Entry was successfully moved to Drink')
        return redirect(url_for('show_entries_drink'))


@app.route('/drink/move/<int:entry_id>')
def move_entry_drink(entry_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        user_id = session['user_id']
        user_name = get_username(user_id)
        db = get_db()
        db.execute('update entries set drank=1 where id =' + str(entry_id))
        db.commit()
        flash('Entry was successfully moved to Drank')
        return redirect(url_for('show_entries_drank'))


""" Begin login/logout/register """

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if get_user(request.form['username']) is None:
            error = 'Please register'
        elif not match_password(request.form['username'], request.form['password']):
            error = 'Invalid password, try again'
        else:
            user = query_db('select id from users where username = ?', [request.form['username']], one=True)
            session['logged_in'] = True
            session['user_id'] = user['id']
            flash('You were logged in')
            return redirect(url_for('show_entries_drank'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries_drank'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    db = get_db()
    if request.method == 'POST' and not get_user(request.form['username']):
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        db.execute('insert into users (username, password) values (?, ?)',
                    [request.form['username'], pw_hash])
        db.commit()
        return redirect(url_for('login'))
    elif request.method == 'POST':
        error = "Username has already been taken"
        return render_template('login.html', error=error)
    return render_template('login.html')



""" Begin custom error pages """

@app.errorhandler(401)
def page_unauthorized(e):
    return render_template('401.html'), 401

@app.errorhandler(403)
def page_forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_server_error(e):
    return render_template('500.html'), 500 



""" main """

if __name__ == '__main__':
    try:
        with open('ftlow.db'):
            app.run(host='0.0.0.0')
    except IOError as e:
        init_db()
        app.run(host='0.0.0.0')
