#!/usr/bin/env python
import os
from migrate.versioning.shell import main

db_url = os.environ.get('DATABASE_URL', 'sqlite:///standup_app.db')

if __name__ == '__main__':
    main(url=db_url, repository='migrations')
