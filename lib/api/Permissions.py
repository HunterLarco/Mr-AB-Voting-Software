# common imports
import response
from .. import voting


### within this file, each root class defines what API functions are accessible by POST or GET. that way permission may be changed by simply instruction the API engine to delegate to a different permission map. For example, 'admin' indicates that api url '/constants/add' allows one to add a constant to the database, because a user doesn't have this privilage, their permission map lacks this ability. Note that GET requests must use the get dictionary exclusively








def require(*keys):
  def decorator(funct):
    def reciever(self, payload):
      for key in keys:
        if not key in payload:
          return response.throw(001)
      return funct(self, payload)
    return reciever
  return decorator







class Admin:
  class admin:
    
    @require('identifier')
    def close(self, payload):
      game = voting.get(payload['identifier'])
      if not game:
        return response.throw(100, payload['identifier'])
      game.closeVoting(keep_duplicates=False)
      
      from json import dumps
      from google.appengine.api import channel
      channel.send_message('projector', dumps({
        'event': 'close',
        'results': game.getResults()
      }))
      
      return response.reply({
        'haswinner': game.hasWinner(),
        'results': game.getResults()
      })
    
    @require('identifier')
    def open(self, payload):
      game = voting.get(payload['identifier'])
      if not game:
        return response.throw(100, payload['identifier'])
      game.openVoting()
      
      from json import dumps
      from google.appengine.api import channel
      channel.send_message('projector', dumps({
        'event': 'open'
      }))
    
    @require('contestants', 'roundmap')
    def create(self, payload):
      try:
        game = voting.create(payload['contestants'], payload['roundmap'])
      except:
        return response.throw(0)
      
      return response.reply({
        'identifier': game.key.id()
      })
      





class Guest:
  class game:
    
    @require('identifier', 'contestant')
    def vote(self, payload):
      game = voting.get(payload['identifier'])
      if not game:
        return response.throw(100, payload['identifier'])
      if not game.vote(payload['contestant']):
        return response.throw(101)
    
    @require('identifier')
    def canvote(self, payload):
      game = voting.get(payload['identifier'])
      if not game:
        return response.throw(100, payload['identifier'])
      return response.reply({
        'canvote': game.isVotingOpen(),
        'haswinner': game.hasWinner()
      })

    @require('identifier')
    def contestants(self, payload):
      game = voting.get(payload['identifier'])
      if not game:
        return response.throw(100, payload['identifier'])
      return response.reply({
        'contestants': game.getResults().keys(),
        'round': game.currentround
      })
