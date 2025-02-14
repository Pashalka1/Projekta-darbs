import flask
from flask_peewee.db import Database
from flask_peewee.auth import Auth
from flask_peewee.admin import Admin, ModelAdmin
from peewee import TextField, IntegerField, FloatField

from werkzeug.utils import secure_filename

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, FloatField as FF
from wtforms.validators import DataRequired, Length, EqualTo

import os

DATABASE = {
    'name': 'team.db',
    'engine': 'peewee.SqliteDatabase'
}
SECRET_KEY = 'afagfasgasgagfagsa'

app = flask.Flask(__name__) 
app.config.from_object(__name__)

db = Database(app)
auth = Auth(app, db)
admin = Admin(app, auth)


class Team(db.Model):
    name = TextField()
    members = TextField()
    lenght = IntegerField()
    height = IntegerField()
    width = IntegerField()
    picture = TextField(null=True)


class TeamAdmin(ModelAdmin):
    columns: ('name')


admin.register(Team, TeamAdmin)
admin.setup()


class UserRegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=6, max=20)])
    email = EmailField('E-mail',
                       validators=[DataRequired()])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField('Confirm password',
                                     validators=[DataRequired(), EqualTo('password')])


class CreateTeamForm(FlaskForm):
    name = StringField('Team name', validators=[DataRequired()])
    members = StringField('Team members', validators=[DataRequired()])
    lenght = FF('Lenght', validators=[DataRequired()])
    height = FF('Height', validators=[DataRequired()])
    width = FF('Width', validators=[DataRequired()])


@app.route('/')
def home():
    teams = Team.select()
    return flask.render_template('home.html', teams=teams)


@app.route('/get_team/<int:id>')
def get_team(id):
    team = Team.get_by_id(id)
    return flask.render_template('get_team.html',
                                 team=team, team_id=id)


@app.route('/create_team', methods=['GET', 'POST'])
@auth.admin_required
def create_team():
    form = CreateTeamForm()

    if flask.request.method == 'POST':
        name = flask.request.form.get('team name')
        members = flask.request.form.get('team members')
        lenght = float(flask.request.form.get('lenght'))
        height = float(flask.request.form.get('height'))
        width = float(flask.request.form.get('width'))

        if 'picture' in flask.request.files:
            file = flask.request.files['picture']
            filename = secure_filename(file.filename)
            filepath = os.path.abspath(app.root_path + '/static/' + filename)
            file.save(filepath)

            new_team = Team(name=name, members=members,lenght=lenght, height=height,width=width, picture=filename)
            
        else:
            new_team = Team(name=name, members=members,lenght=lenght, height=height,width=width)
            
        new_team.save()
        flask.redirect(flask.url_for('home'))
            

    return flask.render_template('create_team.html', form=form)


@app.route('/buy_team', methods=['POST'])
@auth.login_required
def buy_team():
    team_id = flask.request.form.get('team_id')

    if 'cart' in flask.session:
        cart = flask.session['cart']
        cart.append(int(team_id))
        flask.session['cart'] = cart
    else:
        flask.session['cart'] = [int(team_id)]

    return flask.redirect(flask.url_for('my_cart'))


@app.route('/my_cart')
@auth.login_required
def my_cart():
    if 'cart' in flask.session:
        cart = flask.session['cart']
    else:
        cart = []

    cart_teams = [Team.get_by_id(i) for i in cart]
    return flask.render_template('my_cart.html', teams=cart_teams)


@app.route('/create_admin')
def create_admin():
    auth.User.create_table(fail_silently=True)
    admin = auth.User(username='admin', email='', admin=True, active=True)
    admin.set_password('admin')
    admin.save()

    return 'admin created'


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = auth.User(username=username,
                         email=email,
                         admin=False, active=True)
        user.set_password(password)
        user.save()

        return flask.redirect(flask.url_for('home')) 

    return flask.render_template('register.html', form=form)


if __name__ == '__main__':
    auth.User.create_table(fail_silently=True)
    Team.create_table(fail_silently=True)
    app.run(debug=True)
