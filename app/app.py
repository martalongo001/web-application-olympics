import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import abort,render_template, Flask
import logging
import db

APP = Flask(__name__)

# Start page
@APP.route('/')
def index():
  stats = {}
  stats = db.execute('''
   SELECT * FROM
      (SELECT COUNT(*) n_atletas FROM Atletas)
      JOIN
      (SELECT COUNT(*) n_modalidades FROM Modalidades)   
      JOIN
      (SELECT COUNT(*) n_categorias FROM Categorias) 
      JOIN 
      (SELECT COUNT(*) n_eventos FROM Eventos)       
      JOIN
      (SELECT COUNT(*) n_equipas FROM Equipas)
      JOIN
      (SELECT COUNT(*) atletas_mulheres FROM Atletas WHERE sex = 'F')
      JOIN
      (SELECT COUNT(*) atletas_homens FROM Atletas WHERE sex = 'M')
  ''').fetchone()
  logging.info(stats)
  return render_template('index.html',stats = stats)

#-------------------------------------------------------GENERAL-----STATISTICS----------------------------------------------------------------------

@APP.route('/general-statistics/')
def statistics():
  stats = db.execute('''
   SELECT * FROM
      (SELECT COUNT(*) n_atletas FROM Atletas)
      JOIN
      (SELECT COUNT(*) n_modalidades FROM Modalidades)   
      JOIN
      (SELECT COUNT(*) n_categorias FROM Categorias) 
      JOIN 
      (SELECT COUNT(*) n_eventos FROM Eventos)       
      JOIN
      (SELECT COUNT(*) n_equipas FROM Equipas)
       JOIN
      (SELECT COUNT(*) atletas_mulheres FROM Atletas WHERE sex = 'F')
      JOIN
      (SELECT COUNT(*) atletas_homens FROM Atletas WHERE sex = 'M')
      
  ''').fetchone()
  stats_athletes = db.execute('''
    select count(*) as count_medals, a.name, a.idAtletas, e.team
    from Atletas a join Participacoes p on (a.idAtletas = p.idAtletas)
    join Equipas e on e.idEquipas = a.idEquipas
    where( p.medal = 'Gold' or p.medal = 'Silver' or p.medal = 'Bronze')
    group by a.name 
    order by count_medals desc
    LIMIT 10
  ''').fetchall()
  
  stats_equipas = db.execute('''
  select e.team, count(*) as count_medals, e.idEquipas
  from equipas e join atletas a on a.idEquipas = e.idEquipas
  join participacoes p on p.idAtletas = a.idAtletas
  where (p.medal = 'Gold' or p.medal = 'Silver' or p.medal = 'Bronze') 
  group by e.team
  order by count_medals desc
  LIMIT 10;
  ''').fetchall()
  
    
  stats_games = db.execute('''
  select e.year, e.season, e.city, count(*) as number_athletes, e.idEventos,
  count (case when a.sex = 'F' then 1 end) as number_female_athletes, 
  count (case when a.sex = 'M' then 1 end) as number_male_athletes
  from eventos e 
  join participacoes p on e.idEventos = p.idEventos
  join atletas a on p.idAtletas = a.idAtletas
  group by e.year, e.season, e.city
  order by number_athletes desc
  LIMIT 10;
  ''').fetchall()
  
  return render_template('general-statistics.html',stats = stats, stats_athletes=stats_athletes, stats_equipas = stats_equipas, stats_games = stats_games)
  
  


#--------------------ATLETAS-----------------------
#athletes 
@APP.route('/athletes/')
def list_athletes():
    athletes = db.execute(
      '''
    SELECT idAtletas, name
    FROM Atletas
    GROUP BY name
    ORDER BY name
      ''').fetchall()
    return render_template('athletes-list.html', athletes=athletes)
  

#athletes id  
@APP.route('/athletes/<int:id_atleta>/')
def get_athlete(id_atleta):
  athlete_data= db.execute(
      '''
      SELECT name, idAtletas, sex, height, weight
      FROM Atletas
      WHERE idAtletas = :id
      ''', {'id': id_atleta}).fetchall()
  
  
  return render_template('athletes.html', athlete_data = athlete_data)

