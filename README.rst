========
 README
========

standup is an app that logs daily status updates.
It is currently in super early active development, check back later.

We developed it with the following priorities:

1. Lets the team, stake holders and everyone else see status for team
   members across projects.

2. Lets us do that asynchronously. Conference calls were getting
   difficult to schedule because of the range of timezones we're in.

3. Lets us see who's blocked on what---then scrummasters can go
   through and work to unblock people.


Hacking
=======

To set up a local dev environment for hacking:

1. Create and activate a new virtual environment.
2. Clone the repo::

    $ git clone git://github.com/rlr/standup.git
    $ cd standup

3. Install required dependencies::

    $ pip install -r requirements.txt

4. Configure::

    $ cp ./standup/local_settings.py-dist ./standup/local_settings.py
    $ vim ./standup/local_settings.py

5. Create the database using::

    $ ./manage.py db_create

6. Run the app::

    $ ./manage.py runserver


Oh, but wait--what can you do with it? Well, for testing purposes, you
can use the included ``scripts/standup-cmd`` which is a command-line
tool you can use to create statuses.

Example::

    $ ./scripts/standup-cmd localhost:5000 ou812 willkg sumo "hi!"

(This assumes your ``API_KEY`` is set to ou812.)

Also, you can use the ``./manage.py`` script to add teams::

    $ ./manage.py add_team "Team Awesome"
    $ ./manage.py add_team -s "awesome" "Team Awesome"

and projects::

    $ ./manage.py add_project "DEATH MARCH"
    $ ./manage.py add_project -s "death_march" "DEATH MARCH"
    $ ./manage.py add_project -r "http://github.com/rlr/standups" "DEATH MARCH"
    $ ./manage.py add_project -c "0000ff" "DEATH MARCH"

And see stats for your instance::

    $ ./manage.py stats


Migrations
==========

To upgrade the database use::

  $ ./manage.py db_upgrade

You may optionally pass a version that you wish to upgrade to::

  $ ./manage.py db_upgrade 8

If you wish to downgrade, you must specify what version to downgrade to::

  $ ./manage.py db_downgrade 4

Finally you can check the current version of the database by using::

  $ ./manage.py db_version

Configuration
=============

There's a ``standup/local_settings.py-dist`` template which you can copy
to ``standup/local_settings.py`` to start you off.

These are things you can set in ``standup/local_settings.py``:

    SITE_URL
        The url for your site.

        For example, if you're running on your local machine, it would be::

            SITE_URL = 'http://127.0.0.1:5000'

        You have to set this in production, but a default (the above) is
        supplied for ease-of-development.

    SESSION_SECRET
        Secret string used for creating session variables. This can be
        any string.

        For example::

            SESSION_SECRET = '1234'

        You have to set this in production, but a default (the above) is
        supplied for ease-of-development.

    API_KEY
        The key used for using the API. You use this for the standup-irc
        bot as well as the standup-cli.

        Defaults to something ridiculous.

    DEBUG
        Either ``True`` or ``False``. Determines whether it prints lots of
        stuff to the console and whether errors get a debugging-friendly
        error page.

        Defaults to ``False``.

These are things you can set in the environment when you launch standup:

    DATABASE_URL
        The uri to use for the database.

        Defaults to ``sqlite:///standup_app.db``.


Testing
=======

We use nose for testing. To run the tests, do::

    $ nosetests
