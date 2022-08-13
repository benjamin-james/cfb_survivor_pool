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
    weeks = []
    wflist = []
    form = EntryForm()
    for sat in sorted(list(set([g.saturday for g in all_games]))):
        wf = WeekForm()
        wteams = set()
        wtg = {}
        for g in all_games:
            if g.saturday == sat and g.away_team.conference == conference:
                wteams.add(g.away_team)
                wtg[g.away_team] = g
            if g.saturday == sat and g.home_team.conference == conference:
                wteams.add(g.home_team)
                wtg[g.home_team] = g
        wteams = list(wteams)
        oteams = [wtg[t].away_team if wtg[t].home_team == t else wtg[t].home_team for t in wteams]
        teams.update(wteams)
        wf.teams.choices = [(t.school, ot.logo) for t, ot in zip(wteams, oteams)]
        wf.teams.name = sat2str(sat)
        wf.teams.render_kw = {"class": "form-check-input"}
        wf.teams.disabled = [now >= wtg[t].start_date for t in wteams]
        wf.teams.selected = wteams[0]
        wf.teams.td_class = ["" if wtg[t].conference_game else "table-secondary"  for t in wteams]
        wflist.append(wf)
        weeks.append(sat2str(sat))
    form.weeks = wflist
    context = {"form": form, "teams": sorted(list(teams), key=lambda x: x.school), "weeks": weeks}
    if form.validate_on_submit():
        flash("validated! %s" % str(dt.datetime.now()))
        # for wk in form.weeks:
        #     flash("form:", wk.teams)
        ### todo: add items to DB
    return render_template("users/create_entry.html", **context)
