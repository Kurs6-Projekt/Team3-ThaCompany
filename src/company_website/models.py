from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, password_hash, first_name=None, last_name=None,
                 email=None, about=None, role=None, internal_notes=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.about = about
        self.role = role
        self.internal_notes = internal_notes
