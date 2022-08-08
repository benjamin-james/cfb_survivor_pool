# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user

from cfb_survivor_pool.extensions import login_manager, db
from cfb_survivor_pool.public.forms import LoginForm
from cfb_survivor_pool.public.models import Team, Game
from cfb_survivor_pool.user.forms import RegisterForm
from cfb_survivor_pool.user.models import User
from cfb_survivor_pool.utils import flash_errors
from cfb_survivor_pool.cfbd_parser import CfbdParser, saturday_of
from datetime import datetime, date
from sqlalchemy import and_, or_
blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))



@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    conf = [x[0] for x in db.session.query(Team.conference).all()]
    conf = sorted(list(set(conf)))
    current_app.logger.info(conf)
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form, conferences=conf)


@blueprint.route("/schedule/<conference>/", methods=["GET", "POST"])
def schedule(conference="Big Ten"):
    now = datetime.utcnow()
    return schedule_day(conference=conference, year=now.year, month=now.month, day=now.day)

@blueprint.route("/schedule/<conference>/<year>/<month>/<day>/", methods=["GET", "POST"])
def schedule_day(conference="Big Ten", year=2022, month=8, day=10):
    sat2str = lambda x: "Week of %d/%d" % (x.month, x.day)
    # form = EntryForm()
    # if conference in request.args:
    #     conference = request.args["conference"]
    if type(year) == str and year.isnumeric():
        year = int(year)
    if type(month) == str and month.isnumeric():
        month = int(month)
    if type(day) == str and day.isnumeric():
        day = int(day)
    now = datetime(year=year, month=month, day=day)
    all_games = Game.query.join(Game.away_team,
                                Game.home_team,
                                aliased=True).filter(and_(Game.season == year,
                                                          or_(Game.away_team.has(conference=conference),
                                                              Game.home_team.has(conference=conference)))).all()
    grid = {}
    teams = set()
    weeks = set()
    checked = [("Nebraska", sat2str(saturday_of(date(2022, 8, 27))))]
    for g in all_games:
        if g.conference_game:
            conf_str = ""
        else:
            conf_str = "table-secondary"
        if g.start_date > now:
            can_modify = ""
        else:
            can_modify = "disabled"
            conf_str = "table-info"
        weeks.add(g.saturday)
        #### Home
        if g.home_team.conference == conference:
            key = (g.home_team.school, sat2str(g.saturday))
            grid[key] = (can_modify, g.home_team.logo, g.away_team.logo, key in checked, conf_str)
            teams.add(g.home_team.school)
        #### Away
        if g.away_team.conference == conference:
            key = (g.away_team.school, sat2str(g.saturday))
            grid[key] = (can_modify, g.away_team.logo, g.home_team.logo, key in checked, conf_str)
            teams.add(g.away_team.school)

    teams = sorted(list(teams))
    weeks = [sat2str(saturday) for saturday in sorted(weeks)]
    return render_template("public/entry.html", grid=grid, teams=teams, weeks=weeks, form=LoginForm(request.form))

@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)

@blueprint.route("/teams")
def get_teams():
    all_teams = db.session.query(Team).all()
    return render_template("public/teams.html", teams=[(t.id, t.abbreviation, t.classification, t.color, t.conference, t.logo, t.mascot, t.school, t.away_games, t.home_games) for t in all_teams])

@blueprint.route("/games/")
def get_games():
    year = datetime.utcnow().year
    # all_games = db.session.query(Game, Team).filter(and_(Game.season == year,
    #                                                      or_(Team.id == Game.away_id,
    #                                                          Team.id == Game.home_id))).all()
    all_games = db.session.query(Game).all()
    return render_template("public/games.html", games=[(g.id, g.home_id, g.away_id, g.home_points, g.away_points, g.home_team, g.away_team) for g in all_games])

@blueprint.route("/update_teams_games/<year>", methods=["GET", "POST"])
@login_required
def update_teams_games(year):
    if year.isnumeric():
        year = int(year)
    else:
        year = datetime.utcnow().year
    all_teams = db.session.query(Team).all()
    if len(all_teams) == 0:
        parser = CfbdParser(current_app.config["CFBD_API_KEY"])
        for record in parser.teams().to_dict("r"):
            item = Team(**record)
            item.save(commit=False)
        db.session.commit()
        flash("Added new teams")
        all_teams = db.session.query(Team).all()
    all_ids = [x.id for x in all_teams]
    new_games = CfbdParser(current_app.config["CFBD_API_KEY"]).games(year=year)
    new_games = new_games.loc[new_games["away_id"].isin(all_ids) &
                              new_games["home_id"].isin(all_ids), :]
    vgk = set(vars(Game).keys()) - set(["away_team", "home_team"])
    vgk.add("game_id")
    gid_list = [int(x) for x in new_games.loc[~new_games["away_points"].isna() & ~new_games["home_points"].isna(), :].index.values]
    ### 1. Find common games where score needs to be updated AND we have the score
    for game in db.session.query(Game).filter(Game.id.in_(gid_list)):
        game.away_points = int(new_games.loc[game.id, "away_points"])
        game.home_points = int(new_games.loc[game.id, "home_points"])
        game.update(commit=False)
        new_games.drop(game.id, inplace=True)
    db.session.commit()
    gid_list = [int(x) for x in new_games.index.values]
    # for game in db.session.query(Game).filter(Game.id.in_(gid_list)):
    #     new_games.drop(game.id, inplace=True)
    for record in new_games.to_dict("r"):
        record = {k: v for k, v in record.items() if k in vgk}
        game = Game(**record)
        db.session.merge(game)
    db.session.commit()
    all_games = db.session.query(Game).all()
    return redirect("/games")

# @blueprint.route("/clear_teams_games/", methods=["GET"])
# @login_required
# def clear_teams_games():
#     all_games = db.session.query(Game).delete()
#     all_teams = db.session.query(Team).delete()
#     db.session.commit()
#     return redirect("/games")
