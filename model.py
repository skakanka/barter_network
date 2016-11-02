"""Models and database functions for Barter Network."""

from flask_sqlalchemy import SQLAlchemy
import datetime
import bcrypt

db = SQLAlchemy()

#fake app for now, not connected to server.py yet
# app = Flask(__name__)

#######################
# Model definitions and relationships


class User(db.Model):
    """User of Barter Circle"""

    __tablename__ = "users"


    # for networkx and node building 
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_fname = db.Column(db.String(150), nullable=False)
    user_lname = db.Column(db.String(150), nullable=True)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    # future features
    user_street_address = db.Column(db.String(150), nullable=True)
    user_city = db.Column(db.String(64), nullable=True)
    user_state = db.Column(db.String(2), nullable=True)
    user_zipcode = db.Column(db.String(15), nullable=True)
    user_dob = db.Column(db.DateTime, nullable=True) # TODO date of birth
    user_occupation = db.Column(db.String(62), nullable=True)


    # for site log in
    user_email = db.Column(db.String(64), unique=True, nullable=True)
    user_password = db.Column(db.String(64), nullable=True)
 





    def __repr__(self):
        """User repr when printed"""

        return "<User user_id=%s user_fname=%s user_email=%s user_password=%s>" % \
                (self.user_id, 
                    self.user_fname, 
                    self.user_email, 
                    self.user_password)

class UserSkill(db.Model): # TODO UserSkill
    """Users and skills direction of Barter Network"""

    __tablename__ = "userskills"

    userskill_id = db.Column(db.String, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.skill_id'), nullable=False)
    # skill_direction = db.Column(db.String(4), nullable=False)

    # define relationship to user
    user = db.relationship('User', backref=db.backref('userskills'))

    # define relationship to skill
    skill = db.relationship('SkillDirection', backref=db.backref('userskills'))



    def __repr__(self):
        """Userskill repr when printed"""
        return "<Userskill userskill_id=%s user_id=%s skill_id=%s skill_direction=%s>" % \
        (self.userskill_id, self.user_id, self.skill_id, self.skill_direction)


class SkillDirection(db.Model):
    """Skill of Barter Network"""

    __tablename__ = "skills"

    skill_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    skill_name = db.Column(db.String(64), nullable=False)
    skill_value = db.Column(db.Integer, nullable=True) #  for future feature, to use weight attribute for edge, quantify the need for a skill
    skill_direction = db.Column(db.String(4), nullable=False)

    def __repr__(self):
        """Skill repr when printed"""

        return "<Skill skill_id=%s skill_name=%s skill_value=%s>" %(self.skill_id, self.skill_name, self.skill_value)




################################
# Helper functions

def connect_to_db(app):
    """Connect datatbase to Flask app"""

    # configure PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///barternet'
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    from server import app
    connect_to_db(app)
    # db.create_all()
    print "Connected to barternet"
