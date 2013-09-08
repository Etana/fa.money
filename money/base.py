# -*- coding: utf-8 -*-

import webapp2,cgi,re,cookielib,urllib2,urllib,json,datetime

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache

class Options(db.Model):
	admin_username= db.StringProperty()
	admin_password= db.StringProperty()

# modèle d'un message de log
class Log(db.Model):
	id_to= db.IntegerProperty() 
	str_to= db.StringProperty() 
	id_from= db.IntegerProperty()
	str_from= db.StringProperty()
	num= db.IntegerProperty()
	date= db.DateTimeProperty(auto_now_add=True)

# fonction pour prendre les options
def get_options(domain):
	options= memcache.get(domain+'_options')
	if options is None:
		options= Options.get_by_key_name(domain+'_options')
	return options

# page pour administration
class Change(webapp2.RequestHandler):

	# retour d'un message
	def rep(self, message, erreur=True):
		if erreur:
			erreur='1'
		else:
			erreur='0'
		self.response.write('fa_money_callback('+erreur+','+json.dumps(message)+')')
		
	# affichage
	def get(self,domain):
		# on déclare que le document renvoyé est du javascript
		self.response.content_type= 'application/javascript'
		# saisie des options du compte admin
		options= get_options(domain)
		if options is None:
			self.rep("l'outil de transfert n'a pas été configuré")
			return
		# on récupère le &from=
		id_from=self.request.get('from')
		if id_from is None or re.match('^[1-9][0-9]*$',id_from) is None:
			self.rep("problème de requête")
			return
		# on récupère le &from_username
		str_from=self.request.get('from_username')
		if str_from is None:
			self.rep("problème de requête")
			return		
		# on récupère le &to=
		id_to=self.request.get('to')
		if id_to is None or re.match('^[1-9][0-9]*$',id_to) is None:
			self.rep("problème de requête")
			return
		if id_to==id_from:
			self.rep("vous ne pouvez vous envoyez vous-même des points")
			return
		# on récupère le &to_username
		str_to=self.request.get('to_username')
		if str_to is None:
			self.rep("problème de requête")
			return
		# on récupère le &num=
		num=self.request.get('num')
		if num is None or re.match('^[1-9][0-9]*$',num) is None:
			self.rep("problème de requête")
			return
		# on conserve les cookies
		cj = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		# connexion au forum
		opener.open('http://'+domain+'/login.forum','username='+urllib.quote_plus(options.admin_username)+'&password='+urllib.quote_plus(options.admin_password)+'&login=1&redirect=/admin/&admin=1')
		# ouverture du panneau d'admin afin de reçevoir un tid qui permet de visiter le panneau
		r = opener.open('http://'+domain+'/admin')
		# on prend le tid de l'adresse vers laquelle on a été redirigé
		tid=r.geturl()[23+len('http://'+domain):]
		if re.match('^[a-f0-9]{32}$',tid) is None:
			self.rep("l'outil de transfert a été mal configuré")
			return
		# on va rechercher la page avec le nombre de point du donateur
		r= opener.open('http://'+domain+'/admin/index.forum?part=modules&sub=point&mode=don&extended_admin=1&tid='+tid, "action=add_points_for_user&search_user="+urllib.quote_plus(re.sub(r'([\\\*%_])',r'\\\1',str_from))+"&submit_search_user=1")
		# on prend le nombre de point du donateur
		from_match= re.search('<input type="text" name="points_new_value\['+id_from+'\]" value="([+-][0-9]+)" />',r.read())
		if from_match is None:
			memcache.delete('lock'+id_from)
			memcache.delete('lock'+id_to)
			self.rep("problème pour prendre la valeur actuelle des points de %s" %  str_from)
			return
		# on regarde si son nombre de point est plus petit que le nombre de point qu'il donne
		if int(from_match.group(1)) < int(num):
			memcache.delete('lock'+id_from)
			memcache.delete('lock'+id_to)
			self.rep("vous n'avez que %d points, ce n'est pas assez pour en donner %d" %  (int(from_match.group(1)), int(num)))
			return
		# on va rechercher la page avec le nombre de point du reçeveur
		r= opener.open('http://'+domain+'/admin/index.forum?part=modules&sub=point&mode=don&extended_admin=1&tid='+tid, "action=add_points_for_user&search_user="+urllib.quote_plus(re.sub(r'([\\\*%_])',r'\\\1',str_to))+"&submit_search_user=1")
		# on prend le nombre de point du reçeveur
		to_match= re.search('<input type="text" name="points_new_value\['+id_to+'\]" value="([+-]?[0-9]+)" />',r.read())
		if to_match is None:
			self.rep(u"problème pour prendre la valeur actuelle des points de %s" %  str_to)
			return
		# on envoit les nouveaux nombres de point
		opener.open('http://'+domain+'/admin/index.forum?part=modules&sub=point&mode=don&extended_admin=1&tid='+tid, "action=add_points_for_user&points_new_value["+id_from+"]="+str(int(from_match.group(1))-int(num))+"&points_new_value["+id_to+"]="+str(int(to_match.group(1))+int(num))+"&submit=1")
		# on enregistre la transmission
		Log(parent=Options.get_by_key_name(domain+'_options'),id_to=int(id_to), str_to=str_to, id_from=int(id_from), str_from=str_from, num=int(num)).put()
		# on envoie le nouveau nombre de point du reçeveur
		self.rep(str(int(to_match.group(1))+int(num)), False)

