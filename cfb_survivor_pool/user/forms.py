# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, RadioField, SelectField, FormField, FieldList, widgets, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from .models import User


class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=25)]
    )
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=6, max=40)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        return True


class EntryWidget:
    ### modified tablewidget from https://github.com/wtforms/wtforms/blob/master/src/wtforms/widgets/core.py
    def __call__(self, field, **kwargs):
        from markupsafe import Markup
        html = []
        hidden = ""
        iteration = 0
        for subfield in field:
            if subfield.type in ("HiddenField", "CSRFTokenField"):
                hidden += str(subfield)
            else:
                print("subfield:", vars(subfield))
                if "data-td-class" in subfield.render_kw.keys():
                    td = " class=\"%s\"" % subfield.render_kw["data-td-class"]
                else:
                    td = ""
                subfield.id = subfield.data
                if "selected" in subfield.render_kw.keys() and subfield.id == subfield.render_kw["selected"]:
                    subfield.checked = True
                subfield.render_kw["aria-label"] = "%s %s" % (subfield.name, subfield.id)
                html.append(
                    "<td%s><label class=\"radio-inline\">%s%s<img src=\"%s\" style=\"width:50px;height:50px;\"></label></td>"
                    % (td,
                        hidden, str(subfield), subfield.label.text)
                )
                hidden = ""
                iteration += 1
        if hidden:
            html.append(hidden)
        return Markup("\n".join(html))

class WeekForm(FlaskForm):
    ### https://stackoverflow.com/questions/24296834/wtform-fieldlist-with-selectfield-how-do-i-render/57548509#57548509
    teams = RadioField("Placeholder", choices=[], widget=EntryWidget(), render_kw={"class": "form-check-input"})

class EntryForm(FlaskForm):
    ### https://stackoverflow.com/questions/28375565/add-input-fields-dynamically-with-wtforms
    weeks = FieldList(FormField(WeekForm))
    submit = SubmitField('Submit')
