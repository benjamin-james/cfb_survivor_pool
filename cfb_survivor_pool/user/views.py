# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from cfb_survivor_pool.user.models import User
blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")
from cfb_survivor_pool.extensions import db, login_manager


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
