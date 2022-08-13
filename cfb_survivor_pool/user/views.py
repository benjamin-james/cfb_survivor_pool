# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from cfb_survivor_pool.user.models import User, Entry
from cfb_survivor_pool.public.models import Game, Team
from cfb_survivor_pool.user.forms import EntryForm, WeekForm
blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")
from cfb_survivor_pool.extensions import db, login_manager
import datetime as dt
from sqlalchemy import and_, or_
import json
import base64
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/")
@login_required
def members():
    """List members."""
    me = load_user(current_user.id)
    all_users = db.session.query(User).all()
    return render_template("users/members.html", user_id=[u.username for u in all_users])

@blueprint.route("/entry")
@login_required
def entries():
    """List entries by user."""
    me = load_user(current_user.id)
    return render_template("users/members.html", user_id=[u.created for u in me.entries])

@blueprint.route("/create_entry/<conference>/<year>/<month>/<day>/", methods=["GET", "POST"])
@login_required
def create_entry(conference="Big Ten", year=2022, month=8, day=10):
    """strategy: recreate /schedule piece by piece"""
    if type(year) == str and year.isnumeric():
        year = int(year)
    if type(month) == str and month.isnumeric():
        month = int(month)
    if type(day) == str and day.isnumeric():
        day = int(day)
    now = dt.datetime(year=year, month=month, day=day)
    me = load_user(current_user.id)
    all_games = Game.query.join(Game.away_team,
                                Game.home_team,
                                aliased=True).filter(and_(Game.season == now.year,
                                                          or_(Game.away_team.has(conference=conference),
                                                              Game.home_team.has(conference=conference)))).all()
    sat2str = lambda x: "Week of %d/%d" % (x.month, x.day)
    grid = {}
    teams = set()
    weeks = set([g.saturday for g in all_games])
    # for sat in set([g.saturday for g in all_games]):
    #     wf = WeekForm()
    #     wteams = set()
    #     for g in all_games:
    #         if g.saturday == sat and g.away_team.conference == conference:
    #             wteams.add(g.away_team)
    #         if g.saturday == sat and g.home_team.conference == conference:
    #             wteams.add(g.home_team)
    #     wteams = sorted(list(wteams))
    #     teams.update(wteams)
    #     wf.teams.choices = [(t.school, t.logo) for t in wteams]
    #     wf.teams.name = sat2str(sat)
    #     wf.teams.render_kw = {"data-col": [t.school for t in wteams],
    #                           "aria-label": "%s %s" % (g.away_team.school, sat2str(g.saturday)),
    #                           "class": "form-check-input",
    #                           "disabled": False}
    weeks = []
    form = EntryForm()
    ### todo: get default items from DB (entry.get by id
    for g in all_games:
        ws = sat2str(g.saturday)
        wf = WeekForm()
        wf.teams.choices = [(g.away_team.school, g.away_team.logo), (g.home_team.school, g.home_team.logo)]
        wf.teams.name = sat2str(g.saturday)
        wf.teams.render_kw = {
            # "selected": str(g.home_team.school),
            "class": "form-check-input",
#            "disabled": now > g.start_
        }
        wf.teams.disabled = [now >= g.start_date, now >= g.start_date]
        wf.teams.selected = g.home_team.school
        if g.conference_game:
            wf.teams.render_kw["data-td-class"] = ""
        else:
            wf.teams.render_kw["data-td-class"] = "table-secondary"
        if len(weeks) < 12:
            weeks.append(wf)
            print("teams:", vars(wf.teams))
    form.weeks = weeks
    context = {"form": form}
    if form.validate_on_submit():
        flash("validated! %s" % str(dt.datetime.now()))
        # for wk in form.weeks:
        #     flash("form:", wk.teams)
        ### todo: add items to DB
    return render_template("users/create_entry.html", **context)
