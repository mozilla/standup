#!/usr/bin/env python
import os
from migrate.versioning.shell import main

db_url = os.environ.get('DATABASE_URL', 'sqlite:///standup_app.db')
repo_path = os.path.dirname(os.path.abspath(__file__))
repository = os.path.join(repo_path, './migrations')

if __name__ == '__main__':
    print repo_path
    main(url=db_url, repository=repository)
