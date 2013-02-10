# -*- coding: utf-8 -*-

import webapp2

from google.appengine.api import users

class Logout(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_logout_url("/"))

app = webapp2.WSGIApplication(
    [
        ('/logout', Logout)
    ], debug=True)
