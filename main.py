import flask
from flask_peewee.db import Database
import random
from peewee import TextField, IntegerField, FloatField, TimeField
from datetime import timedelta
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt

DATABASE = {
    'name': 'data.db',
    'engine': 'peewee.SqliteDatabase'
}

SECRET_KEY = 'afagfasgasgagfagsa'

app = flask.Flask(__name__) 
app.config.from_object(__name__)
trashdb = Database(app)
tdb = Database(app)
columns = []

def time_to_seconds(time_field):

    time_field=str(time_field)
    if time_field is None:
        return time_field

    else:

        time_parts = time_field.split(':')
        try:
            return float(timedelta(minutes=int(time_parts[-2]), seconds=float(time_parts[-1].replace(',', '.'))).total_seconds())
        except:
            return float(timedelta(seconds=float(time_parts[-1].replace(',', '.'))).total_seconds())
 
class Team(tdb.Model):
    number = IntegerField()
    name = TextField()
    role = TextField()
    mass = IntegerField()
    voltage = IntegerField()
    dragrace = TimeField()
    braking = FloatField()
    figures = TimeField()
    eko = IntegerField()
    race = TimeField()

    def to_dict(self):
        return {
            'Numurs': self.number,
            'Nosaukums': self.name,
            'Grupa': self.role,
            'Masa, kg': self.mass,
            'Jauda, W': self.mass*3,
            'Spriegums, V': self.voltage,
            'Strāvas stiprums, A': round(self.mass*3/self.voltage, 2),
            'Dragreisa laiks, s': time_to_seconds(self.dragrace),
            'Bremzēšanas ceļš, m': "{:.2f}".format(self.braking),
            'Figūru izbraukšanas laiks, s': time_to_seconds(self.figures),
            'Eko-apļos patērētā enerģija, kW*h': self.eko,
            'Sacensību laiks, s': time_to_seconds(self.race),
        }

    class Meta:
            database = tdb.database

with tdb.database.atomic():
    tdb.database.create_tables([Team]) 

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    flask.session['analysis'] = []
    if flask.request.method == 'POST':
        if 'file' not in flask.request.files:
            return "Nav faila augšupielādei", 400

        file = flask.request.files['file']
        
        if file.filename == '':
            return "Fails nav izvelēts", 400

        if file and file.filename.endswith('.csv'):
            tdf = pd.read_csv(file, encoding='UTF-8', delimiter=';') 
            button_value = flask.request.form.get('button')
            try:
                if button_value == 'add':
                    for _, row in tdf.iterrows():
                        name = row['name'].strip()
                        team, created = Team.get_or_create(name=name, defaults={
                            'number': int(row['number']),
                            'role': row['role'].strip(),
                            'mass': float(row['mass'].replace(',', '.')),
                            'voltage': int(row['voltage']),
                            'dragrace': row['dragrace'],
                            'braking': float(row['braking'].replace(',', '.')),
                            'figures': row['figures'],
                            'eko': int(row['eko']),
                            'race': row['race'],
                        })

                elif button_value == 'renew':
                    for _, row in tdf.iterrows():
                        name = row['name'].strip()
                        team, created = Team.get_or_create(name=name, defaults={
                            'number': int(row['number']),
                            'role': row['role'].strip(),
                            'mass': float(row['mass'].replace(',', '.')),
                            'voltage': int(row['voltage']),
                            'dragrace': row['dragrace'],
                            'braking': float(row['braking'].replace(',', '.')),
                            'figures': row['figures'],
                            'eko': int(row['eko']),
                            'race': row['race'],
                        })
                        if not created:
                            team = Team.get(name=name)
                            team.number = int(row['number'])
                            team.role = row['role'].strip()
                            team.mass = float(row['mass'].replace(',', '.'))
                            team.voltage = int(row['voltage'])
                            team.dragrace = row['dragrace']
                            team.braking = float(row['braking'].replace(',', '.'))
                            team.figures = row['figures']
                            team.eko = int(row['eko'])
                            team.race = row['race']
                            team.save()

            except KeyError as e:
                return f"Kļūdu: CSV failā nav atslēgas {e}."
            except ValueError as e:
                return f"Kļūda: Nepareizs datu tips CSV failā priekš {e}."
            return flask.redirect('/my_analysis')

        else: 
            return "Nepareizs faila formāts. Lūdzu, augšupielādējiet CSV failu.", 400
    return flask.render_template('upload.html')   

@app.route('/')
def home():
    teams = Team.select()
    return flask.render_template('home.html', teams=teams)

