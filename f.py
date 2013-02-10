# -*- coding: utf-8 -*-

import webapp2,datetime,urllib2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

class File(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, attr, resource):

        if self.request.headers.get('If-None-Match'):
            self.response.set_status(304)    
            self.response.headers['Cache-Control'] = 'public'
            return


        if attr=='n':
            from google.appengine.api import memcache
            resource= resource.replace('"','%22')
            blob_key= memcache.get(resource)
            if blob_key is None:
                blob_info= blobstore.BlobInfo.all().filter('filename =', resource.decode('utf-8')).order('-creation').get()
                if blob_info is not None:
                    memcache.set(resource,str(blob_info.key()))
            else:
                blob_info= blobstore.BlobInfo.get(blob_key)
        else:
            blob_info= blobstore.BlobInfo.get(resource)

        if blob_info is None:
            self.abort(404)
        
        self.response.headers['Cache-Control'] = 'public'
        date= datetime.datetime.now() + datetime.timedelta(365)
        self.response.headers['Expires'] = date.strftime("%a, %d %b %Y %H:%M:00 GMT")
        self.response.md5_etag()
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        self.send_blob(blob_info)

app = webapp2.WSGIApplication(
    [
        ('/(f)/([A-Za-z0-9_=-]+)(?:/[^/]*)?', File),
        ('/(n)/([^/]+)', File),
    ], debug=True)
