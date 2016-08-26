======
README
======

STATUS: August 26th, 2016
=========================

This is currently undergoing a django rewrite of the original app. It's pretty
far from complete.


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

See ``standup/settings.py`` for settings you can define in the
environment.


Testing
=======

We use pytest for testing. To run the tests, do::

  $ make test

Remember to run tests before submitting pull requests!


To run on Heroku
================

1. Create a heroku app::

     heroku apps:create myapp

2. Push the code::

     git push heroku master

3. Set up required environment variables::

     heroku config:set SECRET_KEY=<KEYHERE>
     heroku config:set ALLOWED_HOSTS=<HEROKU_HOST_HERE>

   You can see other variables you can set in the environment in
   ``standup/settings.py``.

4. You should be all set!
