import os
from repository import app, db
from repository.models import User, Role, Institution

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'Institution': Institution}

if __name__ == '__main__':
    # app.run()
    app.run(ssl_context='adhoc')