@APP.route('/athletes/<int:id_atleta>/athletes-participations')
def athlete_participations(id_atleta):
  
  
  athlete_participations = db.execute(
    '''
    select a.name, e.city, e.season, e.year, c.event, p.medal, e.idEventos, c.idCategorias
    from Eventos e join Participacoes p on e.idEventos = p.idEventos
    join Categorias c on p.idCategorias = c.idCategorias
    join Atletas a on p.idAtletas = a.idAtletas
    where a.name like (
    select name
    from Atletas
    where idAtletas = :id);
    ''', {'id': id_atleta}).fetchall()
  
  return render_template('athletes-participations.html', athlete_participations = athlete_participations)


#athletes search
@APP.route('/athletes/search/<expr>/')
def search_athletes(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  athletes = db.execute(
      ''' 
      SELECT name, idAtletas
      FROM Atletas
      WHERE name LIKE ?
      GROUP BY name
      ''', [expr]).fetchall()
  return render_template('athletes-search.html',
           search=search,athletes=athletes)


#-----------------EVENTOS------------------
  
#games
@APP.route('/games/')
def list_games():
    games = db.execute(
      '''
    SELECT idEventos, year, season
    FROM Eventos
    ORDER BY year
      ''').fetchall()
    return render_template('games-list.html', games=games)

  
#games id  
@APP.route('/games/<int:id_evento>/')
def get_game(id_evento):
  evento_data= db.execute(
      '''
      SELECT idEventos, year, season, city
      FROM Eventos
      WHERE idEventos = :id
      ''', {'id': id_evento}).fetchall()

  stats_events_atletas = db.execute(
    '''
    select count(*) as n_atletas
    from Atletas a 
    where a.idAtletas in
    (
    select a.idAtletas
    from Atletas a join Equipas eq on (eq.idEquipas)
    join Participacoes p on (a.idAtletas = p.idAtletas)
    join Eventos e on (e.idEventos = p.idEventos)
    where e.idEventos = :id
    )
    ''', {'id': id_evento}).fetchall()
  
    
  stats_games_medalha = db.execute(
    '''
    select count(*) as count_medals, a.name, a.idAtletas
    from Atletas a join Participacoes p on (a.idAtletas = p.idAtletas)
    join Eventos e on (e.idEventos = p.idEventos)
    where( p.medal = 'Gold' or p.medal = 'Silver' or p.medal = 'Bronze')and e.idEventos = :id
    group by a.name 
    order by count_medals desc
    LIMIT 3

    ''',{'id': id_evento}).fetchall()
  return render_template('games.html', 
           evento_data = evento_data, stats_events_atletas = stats_events_atletas,  stats_games_medalha = stats_games_medalha)


#games search
@APP.route('/games/search/<expr>')
def search_games(expr):
   search = { 'expr': expr }
   expr = '%' + expr + '%'
   games = db.execute(
      '''
      SELECT year, city, season, idEventos 
      FROM Eventos
      WHERE year LIKE ? or city LIKE ? or season LIKE ?
      ''', (expr, expr, expr)).fetchall()
   return render_template('games-search.html', search=search, games=games)



#-------------EQUIPAS------------------
#teams list
@APP.route('/teams/')
def list_teams():
   teams = db.execute(
      '''
      SELECT idEquipas, team, NOC
      FROM Equipas 
      ORDER BY idEquipas
      ''').fetchall()
   return render_template('teams-list.html', teams=teams)


#teams id
@APP.route('/teams/<int:id_equipa>/')
def get_team(id_equipa):
  team_data = db.execute(
    '''
    SELECT idEquipas, team, NOC
    FROM Equipas
    WHERE idEquipas = :id
    ''', {'id': id_equipa}).fetchall()
  
  team_members = db.execute(
     '''
    SELECT a.name, MIN(a.idAtletas) as idAtletas
    FROM Atletas a JOIN Equipas e ON a.idEquipas = e.idEquipas
    WHERE e.idEquipas = :id
    GROUP BY name
    ORDER BY idAtletas
     ''', {'id': id_equipa}).fetchall()
  
  team_members_years = db.execute(
    '''
    SELECT  a.name, eq.team, a.idAtletas, eq.NOC, e.year, c.event, e.city, e.season
    FROM Atletas a JOIN Equipas eq ON (a.idEquipas = eq.idEquipas)
    JOIN Participacoes p ON (p.idAtletas = a.idAtletas)
    JOIN Eventos e ON (e.idEventos = p.idEventos)
    JOIN Categorias c ON (c.idCategorias = p.idCategorias)
    WHERE a.idAtletas in
    (
      SELECT a.idAtletas
      FROM Atletas a JOIN Equipas eq ON (a.idEquipas = eq.idEquipas)
      where eq.idEquipas = :id
    )
    GROUP BY a.name
    ORDER BY e.year ASC
    ''', {'id': id_equipa}).fetchall()

  return render_template('teams.html', 
           team_data = team_data, team_members_years = team_members_years)


#teams search
@APP.route('/teams/search/<expr>/')
def search_teams(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  teams = db.execute(
    ''' 
    SELECT team, idEquipas
    FROM Equipas 
    WHERE team LIKE ?
    GROUP BY team
    ''', [expr]).fetchall()
  return render_template('teams-search.html',
           search=search,teams=teams)



#---------------CATEGORIAS---------------------------

#categories list
@APP.route('/categories/')
def list_categories():
   categories = db.execute(
      '''
      SELECT idCategorias, event
      FROM Categorias
      ORDER BY idCategorias
      ''').fetchall()
   return render_template('categories-list.html', categories=categories)


#categories id
@APP.route('/categories/<int:id_categoria>/')
def get_category(id_categoria):
   category_data = db.execute(
      '''
      SELECT event, idCategorias
      FROM Categorias
      WHERE idCategorias = :id
      ''', {'id': id_categoria}).fetchall()
   

   category_results_years = db.execute(
      '''
      SELECT e.year, a.name, a.idAtletas, p.medal, c.event, e.city, e.season, c.idCategorias
      FROM Eventos e JOIN Participacoes p ON e.idEventos=p.idEventos 
      JOIN Atletas a ON a.idAtletas=p.idAtletas
      JOIN Categorias c ON c.idCategorias=p.idCategorias
      WHERE c.idCategorias = :id AND (p.medal LIKE 'Gold' OR p.medal LIKE 'Silver' OR p.medal LIKE 'Bronze')
      ORDER BY e.year ASC, CASE 
        WHEN p.medal = 'Gold' THEN 1
        WHEN p.medal = 'Silver' THEN 2
        WHEN p.medal = 'Bronze' THEN 3
        END
      ''', {'id': id_categoria}).fetchall()
   return render_template('categories.html', category_data = category_data, category_results_years = category_results_years)


#categories search
@APP.route('/categories/search/<expr>/')
def search_categories(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  categories = db.execute(
    ''' 
    SELECT event, idCategorias
    FROM Categorias
    WHERE event LIKE ?
    ''', [expr]).fetchall()
  return render_template('categories-search.html',
           search=search,categories=categories)
 
   


#-----------------MODALIDADES--------------------------

#sports list
@APP.route('/sports/')
def list_sports():
   sports = db.execute(
      '''
      SELECT idModalidades, sport
      FROM Modalidades
      ORDER BY idModalidades
      ''').fetchall()
   return render_template('sports-list.html', sports=sports)


#sports id
@APP.route('/sports/<int:id_modalidade>/')
def get_sport(id_modalidade):
  sport_data = db.execute(
      '''
      select c.event as event, m.sport, m.idModalidades, c.idCategorias
      from Categorias c join Modalidades m on c.idModalidades=m.idModalidades
      where m.idModalidades = :id
      order by c.idCategorias

      ''', {'id': id_modalidade}).fetchall()
  
  return render_template('sports.html', sport_data=sport_data)


# sports search
@APP.route('/sports/search/<expr>')
def search_sports(expr):
   search = { 'expr': expr }
   expr = '%' + expr + '%'
   sports = db.execute(
      '''
      SELECT idModalidades, sport
      FROM Modalidades
      WHERE sport LIKE ?
      ''', [expr]).fetchall()
   return render_template('sports-search.html', search=search, sports=sports)
