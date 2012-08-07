#!/usr/bin/env python
import os
from migrate.versioning.shell import main

app_path = os.path.relpath(os.path.dirname(os.path.abspath(__file__)),
                           os.getcwd())
sqlite = os.path.join(app_path, 'standup_app.db')
repository = os.path.join(app_path, 'migrations')
db_url = os.environ.get('DATABASE_URL', 'sqlite:///%s' % sqlite)

if __name__ == '__main__':
    main(url=db_url, repository=repository)