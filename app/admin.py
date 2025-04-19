
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()

# Define models for each table
class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String)
    value = db.Column(db.String)
    description = db.Column(db.String)

class FinalizedDetail(db.Model):
    __tablename__ = 'finalized_details'
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String)
    details = db.Column(db.String)

class CharacterInspiration(db.Model):
    __tablename__ = 'character_inspirations'
    id = db.Column(db.Integer, primary_key=True)
    theme = db.Column(db.String)
    setting = db.Column(db.String)
    traits = db.Column(db.String)

def init_admin(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/databases/preferences.db'
    app.config['SQLALCHEMY_BINDS'] = {
        'details': 'sqlite:///data/databases/details.db',
        'characters': 'sqlite:///data/databases/characters.db'
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    admin = Admin(app, name='Database Admin', template_mode='bootstrap3')
    
    # Add views
    admin.add_view(ModelView(UserPreference, db.session))
    admin.add_view(ModelView(FinalizedDetail, db.session))
    admin.add_view(ModelView(CharacterInspiration, db.session))