@app.route('/get_team/<int:id>', methods=['GET', 'POST'])
def get_team(id):
    team = Team.get_by_id(id)
    if team is None:
        return "Komanda nav atrasta", 404
    if flask.request.method == 'POST':
            button_value = flask.request.form.get('button')
            if button_value == 'addTeam':

                if 'analysis' in flask.session:
                    analysis = flask.session['analysis']
                    if not int(id) in analysis:
                        analysis.append(int(id))
                        flask.session['analysis'] = analysis
                else:
                    flask.session['analysis'] = [int(id)]



            elif button_value == 'removeTeam':
                if 'analysis' in flask.session:
                    analysis = flask.session['analysis']
                    if int(id) in analysis:
                        analysis.remove(int(id))
                        flask.session['analysis'] = analysis

                else:
                    flask.session['analysis'] = []

            elif button_value == 'deleteTeam':
                if 'analysis' in flask.session:
                    analysis = flask.session['analysis']
                if int(id) in analysis:
                    analysis.remove(int(id))
                    flask.session['analysis'] = analysis
                team = Team.get(Team.id == id)
                team.delete_instance()

            return flask.redirect(flask.url_for('my_analysis'))

    return flask.render_template('get_team.html', team=team, team_id=id)

@app.route('/my_analysis', methods=['GET','POST'])
def my_analysis():
    if 'analysis' in flask.session:
        analysis = flask.session['analysis']
    else:
        analysis = []

    analysis_teams = []
    try:
        analysis_teams = [Team.get_by_id(i) for i in analysis]
    except Team.DoesNotExist:
        pass
    teams = Team.select().where(Team.id.not_in(flask.session['analysis']))

    if flask.request.method == 'POST':
            button_value = flask.request.form.get('button')
            if button_value == 'addAllTeams':
                for team in teams:
                    analysis.append(team.id)
                flask.session['analysis'] = analysis
                analysis_teams = [Team.get_by_id(i) for i in analysis]
                teams=[]
                
            elif button_value == 'removeAllTeams':
                flask.session['analysis'] = []
                analysis_teams=[]
                teams = Team.select()
            


    return flask.render_template('my_analysis.html', analysis=analysis_teams, teams=teams)

@app.route('/table')
def table():
    if 'analysis' in flask.session:
        analysis = flask.session['analysis']
    else:
        analysis = []
    try:
        df = pd.DataFrame([team.to_dict() for team in Team.select()]).reset_index()
        del df['index']
        analysis_teams = (df.iloc[i-1] for i in analysis)
        columns=df.columns
        return flask.render_template('table.html', analysis=analysis_teams, columns=columns)
    except IndexError: return "Sākumā pievienojiet datubāzi", 404

@app.route('/workplace', methods=['GET', 'POST'])
def workplace():
    variable_names = ['chart_type', 'filter_column', 'filter_value', 'x_axis', 'y_axis']
    data = {}

    for name in variable_names:
        try:
            data[name] = flask.session[name]
        except:
            data[name] = ''
    if 'analysis' in flask.session:
        analysis = flask.session['analysis']
    else:
        analysis = []

    try:    
        df = pd.DataFrame([team.to_dict() for team in [Team.get_by_id(i) for i in analysis]])
        graphJSON = None

        if flask.request.method == 'POST':

            for name in variable_names:
                data[name] = flask.request.form.get(name)
            if data['filter_column'] in df.columns and data['filter_value'] != '':
                df_filtered = df[df[data['filter_column']] == data['filter_value']]
            else:
                df_filtered = df
            df_sorted = df_filtered.sort_values(by=data['x_axis'])

            if data['chart_type'] == 'Lineārs':
                fig = px.line(df_sorted, x=data['x_axis'], y=data['y_axis'])
            elif data['chart_type'] == 'Stabiņu':
                fig = px.bar(df_sorted, x=data['x_axis'], y=data['y_axis'])
            elif data['chart_type'] == 'Riņķa':
                fig = px.pie(df_sorted, values=data['y_axis'], names=data['x_axis'])
            elif data['chart_type'] == 'Histogramma':
                fig = px.histogram(df_sorted, x=data['x_axis'])
                fig.update_layout(yaxis_title="Skaits")
            else:
                fig = px.line(df_sorted, x=data['x_axis'], y=data['y_axis'])

            graphJSON = fig.to_json()
            for name in variable_names:
                flask.session[name]=data[name]
    except IndexError: return "Sākumā pievienojiet datubāzi", 404

    return flask.render_template('workplace.html', df=df, graphJSON=graphJSON, chart_type=data['chart_type'], filter_column=data['filter_column'],
                                 filter_value=data['filter_value'], x_axis=data['x_axis'], y_axis=data['y_axis'])

@app.route('/trash')
def trash():
    plt.close()
    count = round(random.randint(5, 25),0)
    teams=[]
    for _ in range (count):
        try:
            team=Team.get_by_id(round(random.randint(1, len(Team)),0))
            teams.append(team)
        except: pass
    trashdf = pd.DataFrame([team.to_dict() for team in teams])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    trashdf.plot(x='Nosaukums', y='Eko-apļos patērētā enerģija, kW*h', kind='bar', ax=ax)
    plt.title('Vienkārši random grafiks')
    plt.xlabel('Figūru izbraukšanas laiks')
    plt.ylabel('Eko-apļos patērētā enerģija, kW*h')
    plt.grid()
    plt.show()
    return flask.redirect('/workplace'), plt.close()

if __name__ == '__main__':
    Team.create_table(fail_silently=True)
    app.run(debug=True)
     
