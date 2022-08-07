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
from cfb_survivor_pool.public.forms import LoginForm, EntryForm
from cfb_survivor_pool.public.models import Team, Game
from cfb_survivor_pool.user.forms import RegisterForm
from cfb_survivor_pool.user.models import User
from cfb_survivor_pool.utils import flash_errors
from cfb_survivor_pool.cfbd_parser import CfbdParser
from datetime import datetime
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
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form)


@blueprint.route("/entry", methods=["GET", "POST"])
@login_required
def entry():
    form = EntryForm()
    is_playing = [('Illinois', 'Week 1'), ('Illinois', 'Week 5'), ('Illinois', 'Week 6'), ('Illinois', 'Week 7'), ('Illinois', 'Week 9'), ('Illinois', 'Week 10'), ('Illinois', 'Week 11'), ('Illinois', 'Week 12'), ('Illinois', 'Week 13'), ('Indiana', 'Week 1'), ('Indiana', 'Week 5'), ('Indiana', 'Week 6'), ('Indiana', 'Week 7'), ('Indiana', 'Week 8'), ('Indiana', 'Week 10'), ('Indiana', 'Week 11'), ('Indiana', 'Week 12'), ('Indiana', 'Week 13'), ('Iowa', 'Week 4'), ('Iowa', 'Week 5'), ('Iowa', 'Week 6'), ('Iowa', 'Week 8'), ('Iowa', 'Week 9'), ('Iowa', 'Week 10'), ('Iowa', 'Week 11'), ('Iowa', 'Week 12'), ('Iowa', 'Week 13'), ('Maryland', 'Week 4'), ('Maryland', 'Week 5'), ('Maryland', 'Week 6'), ('Maryland', 'Week 7'), ('Maryland', 'Week 8'), ('Maryland', 'Week 10'), ('Maryland', 'Week 11'), ('Maryland', 'Week 12'), ('Maryland', 'Week 13'), ('Michigan', 'Week 4'), ('Michigan', 'Week 5'), ('Michigan', 'Week 6'), ('Michigan', 'Week 7'), ('Michigan', 'Week 9'), ('Michigan', 'Week 10'), ('Michigan', 'Week 11'), ('Michigan', 'Week 12'), ('Michigan', 'Week 13'), ('Michigan State', 'Week 4'), ('Michigan State', 'Week 5'), ('Michigan State', 'Week 6'), ('Michigan State', 'Week 7'), ('Michigan State', 'Week 9'), ('Michigan State', 'Week 10'), ('Michigan State', 'Week 11'), ('Michigan State', 'Week 12'), ('Michigan State', 'Week 13'), ('Minnesota', 'Week 4'), ('Minnesota', 'Week 5'), ('Minnesota', 'Week 7'), ('Minnesota', 'Week 8'), ('Minnesota', 'Week 9'), ('Minnesota', 'Week 10'), ('Minnesota', 'Week 11'), ('Minnesota', 'Week 12'), ('Minnesota', 'Week 13'), ('Nebraska', 'Week 1'), ('Nebraska', 'Week 5'), ('Nebraska', 'Week 6'), ('Nebraska', 'Week 7'), ('Nebraska', 'Week 9'), ('Nebraska', 'Week 10'), ('Nebraska', 'Week 11'), ('Nebraska', 'Week 12'), ('Nebraska', 'Week 13'), ('Northwestern', 'Week 1'), ('Northwestern', 'Week 5'), ('Northwestern', 'Week 6'), ('Northwestern', 'Week 8'), ('Northwestern', 'Week 9'), ('Northwestern', 'Week 10'), ('Northwestern', 'Week 11'), ('Northwestern', 'Week 12'), ('Northwestern', 'Week 13'), ('Ohio State', 'Week 4'), ('Ohio State', 'Week 5'), ('Ohio State', 'Week 6'), ('Ohio State', 'Week 8'), ('Ohio State', 'Week 9'), ('Ohio State', 'Week 10'), ('Ohio State', 'Week 11'), ('Ohio State', 'Week 12'), ('Ohio State', 'Week 13'), ('Penn State', 'Week 1'), ('Penn State', 'Week 5'), ('Penn State', 'Week 7'), ('Penn State', 'Week 8'), ('Penn State', 'Week 9'), ('Penn State', 'Week 10'), ('Penn State', 'Week 11'), ('Penn State', 'Week 12'), ('Penn State', 'Week 13'), ('Purdue', 'Week 1'), ('Purdue', 'Week 5'), ('Purdue', 'Week 6'), ('Purdue', 'Week 7'), ('Purdue', 'Week 8'), ('Purdue', 'Week 10'), ('Purdue', 'Week 11'), ('Purdue', 'Week 12'), ('Purdue', 'Week 13'), ('Rutgers', 'Week 4'), ('Rutgers', 'Week 5'), ('Rutgers', 'Week 6'), ('Rutgers', 'Week 8'), ('Rutgers', 'Week 9'), ('Rutgers', 'Week 10'), ('Rutgers', 'Week 11'), ('Rutgers', 'Week 12'), ('Rutgers', 'Week 13'), ('Wisconsin', 'Week 4'), ('Wisconsin', 'Week 5'), ('Wisconsin', 'Week 6'), ('Wisconsin', 'Week 7'), ('Wisconsin', 'Week 8'), ('Wisconsin', 'Week 10'), ('Wisconsin', 'Week 11'), ('Wisconsin', 'Week 12'), ('Wisconsin', 'Week 13')]
    teams = ['Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota', 'Nebraska', 'Northwestern', 'Ohio State', 'Penn State', 'Purdue', 'Rutgers', 'Wisconsin']
    weeks = ['Week 1', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8', 'Week 9', 'Week 10', 'Week 11', 'Week 12', 'Week 13']
    grid = []
    checked = [("Nebraska", "Week 1"), ("Iowa", "Week 5")]
    for team in teams:
        for week in weeks:
            ### TODO: check if current time allows pick
            grid.append((team, week, (team, week) in is_playing, (team, week) in checked))
    return render_template("public/entry.html", grid=grid, teams=teams, weeks=weeks, form=form)

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

def grab_teams_games():
    """Update games from CFBD"""
    parser = CfbdParser(current_app.config["CFBD_API_KEY"])
    teams = parser.teams()
    # games = parser.games(year=datetime.utcnow().year)
    #
    # current_app.logger.info("%d games; %d teams" % (games.shape[0], teams.shape[0]))
    return teams, None

@blueprint.route("/teams")
def get_teams():
    all_teams = db.session.query(Team).all()
    return render_template("public/teams.html", teams=[(t.id, t.abbreviation, t.classification, t.color, t.conference, t.logo, t.mascot, t.school) for t in all_teams])

@blueprint.route("/games/")
def get_games():
    all_games = db.session.query(Game).all()
    return render_template("public/games.html", games=[(g.id, g.home_id, g.away_id, g.home_points, g.away_points, g.home_team, g.away_team) for g in all_games])

@blueprint.route("/update_teams_games/", methods=["GET"])
def update_teams_games():
    year = datetime.utcnow().year
    if "year" in request.args and request.args["year"].isnumeric():
        year = int(request.args["year"])
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
    ### For the games, we want to
    ### 1. update when scores are changed
    ### 2. insert when id is not in db so need to find when ID will be in DB
    ###   A.
    new_games = CfbdParser(current_app.config["CFBD_API_KEY"]).games(year=year)
    new_games = new_games.loc[new_games["away_id"].isin(all_ids) &
                              new_games["home_id"].isin(all_ids), :]
    ### filter for games where we need to explicitly update
    gid_list = new_games.loc[~new_games["away_points"].isna() & ~new_games["home_points"].isna(), :].index.values
    ### 1. Find common games where score needs to be updated AND we have the score
    for game in db.session.query(Game).filter(and_(Game.away_points is None,
                                                   Game.home_points is None,
                                                   Game.id.in_(gid_list))):
        game.away_points = new_games.loc[game.id, "away_points"]
        game.home_points = new_games.loc[game.id, "home_points"]
        game.update(commit=False)
        new_games.drop(game.id, inplace=True)
    db.session.commit()
    vgk = list(vars(Game).keys())
    vgk.append("game_id")
    for record in new_games.to_dict("r"):
        record = {k: v for k, v in record.items() if k in vgk}
        game = Game(**record)
        db.session.merge(game)
    db.session.commit()
    all_games = db.session.query(Game).all()
    return render_template("public/games.html", games=[(g.id, g.home_id, g.away_id, g.home_points, g.away_points, g.home_team, g.away_team) for g in all_games])
