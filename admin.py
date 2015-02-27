import os
from google.appengine.ext.webapp import template
import webapp2


class APIHandler(webapp2.RequestHandler):
  def run(self, method):
    from lib.api import delegate, Permissions
    delegate(self, 'admin', method, Permissions.Admin)
  def post(self, method):
    self.run(method)
  def get(self, method):
    self.run(method)


class MainHandler(webapp2.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'templates/create.html')
    self.response.out.write(template.render(path, template_values))


class GameConsole(webapp2.RequestHandler):
  def get(self, identifier):
    from lib import voting
    
    game = voting.get(identifier)
    if game == None:
      self.redirect('/admin/')
      return
    
    from json import dumps
    
    template_values = {
      'contestants': dumps(game.getContestants()),
      'roundmap': game.roundmap,
      'results': dumps(game.getAllResults()),
      'currentround': game.currentround,
      'identifier': int(identifier),
      'isopen': dumps(game.isVotingOpen()),
      'haswinner': dumps(game.hasWinner())
    }
    
    path = os.path.join(os.path.dirname(__file__), 'templates/monitor.html')
    self.response.out.write(template.render(path, template_values))


class ProjectorHandler(webapp2.RequestHandler):
  def get(self):
    from google.appengine.api import channel
    from json import dumps
    from lib import voting
    
    game = voting.getCurrent()
    if game == None:
      self.redirect('/admin/')
      return
    
    template_values = {
      'socket': channel.create_channel('projector'),
      'results': dumps(game.getAllResults()),
      'isvoting': dumps(game.isVotingOpen())
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/projector.html')
    self.response.out.write(template.render(path, template_values))


class TestHandler(webapp2.RequestHandler):
  def get(self):
    from lib import voting
    
    game = voting.getCurrent()
    if game == None:
      self.redirect('/admin/')
      return
    
    template_values = {
      'identifier': int(game.key.id())
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/test.html')
    self.response.out.write(template.render(path, template_values))


app = webapp2.WSGIApplication([
          ('/api/admin/([a-z]+)/?', APIHandler),
          ('/admin/game/([0-9]+)/?', GameConsole),
          ('/admin/projector/?', ProjectorHandler),
          ('/admin/test/?', TestHandler),
          ('.*', MainHandler)
        ], debug=True)