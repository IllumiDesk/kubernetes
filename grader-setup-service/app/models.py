import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()


class GraderService(db.Model):
    __tablename__ = 'grader_services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    course_id = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    oauth_no_confirm = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=True)
    api_token = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return "<Service name: {} at {}>".format(self.name, self.url)
