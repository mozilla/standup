from wtforms import Form, HiddenField, TextField, validators


class ProfileForm(Form):
    email = HiddenField('E-mail', validators=[validators.required()])
    name = TextField('Name', validators=[validators.required()])
    username = TextField('IRC Handle', validators=[validators.required()])
    github_handle = TextField('GitHub Handle')
