# -*- coding: utf-8 -*-

import webapp2,datetime,urllib,cgi

from google.appengine.ext import blobstore
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers

class Admin(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')

        display_up= []
        uploads= blobstore.BlobInfo.all().order('-creation')
        for upload in uploads:
            display_up.append('<tr><td>'+cgi.escape(urllib.unquote(upload.filename))+'</td><td>'+upload.content_type+'</td><td>'+str(round(upload.size/1024.0,1))+' ko</td><td>'+format_timedelta(upload.creation) +'</td><td><a href="/f/'+str(upload.key())+'/'+urllib.quote(urllib.unquote(upload.filename).encode('utf-8'),'~@#$&()*!+=:;,.?/\'')+'">unique</a> | <a href="/n/'+urllib.quote(urllib.unquote(upload.filename).encode('utf-8'),'~@#$&()*!+=:;,.?/\'')+'">nomm&eacute;</a> | <a href="/delete/'+str(upload.key())+'">suppression</a></td></tr>');

        display_up='\n        '.join(display_up)

        self.response.out.write('''<html>
<head>
    <title>Zufont</title>
    <style>th{color:#FFF;background-color:#6199df;border:1px solid #4d90fe;font-weight:700;}th,td{padding:6px 10px;}td{border:1px solid #bbb;}table{border-collapse:collapse;text-align:left;font-size:13px;}body{color:#333;font-family:arial,serif;}a{color:#15c;}h2{font-size:1.05em;font-weight:700;color:#404040;margin-top:1em;}</style>
<body>
    <h2>Ajouter un fichier</h2>
    <form action="%s" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"> <input type="submit" name="submit" value="Envoyer">
    </form>
    <h2>Liste des fichiers</h2>
    <table>
        <tr><th>Fichier</th><th>Type</th><th>Taille</th><th>Ajout&eacute;</th><th>Liens</th></tr>
        %s
    </table>
    <h2>D&eacute;connexion</h2>
    <a href="%s">Se d&eacute;connecter</a>
</body>
</html>''' % (upload_url,display_up,users.create_logout_url(self.request.uri)))

def format_timedelta(value):
    t= datetime.datetime.now() - value
    if  t.days>0 :
        return value.strftime('le %d/%m/%Y')
    elif t.seconds>3599 :
        return 'il y a '+str(t.seconds/3600)+'h'
    elif t.seconds>59 :
        return 'il y a '+str(t.seconds/60)+'m'
    else:
        return 'il y a '+str(t.seconds)+'s'

class Upload(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        blob_info= upload_files[0]
        from google.appengine.api import memcache
        memcache.set(blob_info.filename,str(blob_info.key()))
        self.redirect("/")

class Delete(webapp2.RequestHandler):
    def get(self,resource):
        blob_info= blobstore.BlobInfo.get(resource)
        from google.appengine.api import memcache
        blob_key= memcache.get(blob_info.filename)
        if blob_key==str(blob_info.key()):
            memcache.delete(blob_info.filename)
        blob_info.delete()
        self.redirect("/")

app = webapp2.WSGIApplication(
    [
        ('/', Admin),
        ('/delete/([A-Za-z0-9_=-]+)', Delete),
        ('/upload', Upload)
    ], debug=True)
