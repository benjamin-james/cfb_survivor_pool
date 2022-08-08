# -*- coding: utf-8 -*-
"""CFBD models."""
from datetime import datetime

from cfb_survivor_pool.database import Column, PkModel, db, reference_col, relationship
from cfb_survivor_pool.cfbd_parser import saturday_of
from sqlalchemy.orm import backref
from sqlalchemy.ext.hybrid import hybrid_property
_team_tablename = "team"

class Game(PkModel):
    __tablename__ = "game"
    away_id = reference_col(_team_tablename, nullable=False)
    home_id = reference_col(_team_tablename, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    conference_game = db.Column(db.Boolean, nullable=False, default=False)
    neutral_site = db.Column(db.Boolean, nullable=False, default=False)
    season = db.Column(db.Integer, nullable=False, default=datetime.utcnow().year)
    week = db.Column(db.String(50), nullable=False)
    season_type = db.Column(db.String(50), nullable=False, default="regular")
    venue = db.Column(db.String(100), nullable=False)
    away_points = db.Column(db.Integer, nullable=True)
    home_points = db.Column(db.Integer, nullable=True)

    def __init__(self, game_id, away_id, home_id,
                 start_date,
                 conference_game, neutral_site, season,
                 week, season_type, venue, away_points=None, home_points=None):
        super().__init__(id=game_id)
        self.away_id = away_id
        self.home_id = home_id
        self.start_date = start_date
        self.conference_game = conference_game
        self.neutral_site = neutral_site
        self.season = season
        self.week = week
        self.season_type = season_type
        self.venue = venue
        if away_points is not None and home_points is not None:
            ### only makes sense if both are set
            self.away_points = away_points
            self.home_points = home_points
    def __repr__(self):
        return "<Game %d>" % self.id
    @hybrid_property
    def saturday(self):
        return saturday_of(self.start_date)

class Team(PkModel):
    __tablename__ = _team_tablename
    abbreviation = db.Column(db.String(10), nullable=False)
    alt_color = db.Column(db.String(10), nullable=True)
    classification = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(10), nullable=False)
    conference = db.Column(db.String(50), nullable=False)
    # team_id = db.Column(db.Integer, unique=True, nullable=False)
    logo = db.Column(db.String(200), nullable=False)
    mascot = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(50), nullable=False)
    away_games = relationship("Game", backref="away_team", foreign_keys=Game.away_id)
    home_games = relationship("Game", backref="home_team", foreign_keys=Game.home_id)
    def __init__(self, team_id, abbreviation, classification, color, conference, logo, mascot, school, alt_color=None):
        super().__init__(id=team_id)
        self.abbreviation = abbreviation
        self.classification = classification
        self.conference = conference
        self.logo = logo
        self.mascot = mascot
        self.school = school
        self.color = color
        if alt_color is not None:
            self.alt_color = alt_color
    def __repr__(self):
        return "<Team %r>" % self.abbreviation
