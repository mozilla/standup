======
README
======

Summary
=======

standup is an app that logs daily status updates.
It is in perpetual Beta which is to say that it probably has bugs and you
shouldn't bet a million dollars on it.

We developed it with the following priorities:

1. Lets the team, stake holders and everyone else see status for team
   members across projects.

2. Lets us do that asynchronously. Conference calls were getting
   difficult to schedule because of the range of timezones we're in.

3. Lets us see who's blocked on what---then scrummasters can go
   through and work to unblock people.


Years passed. It was cool, then time passed and it bitrotted and in that
time we discovered we had various needs and Persona was dying. So a small
elite group of us rewrote it in Django.


Hacking
=======

To set up a local dev environment for hacking:

1. Clone the repo::

     $ git clone git://github.com/mozilla/standup.git
     $ cd standup

2. Configure.

3. Run::

     $ make run


Then connect to it at http://localhost:8000/ .

Oh, but wait--what can you do with it? Well, for testing purposes, you
can use the included ``bin/standup-cmd`` which is a command-line
tool you can use to create statuses.

Example::

  $ ./bin/standup-cmd localhost:8000 ou812 willkg sumo "hi."


Configuration
=============

FIXME: This is all wrong

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

    API2_TIMELINES_MAX_RESULTS
        Sets the maximum number of results that can be requested from the
        timeline endpoints of the API (v2).

        Defaults to 800.

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

We use pytest for testing. To run the tests, do::

  $ make test

Remember to run tests before submitting pull requests!
