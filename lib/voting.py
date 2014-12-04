"""
' Common Package Imports
"""
from google.appengine.ext import ndb

"""
' PURPOSE
"""
class Game(ndb.Model):
  roundmap = ndb.IntegerProperty(repeated=True)
  currentround = ndb.IntegerProperty()
  voting = ndb.BooleanProperty()
  results = ndb.PickleProperty()
  
  """
  ' PURPOSE
  '   Changes game data to reflect the next round, saving all contestant
  '   stats and removing those who are no longer in the game.
  ' PARAMETERS
  '   <bool **kwarg keep_duplicates>
  ' RETURNS
  '   Boolean
  '     True ~ The next round has begun
  '     False ~ There are no future rounds, the game is over
  ' NOTES
  '   1. see updatesResults for the 'keep_duplicates' explanation
  """
  def nextRound(self, keep_duplicates=True):
    if self.currentround > len(self.roundmap)-1:
      return False
    self.updateResults(keep_duplicates=keep_duplicates)
    self.currentround += 1
    self.put()
    return True
  
  """
  ' PURPOSE
  '   Creates a new result dict and adds the top contestants into
  '   the new dict for the next round. The amount of contestants depends on
  '   the amount of people specified for this round in the roundmap
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  ' NOTES
  '   1. The 'keep_duplicates' parameter determines whether
  '      people with the same vote count can be moved to the next
  '      round. For example, pick the top two from this...
  '        Max - 5 votes
  '        Ted - 3 votes
  '        Bob - 3 votes
  '      If it is false then either ted or bob will be chosen to move on
  '      randomly.
  """
  def updateResults(self, keep_duplicates=True):
    arr = self.results[self.currentround].items()
    sorter_arr = sorted(arr, key=lambda x: x[1], reverse=True)
    keep_num = self.roundmap[self.currentround]
    keeps = sorter_arr[:keep_num]
    
    dupes = []
    counter = 0
    while keep_num+counter < len(arr) and sorter_arr[keep_num+counter][1] == sorter_arr[keep_num-1][1]:
      dupes.append(sorter_arr[keep_num+counter])
      counter += 1
    
    if keep_duplicates:
      keeps += dupes;
    elif len(dupes) > 0:
      from random import random
      while keeps[-1][1] == dupes[0][1]:
        dupes.append(keeps.pop())
      while len(keeps) != keep_num:
        keeps.append(dupes.pop(int(random()*len(dupes))))
    
    self.results.append(dict([(contestant[0], 0) for contestant in keeps]))
  
  """
  ' PURPOSE
  '   Returns the voting results for a speecified round. If
  '   No round is specified, then the most recent is returned.
  ' PAREMETERS
  '   <int **kwarg round>
  ' RETURNS
  '   The voting dict for the specified round
  """
  def getResults(self, num=None):
    if not num:
      num = self.currentround
    return self.results[num]
  
  """
  ' PURPOSE
  '   Closes voting. Effectively stopping all devices from voting.
  '   It also ends the current round, locking in all votes.
  ' PARAMETERS
  '   <bool **kwarg keep_duplicates>
  ' RETURNS
  '   Boolean
  '     For details see delegated method
  ' NOTES
  '   1. see updatesResults for the 'keep_duplicates' explanation
  """
  def closeVoting(self, keep_duplicates=True):
    self.voting = False
    return self.nextRound(keep_duplicates=keep_duplicates)
  
  """
  ' PURPOSE
  '   Opens voting. Effectively allowing all devices to vote
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def openVoting(self):
    self.voting = True
    self.put()
  
  """
  ' PURPOSE
  '   Votes for a contestant.
  ' PAREMETERS
  '   Contestant name
  ' RETURNS
  '   Boolean
  '     True ~ The vote was cast
  '     False ~ Voting is closed or the contestant doesn't exist.
  """
  def vote(self, contestant):
    if not self.voting:
      return False
    if not contestant in self.results[self.currentround]:
      return False
    self.results[self.currentround][contestant] += 1
    self.put()
    return True


"""
' PURPOSE
'   Creates a new game with the given contestants and voting procedure
' PARAMETERS
'   <String[] contestants>
'   <int[] roundmap>
' RETURNS
'   <Game extends ndb.Model>
' NOTES
'   1. It will raise a BaseException if the round map is invalid
'   2. All duplicates are removed after the validity of the round map is confirmed
"""
def create(contestants, roundmap):
  
  inorder = True
  last = len(contestants)
  for num in roundmap:
    if last < num and last != None:
      inorder = False
      break
    last = num
  
  if not inorder:
    raise BaseException("Round map expects more players in a round than are present.")
  
  roundmap = sorted(list(set(roundmap)), reverse=True)
  
  game = Game()
  game.roundmap = roundmap
  game.currentround = 0
  game.voting = False
  game.results = [dict([(contestant, 0) for contestant in contestants])]
  game.put()
  return game
  