# page pour l'affichage de l'historique d'un membre
class History(webapp2.RequestHandler):
	# affichage de la page
	def get(self, domain, user):

		# on récupère les options pour le domaine
		ancestor= get_options(domain)

		# on va rechercher toutes les fois où le membre a été reçeveur
		receiver= []
		if ancestor:
			for log in Log.all().ancestor(ancestor).filter('id_to =',int(user)).order('-date'):
				log.date=log.date.replace(tzinfo=UTC()).astimezone(CET())
				receiver.append('<td><a href="http://'+domain+'/u'+str(log.id_from)+'">'+cgi.escape(log.str_from)+'</a></td><td>'+str(log.num)+'</td><td>'+log.date.strftime("%d/%m/%y %Hh%M")+'</td>')
		if len(receiver)<1:
			receiver= '<table><tr><td>Jamais re&ccedil;u de points</td></tr></table>';
		else:
			receiver= '<table><tr><th>Envoyeur</th><th>Nombre de point</th><th>Date</th><tr><tr>'+'</tr><tr>'.join(receiver)+'</tr></table>'

		# on va rechercher toutes les fois où le membre a été envoyeur
		sender= []
		if ancestor:
			for log in Log.all().ancestor(ancestor).filter('id_from =',int(user)).order('-date'):
				log.date=log.date.replace(tzinfo=UTC()).astimezone(CET())
				sender.append('<td><a href="http://'+domain+'/u'+str(log.id_to)+'">'+cgi.escape(log.str_to)+'</a></td><td>'+str(log.num)+'</td><td>'+log.date.strftime("%d/%m/%y %Hh%M")+'</td>')
		if len(sender)<1:
			sender= '<table><tr><td>Jamais envoy&eacute; de points</td></tr></table>';
		else:
			sender= '<table><tr><th>Re&ccedil;eveur</th><th>Nombre de point</th><th>Date</th><tr><tr>'+'</tr><tr>'.join(sender)+'</tr></table>'
			
		# affichage de la page
		self.response.out.write('''<html>


<head>
	<title>Administration</title>
	<style>
		th {color:#FFF;background-color:#6199df;border:1px solid #4d90fe;font-weight:700;}
		th, td{padding:6px 10px;}
		td { border:1px solid #bbb }
		body{font-size:0.9em, color:#333;font-family:arial,serif;}
		a{color:#15c;}
		h2{font-size:1.05em;font-weight:700;color:#404040;margin-top:1em;}
		table{border-collapse:collapse;text-align:left;font-size:13px;}
	</style>
<body>
	<h2>R&eacute;ception de point</h2>
	%s
	<h2>Don de point</h2>
	%s
	<h2>Profil</h2>
	<a href="%s">Lien</a>
</body>
</html>''' % (
				receiver,
				sender,
				'http://'+domain+'/u'+user
			)
		)
	   

