# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import validates
from cfb_survivor_pool.database import Column, PkModel, db, reference_col, relationship
from cfb_survivor_pool.extensions import bcrypt
from cfb_survivor_pool.public.models import Team, Game

class Role(PkModel):
    """A role for a user."""

    __tablename__ = "roles"
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="roles")

    def __init__(self, name, **kwargs):
        """Create instance."""
        super().__init__(name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"


class User(UserMixin, PkModel):
    """A user of the app."""

    __tablename__ = "users"
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    _password = Column("password", db.LargeBinary(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)
    entries = relationship("Entry", backref="creator")
    @hybrid_property
    def password(self):
        """Hashed password."""
        return self._password

    @password.setter
    def password(self, value):
        """Set password."""
        self._password = bcrypt.generate_password_hash(value)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self._password, value)

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User({self.username!r})>"


_entry_tablename = "entry"

class Pick(PkModel):
    ### TODO: needs triggers on entry scoring: 1. game is in the future. 2. team is playing in game
    __tablename__ = "pick"
    team_id = reference_col(Team.__tablename__, nullable=False)
    team = relationship("Team")
    game_id = reference_col(Game.__tablename__, nullable=False)
    created = db.Column(db.DateTime, nullable=False)
    game = relationship("Game")
    entry_id = reference_col(_entry_tablename, nullable=False)
    def __init__(self, team, game, entry, created=None):
        self.team_id = team.id
        self.game_id = game.id
        if created is not None:
            self.created = created
        else:
            self.created = dt.datetime.utcnow()
        assert self.created < game.start_date, "Cannot set pick after game start"
        assert self.team_id == game.away_id or self.team_id == game.home_id, "Team must be playing in game"
        for pick in entry.picks:
            assert pick.id != self.id, "Cannot pick same team and week"
            assert pick.team_id != self.team_id, "Teams must be exclusively selected"
            assert pick.game.saturday != self.game.saturday, "Picks must be on separate weeks"
        self.entry_id = entry.id

    def __repr__(self):
        return f"<Pick {self.team, self.game.saturday, self.is_correct, self.created, self.game.away_team, self.game.home_team}>"
    @hybrid_property
    def is_correct(self):
        if self.game.away_points is None or self.game.home_points is None:
            return None
        elif self.game.away_points > self.game.home_points:
            return self.team == self.game.away_team
        else:
            return self.team == self.game.home_team
    @hybrid_method
    def score(self, intra_conference_score, inter_conference_score):
        if self.game.away_id != self.team_id and self.game.home_id != self.team_id:
            return 0 ### Invalid team: no score
        if self.created > self.game.start_date:
            return 0 ### Cannot set pick after game start, set no score
        if self.is_correct is not None and self.is_correct:
            if self.game.conference_game:
                return intra_conference_score
            else:
                return inter_conference_score
        else:
            return 0

class Entry(PkModel):
    #### TODO: Enforce (1) that teams are only chosen once, and (2) that weeks are only chosen once
    __tablename__ = _entry_tablename
    name = Column(db.String(80), nullable=False)
    creator_id = reference_col(User.__tablename__, nullable=False)
    ### pools = relationship("Pool", backref="entries")
    picks = relationship("Pick", backref="entry")
    created = db.Column(db.DateTime, nullable=False)
    def __init__(self, name, creator, created=None):
        self.name = name
        self.creator_id = creator.id
        if created is not None:
            self.created = created
        else:
            self.created = dt.datetime.utcnow()
    def __repr__(self):
        return f"<Entry {self.name, self.creator_id}>"
    @hybrid_property
    def score(self, intra_conference_score, inter_conference_score):
        total = 0
        for pick in self.picks:
            total += self.picks.score(intra_conference_score=intra_conference_score,
                                      inter_conference_score=inter_conference_score)
        return total
    @hybrid_property
    def last_updated(self):
        lu = self.created
        for pick in self.picks:
            lu = max(lu, pick.created)
        return lu
### For Pool, enforce that all teams chosen are in the same conference
# class Pool(PkModel):
#     name = Column(db.String(80), unique=True, nullable=False)
#     conference = Column(db.String(80), nullable=False)
#     year = Column(db.Integer, nullable=False, default=dt.datetime.utcnow().year)
#     intra_score = Column(db.Integer, nullable=False, default=5)
#     inter_score = Column(db.Integer, nullable=False, default=1)
#     creator = reference_col("users", nullable=True)
#     def __init__(self, name, conference):
