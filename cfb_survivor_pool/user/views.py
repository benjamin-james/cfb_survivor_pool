# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, flash, redirect, request
from flask_login import login_required, current_user
from cfb_survivor_pool.user.models import User, Entry, Pick
from cfb_survivor_pool.public.models import Game, Team
from cfb_survivor_pool.user.forms import EntryForm, WeekForm, CreateEntryForm
blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")
from cfb_survivor_pool.extensions import db, login_manager
import datetime as dt
from sqlalchemy import and_, or_
import json
import base64
sat2str = lambda x: "Week of %d/%d" % (x.month, x.day)
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/members")
@login_required
def members():
    """List members."""
    me = load_user(current_user.id)
    all_users = db.session.query(User).all()
    return render_template("users/members.html", user_id=[u.username for u in all_users])

@blueprint.route("/")
@login_required
def home():
#    clear_entries_for_id(current_user.id)
    return redirect("/users/entries")

@blueprint.route("/entries", methods=["GET", "POST"])
@login_required
def list_entries():
    """List entries."""
    ### TODO: link to standings; buttons for editing and deletion; name editing
    me = load_user(current_user.id)
    all_entries = [u for u in me.entries]
    conferences = [x[0] for x in db.session.query(Team.conference).distinct()]
    cef = CreateEntryForm()
    cef.conference.choices = conferences
    if request.method == "POST" and cef.validate_on_submit():
        if request.form.get("entry_create"):
            now = dt.datetime.utcnow()
            conference = cef.conference.data
            entry_name = cef.entry_name.data
            ent = Entry(name=entry_name, creator=current_user, conference=conference, year=now.year, created=now)
            db.session.add(ent)
            db.session.commit()
            return redirect("/users/edit_entry/%d" % ent.id)
        else:
            flash("Unknown button pressed")
            return render_template("users/entries.html", entries=all_entries, form=cef)
    else:
        return render_template("users/entries.html", entries=all_entries, form=cef)

def get_entry_selected(teams, team2game, week, entry=None):
    """From an Entry object, select the team playing in a certain week"""
    if entry is None:
        return teams[0]
    for pick in entry.picks:
        if sat2str(pick.game.saturday) == sat2str(week):
            for team in teams:
                if pick.team == team and team2game[team] == pick.game:
                    return team.school
    return None

def _entry_form(conference, now, entry=None):
    form = EntryForm()
    """Complete the WTForm in a renderable format"""
    all_games = Game.query.join(Game.away_team,
                                Game.home_team,
                                aliased=True).filter(and_(Game.season == now.year,
                                                          or_(Game.away_team.has(conference=conference),
                                                              Game.home_team.has(conference=conference)))).all()
    teams = set() ## list of conference teams
    weeks = [] ## list of saturday strings
    wflist = [] ## list of weekform
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
        sel = get_entry_selected(teams=wteams, team2game=wtg, week=sat, entry=entry)
        if sel is not None:
            wf.teams.selected = sel
        wf.teams.td_class = ["" if wtg[t].conference_game else "table-secondary"  for t in wteams]
        wflist.append(wf)
        weeks.append(sat2str(sat))
    form.weeks = wflist
    context = {"form": form, "teams": sorted(list(teams), key=lambda x: x.school), "weeks": weeks}
    return context

def clear_entries_for_id(id):
    entries = db.session.query(Entry).filter(Entry.creator_id == id).all()
    for e in entries:
        db.session.delete(e)
    db.session.commit()
    return 0

def form2entry(form, now, weeks, teams, entry):
    all_picks = entry.picks
    to_change = [{} for _ in all_picks]
    pick_keep = [False for _ in all_picks]
    to_add = []
    ### conditions:
    ### 1. pick is same (pick_keep is True)
    ### 2. pick is changed or added (pick_keep is False, to_add is nonempty)
    ### 3. pick is deleted (pick_keep is False, to_add is empty)
    for week in weeks:
        school = form.get(week)
        if school is not None:
            team_list = db.session.query(Team).filter(Team.school == school).all()
            if len(team_list) != 1:
                flash("Team list for week %s is: [%s]" % (week, ", ".join(team_list)))
                break
            ### get game for week with team
            games = db.session.query(Game).filter(or_(Game.away_id == team_list[0].id,
                                                      Game.home_id == team_list[0].id))
            games = [g for g in games if sat2str(g.saturday) == week]
            if len(games) != 1:
                flash("Games for team %s in week %s is: [%s]" % (team_list[0], week, ", ".join(games)))
                break
            is_changed = False
            for i, pick in enumerate(all_picks):
                if sat2str(pick.game.saturday) == week:
                    ### determine if this pick is the pick of the week
                    pick_keep[i] = pick.team == team_list[0]
                    to_change[i] = {"team": team_list[0], "game": games[0]}
                    # if to_change[i]:
                    #     flash({"team": to_change[i]["team"].school, "week": to_change[i]["game"].saturday})
                    is_changed = True
            if not is_changed:
                to_add.append({"team": team_list[0], "game": games[0]})
    else:
        for i, pick in enumerate(all_picks):
            if not pick_keep[i]:
                db.session.delete(pick)
        db.session.commit()
        for pkeep, params in zip(pick_keep, to_change):
            if (not pkeep) and params:
                try:
                    pk = Pick(entry=entry, created=now, **params)
                    db.session.add(pk)
                except AssertionError:
                    print("Error in adding pick %s %s to the database" % (sat2str(params["game"].saturday),
                                                                          params["team"]))
                    flash("Error in adding pick %s %s to the database" % (sat2str(params["game"].saturday),
                                                                          params["team"]))
                    break
        for params in to_add:
            try:
                pk = Pick(entry=entry, created=now, **params)
                db.session.add(pk)
            except AssertionError:
                print("Error in adding pick %s %s to the database" % (sat2str(params["game"].saturday),
                                                                      params["team"]))
                flash("Error in adding pick %s %s to the database" % (sat2str(params["game"].saturday),
                                                                      params["team"]))
                break
        db.session.commit()
#        flash([(p.team.school, sat2str(p.game.saturday)) for p in entry.picks])
        return redirect("/users/")
    print("Entry was not added")
    # db.session.delete(entry)
    # db.session.commit()
    flash("Entry was not edited.")
    return redirect("/users/")

@blueprint.route("/edit_entry/<entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    """Edit an already filled-in entry."""
    elist = db.session.query(Entry).filter(and_(Entry.id == entry_id,
                                                Entry.creator_id == current_user.id)).all()
    if len(elist) != 1:
        flash("No entry with id %s for this user" % entry_id)
        return redirect("/users/")
    entry = elist[0]
    now = dt.datetime.utcnow()
    context = _entry_form(conference=entry.conference, now=now, entry=entry)
    form = context["form"]
    if form.validate_on_submit():
        flash("validated! %s" % str(dt.datetime.now()))
        context["form"] = request.form
        return form2entry(entry=entry, now=now, **context)
    else:
        return render_template("users/create_entry.html", **context)