# page pour administration
class Admin(webapp2.RequestHandler):
	# affichage
	def get(self, domain):
		# saisie des options
		options= get_options(domain)
		if options is None:
			options=Options(admin_username='',admin_password='')

		# on va rechercher tout les 100 derniers logs
		logs= []
		ancestor= get_options(domain)
		if ancestor:
			for log in Log.all().ancestor(ancestor).order('-date').fetch(100):
				log.date=log.date.replace(tzinfo=UTC()).astimezone(CET())
				logs.append('<td><a href="http://'+domain+'/u'+str(log.id_from)+'">'+cgi.escape(log.str_from)+'</a></td><td><a href="http://'+domain+'/u'+str(log.id_to)+'">'+cgi.escape(log.str_to)+'</a></td><td>'+str(log.num)+'</td><td>'+log.date.strftime("%d/%m/%y %Hh%M")+'</td>')
		if len(logs)<1:
			logs= '<table><tr><td>Aucune transmission de point r&eacute;alis&eacute;e</td></tr></table>';
		else:
			logs= '<table><tr><th>Envoyeur</th><th>Re&ccedil;eveur</th><th>Nombre de point</th><th>Date</th><tr><tr>'+'</tr><tr>'.join(logs)+'</tr></table>'

		# affichage de la page
		self.response.out.write('''<html>


<head>
	<title>Administration</title>
	<style>
		th,button{color:#FFF;background-color:#6199df;border:1px solid #4d90fe;font-weight:700;}
		th, td, input,button{padding:6px 10px;}
		input, td, textarea { border:1px solid #bbb }
		textarea, input{width:300px;}
		textarea { height: 200px; width: 500px; }
		body{font-size:0.9em}
		body,input{color:#333;font-family:arial,serif;}
		a{color:#15c;}
		h2{font-size:1.05em;font-weight:700;color:#404040;margin-top:1em;}
		label, label input { display: block; }
		label input { margin: 5px 0; }
		label span { display: block; }
		table{border-collapse:collapse;text-align:left;font-size:13px;}
	</style>
<body>
	<form method="POST" enctype="multipart/form-data">
		<h2>Identification</h2>
			<label>Pseudo admin : <input name="username" value="%s" /></label>
			<label>Mot de passe : <input type="password" name="password" /></label>
			<button type="submit">Enregistrer</button>
		</table>
	</form>
	<h2>Script</h2>
	<textarea readonly>var money_app_url='%s';

location.pathname.match(/^\/u[1-9][0-9]*/) &amp;& $(function() {
  var to = location.pathname.match(/^\/u([1-9][0-9]*)/)[1];
  var to_username = document.title.replace(/^.*? - /, "");
  var from = +(my_getcookie("fa_" + location.host.replace(/\./g, "_") + "_data") || "").replace(/^.*"userid";(s:[1-9][0-9]*:"([1-9][0-9]*)"|i:([1-9][0-9]*));.*$/, "$2$3");
  var from_username = $('#logout img').attr('alt').replace(/^.*?\[ (.*) \]$/,'$1');
  var default_point = 10;
  $("#field_id-13 dd div").wrapInner('&lt;span class="num_point" /&gt;').append('<span class="history_point"> <a href="'+money_app_url+'/history/'+to+'"><input type="button" value="Historique" /></a> </span>');
  if(from && to != from) {
	fa_money_callback = function(error, message) {
	  if(error) {
		alert("Erreur : " + message)
	  }else {
		$("#field_id-13 .num_point").text(message)
	  }
	};
	$('<span class="offer_point"><input type="button" value="Donner" /></span>').insertAfter($(".history_point")).children().click(function() {
	  var bouton = $(this).prop("disabled", true);
	  var num = prompt("Offrir combien de points ?", default_point);
	  if(!num || !num.match(/^\s*[1-9][0-9]*\s*$/)) {
		bouton.prop("disabled", false);
		return
	  }
	  default_point = num;
	  $.getScript(money_app_url+"/?from=" + from + "&from_username="+encodeURIComponent(from_username)+"&to=" + to + "&to_username=" + encodeURIComponent(to_username) + "&num=" + num.replace(/(^\s*|\s*$)/g, ""), function() {
		bouton.prop("disabled", false)
	  })
	})
  }
});</textarea>
	<h2>Historique</h2>
	%s
	<h2>D&eacute;connexion</h2>
	<a href="%s">Se d&eacute;connecter</a>
</body>
</html>''' % (
				cgi.escape(options.admin_username, True),
				self.request.host_url+self.request.path[:-6],
				logs,
				users.create_logout_url(self.request.uri)
			)
		)
	
	# traitement formulaire
	def post(self, domain):
			# on prend le lien jusqu'au troisieme slash
			link=re.sub(r'^(http://[^/]+)/?.*$',r'\1',self.request.get('link'))
			# on enregistre les options dans la base de donnée
			Options(key_name=domain+'_options', admin_username=self.request.get('username'), admin_password=self.request.get('password')).put()
			# on supprime les options pouvant se trouver dans le cache
			memcache.delete(domain+'_options')
			# on redirige vers le formulaire
			self.redirect('./admin')

# fuseau horaire UTC
class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
	return datetime.timedelta(0)
 
  def dst(self, dt):
	return datetime.timedelta(0)
 
  def tzname(self, dt):
	return "UTC"

# fuseau horaire de l'Europe centrale
class CET(datetime.tzinfo):
  def __init__(self):
	dt = datetime.datetime.utcnow()

	d = datetime.datetime(dt.year, 4, 1)
	self.dston = d - datetime.timedelta(days = d.weekday() + 1)

	d = datetime.datetime(dt.year, 11, 1)
	self.dstoff = d - datetime.timedelta(days = d.weekday() + 1)

  def utcoffset(self, dt):
	return datetime.timedelta(hours = 1) + self.dst(dt)

  def dst(self, dt):
	if self.dston <= dt.replace(tzinfo = None) < self.dstoff:
	  return datetime.timedelta(hours = 1)
	else:
	  return datetime.timedelta()

  def tzname(self, dt):
	if self.dston <= dt.replace(tzinfo = None) < self.dstoff:
		return "CEST"
	else:
		return "CET"

app = webapp2.WSGIApplication(
	[
		('/fa_money/([a-z0-9.-]+)/admin', Admin),
		('/fa_money/([a-z0-9.-]+)/history/([1-9][0-9]*)', History),
		('/fa_money/([a-z0-9.-]+)/', Change)
	], debug=True)
