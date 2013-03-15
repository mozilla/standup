from standup.settings import *

TESTING = True

# This looks wrong, but actually, it's an in-memory db uri
# and it causes our tests to run super fast!
DATABASE_URL = 'sqlite://'
CSRF_DISABLE = True
