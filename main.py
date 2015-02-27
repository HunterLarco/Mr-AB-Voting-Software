import webapp2
import os
from google.appengine.ext.webapp import template


class MainHandler(webapp2.RequestHandler):
  def get(self):
    from lib import voting
    
    game = voting.getCurrent()
    if game == None:
      self.response.out.write('Error: No Games Exist')
      return;
    
    from json import dumps
    
    template_values = {
      'contestants': dumps(game.getResults().keys()),
      'votingopen': dumps(game.isVotingOpen()),
      'identifier': int(game.key.id()),
      'round': int(game.currentround),
      'haswinner': dumps(game.hasWinner())
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/mobile.html')
    self.response.out.write(template.render(path, template_values))


class APIHandler(webapp2.RequestHandler):
  def run(self, dictionary, method):
    from lib.api import delegate, Permissions
    delegate(self, dictionary, method, Permissions.Guest)
  def post(self, dictionary, method):
    self.run(dictionary, method)
  def get(self, dictionary, method):
    self.run(dictionary, method)


class TwilioHandler(webapp2.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    
    sender = self.request.get('From')
    body = self.request.get('Body').strip()
    
    if body.lower().replace(' ', '') == 'helpme':
      self.response.out.write('Welcome To The Mr. AB Competition!\n\nTo vote type the name of your desired contestant. Keep in mind it is case sensitive.\n\nEnjoy the show!')
      return
    
    from lib import voting
    
    game = voting.getCurrent()
    if game == None:
      self.response.out.write('Error: No Game Exists')
      return
    
    if game.hasWinner():
      self.response.out.write('Sorry But The Competition Is Over!')
      return
    
    if not game.isVotingOpen():
      self.response.out.write('Please Wait. Voting Is Closed Now.')
      return
    
    namepace = game.GenerateShardNamespace()
    
    from google.appengine.api import memcache
    voted = memcache.get(sender, namespace=namepace) != None
    
    if voted:
      self.response.out.write('Sorry But You May Only Vote Once')
      return
    
    worked = game.vote(body)
    
    if not worked:
      self.response.out.write('Sorry But We Don\'t Recognize That Contestant.')
      return
    
    # expires in 30 minutes
    memcache.set(sender, True, namespace=namepace, time=60*30)
    
    self.response.out.write('Thank You For Voting!')


app = webapp2.WSGIApplication([
          ('/api/([a-z]+)/([a-z]+)/?', APIHandler),
          ('/twilio/?', TwilioHandler),
          ('/.*', MainHandler)
        ], debug=True)