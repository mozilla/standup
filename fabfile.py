from fabric.api import env, local

env.hosts = ['localhost']

def npm_install():
    """Correctly runs npm install"""
    local('cp node.json package.json')
    local('npm install')
    local('rm package.json')
