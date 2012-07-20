========
 README
========

standup is an app to log daily status updates.
It is currently in super early active development, check back later.

We developed it with the following priorities:

1. Let's the team, stake holders and everyone else see status for team
   members across projects.

2. Let's us do that asynchronously. Conference calls were getting
   difficult to schedule because of the range of timezones we're in.

3. Let's us see who's blocked on what---then scrummasters can go
   through and work to unblock people.


Hacking
=======

To setup a local dev environment for hacking::

1. Create and activate a new virtual environment.
2. Clone the repo::

    $ git clone git://github.com/rlr/standup.git
    $ cd standup

3. Install required dependencies::

    $ pip install -r requirements.txt

4. Run the app::

    $ python app.py
