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
from cfb_survivor_pool.user.models import User, Pick, Entry
from cfb_survivor_pool.utils import flash_errors
from cfb_survivor_pool.cfbd_parser import CfbdParser, saturday_of
#from datetime import datetime, date
import datetime as dt
from sqlalchemy import and_, or_, desc
blueprint = Blueprint("public", __name__, static_folder="../static")
sat2str = lambda x: "Week of %d/%d" % (x.month, x.day)

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
            redirect_url = request.args.get("next") or url_for("user.list_entries")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    year = dt.datetime.utcnow().year
    return render_template("public/home.html", form=form, conferences=conf, year=year)


@blueprint.route("/schedule/<year>/<conference>/", methods=["GET", "POST"])
def schedule(year=2022, conference="Big Ten"):
    now = dt.datetime.utcnow()
    return schedule_day(conference=conference, year=year, month=now.month, day=now.day)

@blueprint.route("/schedule/<conference>/<year>/<month>/<day>/", methods=["GET", "POST"])
def schedule_day(conference="Big Ten", year=2022, month=8, day=10):
    ### TODO: warn user if could select more teams or picks
    sat2str = lambda x: "Week of %d/%d" % (x.month, x.day)
    print(request.method)
    # form = EntryForm()
    # if conference in request.args:
    #     conference = request.args["conference"]
    if type(year) == str and year.isnumeric():
        year = int(year)
    if type(month) == str and month.isnumeric():
        month = int(month)
    if type(day) == str and day.isnumeric():
        day = int(day)
    now = dt.datetime(year=year, month=month, day=day)
    all_games = Game.query.join(Game.away_team,
                                Game.home_team,
                                aliased=True).filter(and_(Game.season == now.year,
                                                          or_(Game.away_team.has(conference=conference),
                                                              Game.home_team.has(conference=conference)))).all()
    grid = {}
    teams = set()
    weeks = set()

    checked = [("Nebraska", sat2str(saturday_of(dt.date(2022, 8, 27))))]
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
            # pk = Pick(team=g.home_team, game=g, created=now)
            # db.session.add(pk)
            key = (g.home_team.school, sat2str(g.saturday))
            grid[key] = (can_modify, g.home_team.logo, g.away_team.logo, key in checked, conf_str)
            teams.add(g.home_team.school)
        #### Away
        if g.away_team.conference == conference:
            # pk = Pick(team=g.away_team, game=g, created=now)
            # db.session.add(pk)
            key = (g.away_team.school, sat2str(g.saturday))
            grid[key] = (can_modify, g.away_team.logo, g.home_team.logo, key in checked, conf_str)
            teams.add(g.away_team.school)

    teams = sorted(list(teams))
    weeks = [sat2str(saturday) for saturday in sorted(weeks)]
    # flash(db.session.query(Pick).all())
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

@blueprint.route("/picks")
def get_picks():
    all_picks = db.session.query(Pick).all()
    return render_template("public/picks.html", picks=all_picks)

def render_games(all_games):
    import pytz
    return render_template("public/games.html", games=[(g.id, g.home_id, g.away_id, g.home_points, g.away_points, g.home_team, g.away_team, g.start_date.astimezone(pytz.timezone('US/Eastern'))) for g in all_games])

@blueprint.route("/games/<year>")
def get_games(year):
    all_games = db.session.query(Game).filter(Game.season == year).all()
    return render_games(all_games)

@blueprint.route("/scores")
def get_scores():
    return get_games(dt.datetime.utcnow().year)

@blueprint.route("/games/<year>/<conference>")
def get_games_conference(year, conference):
    all_games = Game.query.join(Game.away_team,
                                Game.home_team,
                                aliased=True).filter(and_(Game.season == year,
                                                          or_(Game.away_team.has(conference=conference),
                                                              Game.home_team.has(conference=conference)))).all()
    return render_games(all_games)

@blueprint.route("/scores/<conference>")
def get_scores_conference(conference):
    return get_games_conference(year=dt.datetime.utcnow().year, conference=conference)


@blueprint.route("/update_teams_games/<year>", methods=["GET", "POST"])
@login_required
def update_teams_games(year):
    if year.isnumeric():
        year = int(year)
    else:
        year = dt.datetime.utcnow().year
    if False: ### if need to clear data
        all_teams = db.session.query(Team).all()
        all_games = db.session.query(Game).all()
        for g in all_games:
            db.session.delete(g)
        db.session.commit()
        for t in all_teams:
            db.session.delete(t)
        db.session.commit()
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

@blueprint.route("/standings/<year>/<conference>")
def standings(year, conference):
    intra = 5
    inter = 1
    elist = db.session.query(Entry).filter(and_(Entry.year == year,
                                                Entry.conference == conference)).all() #.order_by(Entry.last_updated).all()
    elist.sort(key=lambda x: x.last_updated)
    elist.sort(key=lambda x: x.survived)
    elist.sort(key=lambda x: x.score(intra_conference_score=intra, inter_conference_score=inter), reverse=True)
    return render_template("public/standings.html", entries=elist, year=year, conference=conference, intra=intra, inter=inter)

@blueprint.route("/view_entry/<entry>")
def view_entry(entry):
    elist = db.session.query(Entry).filter(Entry.id == entry).all()
    if len(elist) != 1:
        return render_template("404.html")
    entry = elist[0]
    picks = []
    for pick in entry.picks:
        tbl = {"logo": pick.team.logo,
               "saturday": pick.game.saturday,
               "week": sat2str(pick.game.saturday),
               "school": pick.team.school,
               "correct": pick.is_correct}
        picks.append(tbl)
        picks.sort(key=lambda x: x["saturday"])
    return render_template("public/view.html", entry=entry, picks=picks)
