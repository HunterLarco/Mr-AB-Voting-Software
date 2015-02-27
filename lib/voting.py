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
  datetime = ndb.DateTimeProperty(auto_now_add=True)
  
  """
  ' PURPOSE
  '   Returns a list of all initially competing contestants
  ' PARAMETERS
  '   None
  ' RETURNS
  '   list
  """
  def getContestants(self):
    return self.getResults(0).keys()
  
  """
  ' PURPOSE
  '   Returns a list of all results for all rounds including the
  '   most recent, even if incomplete.
  ' PARAMETERS
  '   None
  ' RETURNS
  '   list
  """
  def getAllResults(self):
    results = []
    for i in range(self.currentround+1):
      results.append(self.getResults(i))
    return results
  
  """
  ' PURPOSE
  '   Returns whether the game is over
  ' PARAMETERS
  '   None
  ' RETURNS
  '   bool
  """
  def hasWinner(self):
    return self.currentround == len(self.roundmap)
  
  """
  ' PURPOSE
  '   Returns all the winners if and only if the game is over.
  '   If the game isn't over None is returned
  ' PARAMETERS
  '   None
  ' RETURNS
  '   dict ~ See self.getResults for details
  """
  def getWinners(self):
    return self.getResults() if self.hasWinner() else None
  
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
    arr = self.getResults().items()
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
      while len(keeps) != 0 and keeps[-1][1] == dupes[0][1]:
        dupes.append(keeps.pop())
      while len(keeps) != keep_num:
        keeps.append(dupes.pop(int(random()*len(dupes))))
    
    self.results.append([contestant[0] for contestant in keeps])
  
  """
  ' PURPOSE
  '   Returns the voting results for a speecified round. If
  '   No round is specified, then the most recent is returned.
  ' PAREMETERS
  '   <int **kwarg round>
  ' RETURNS
  '   The voting dict for the specified round
  """
  def getResults(self, voteround=None):
    if voteround == None:
      voteround = self.currentround
    out = {}
    for contestant in self.results[voteround]:
      out[contestant] = self.GetVotes(contestant, voteround)
    return out
  
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
    if not self.voting or self.hasWinner():
      return
    self.voting = False
    return self.nextRound(keep_duplicates=keep_duplicates)
  
  """
  ' PURPOSE
  '   Returns whether the voting system is open or closed
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def isVotingOpen(self):
    return self.voting
  
  """
  ' PURPOSE
  '   Opens voting. Effectively allowing all devices to vote
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def openVoting(self):
    if self.voting or self.hasWinner():
      return
    self.voting = True
    self.put()
  
  """
  ' PURPOSE
  '   Votes for a contestant based on their name
  ' PAREMETERS
  '   <str contestant>
  ' RETURNS
  '   Boolean
  '     True ~ The vote was cast
  '     False ~ Voting is closed or the contestant doesn't exist.
  """
  def vote(self, contestant):
    if not self.voting or self.hasWinner():
      return False
    if not contestant in self.results[self.currentround]:
      return False
    self.IncrementVote(contestant)
    return True
  
  """
  ' PURPOSE
  '   Returns the amount of votes for a given contestant and voting round
  '   If the voting round is None then it uses the most current
  ' PARAMETERS
  '   <str contestant>
  '   <int **kwarg voteround>
  ' RETURNS
  '   int
  """
  def GetVotes(self, contestant, voteround=None):
    counter = self.GetVoteCounter(contestant, voteround=voteround)
    return counter.getValue()
  
  """
  ' PURPOSE
  '   Increments the vote in the current voting round for the specified
  '   contestant.
  ' PARAMETERS
  '   <str contestant>
  ' RETURNS
  '   Nothing
  """
  def IncrementVote(self, contestant):
    counter = self.GetVoteCounter(contestant)
    counter.run('add', 1)
  
  """
  ' PURPOSE
  '   Returns the voting shard for the given contestant and voting round.
  ' PARAMETERS
  '   <str contestant>
  '   <int **kwarg voteround>
  ' RETURNS
  '   <Integer extends shards.generic>
  """
  def GetVoteCounter(self, contestant, voteround=None):
    if not voteround:
      voteround = self.currentround
    from shards import Integer
    namespace = self.GenerateShardNamespace(voteround)
    return Integer.getOrCreate(contestant, namespace)
  
  """
  ' PURPOSE
  '   Generates a shard namespace based on this game and given voteround.
  ' PARAMETERS
  '   <int voteround>
  ' RETURNS
  '   str
  """
  def GenerateShardNamespace(self, voteround=None):
    if voteround == None:
      voteround = self.currentround
    string = 'Game<%s>Round<%s>' % (self.key.urlsafe(), voteround)
    from hashlib import sha256
    return sha256(string).hexdigest()


"""
' PURPOSE
'   Creates a new game with the given contestants and voting procedure
' PARAMETERS
'   <str[] contestants>
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
  contestants = list(set(contestants))
  
  game = Game()
  game.roundmap = roundmap
  game.currentround = 0
  game.voting = False
  game.results = [contestants]
  game.put()
  return game


"""
' PURPOSE
'   Returns the game associated with the given identifier
' PARAMETERS
'   <str identifier>
' RETURNS
'   <Game extends ndb.Model>
"""
def get(identifier):
  identifier = int(identifier)
  return Game.get_by_id(identifier)


"""
' PURPOSE
'   Returns the most recently created game
' PARAMETERS
'   None
' RETURNS
'   <Game extends ndb.Model>
"""
def getCurrent():
  return Game.query().order(-Game.datetime).get()