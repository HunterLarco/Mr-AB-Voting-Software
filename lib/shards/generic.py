# ADAPTED FROM <https://developers.google.com/appengine/articles/sharding_counters>

"""
' Common Package Imports  
"""
from google.appengine.ext import ndb


"""
' PURPOSE
'   Given a ShardModel and shard manager name, create
'   a new Manager for it if none exists, or return
'   the current one.
' PARAMETERS
'   <ndb.Model ShardModel>
'   <String name>
'   <String **kwarg namespace>
' Returns
'   <ndb.Model DynamicShardManager> instance
"""
def getOrCreate(ShardModel, name, namespace=None):
  MANAGER_KEY_TEMPLATE = 'shard-manager:-name:{}-modelname:{}'
  manager = DynamicShardManager.get_or_insert(MANAGER_KEY_TEMPLATE.format(name, ShardModel.__name__), namespace=namespace)
  manager.__setModel__(ShardModel)
  return manager


"""
' PURPOSE
'   The ndb.Model that runs all the shards and tracks data.
'   It's used for everything.
' NOTES
'   Use the 'getOrCreate' method to access DynamicShardManagers
"""
class DynamicShardManager(ndb.Model):
  num_shards = ndb.IntegerProperty(default=20)
  
  SHARD_KEY_TEMPLATE = 'shard-type:({})-name:({})-id:({:d})'
  __shardmodel__ = None
  
  
  """
  ' PURPOSE
  '   A private method that sets the Shard ndb Model
  '   for this ShardManager
  ' PARAMETERS
  '   <ndb.Model ShardModel>
  ' RETURNS
  '   Nothing
  ' NOTES
  '   This is needed because arguments cannot be sent to the
  '   constructor when using .get_or_insert
  """
  def __setModel__(self, ShardModel):
    self.__shardmodel__ = ShardModel
  
  
  """
  ' PURPOSE
  '   A simple object used for pass-by-reference
  '   function calling so that as function mutate the
  '   data, it is persistant.
  """
  class ValueObject(object):
    pass
  
  
  """
  ' PURPOSE
  '   Returns the current value of this shard manager.
  '   Calculated by the shards themselves. What the value means
  '   may vary.
  ' PARAMETERS
  '   None
  ' Returns
  '   The shard manager's 'value'
  """
  def getValue(self):
    name = self.getName()
    value = self.ValueObject()
    value.value = self.__shardmodel__.getDefaultValue()
    all_keys = self.getAllShardKeys()
    for shard in ndb.get_multi(all_keys):
      if shard is not None:
        shard.computeValue(value)
    return value.value
  
  
  """
  ' PURPOSE
  '   Runs a particular function on a random shard, such as Add on
  '   an Integer shard counter
  ' PARAMETERS
  '   <String functname>
  ' Returns
  '   Nothing
  ' NOTES
  '   This function increases the amount of shards if a transaction
  '   fails for memory locks.
  """
  def run(self, functname, *args, **kwargs):
    # run a static function
    funct = getattr(self.__shardmodel__, functname)
    if hasattr(funct, '__static__') and getattr(funct, '__static__'):
      funct(self, *args, **kwargs)
      return
    
    DATA = dict(tries=0)
    self._run(DATA, functname, args, kwargs)
    
    if DATA['tries'] > 1:
      self._increase_shards(2)


  """
  ' PURPOSE
  '   The private method that handles accessing random
  '   shards and mutating their data.
  ' PARAMETERS
  '   <dict retrydata>
  '   <String functname>
  '   <*args args>
  '   <**kwargs args>
  ' RETURNS
  '   Nothing
  """
  @ndb.transactional
  def _run(self, retrydata, functname, args, kwargs):
    import random
    
    name = self.getName()
    num_shards = self.num_shards
    
    index = random.randint(0, num_shards - 1)
    shard_key_string = self.SHARD_KEY_TEMPLATE.format(self.__shardmodel__.__name__, name, index)
    shard = self.__shardmodel__.get_by_id(shard_key_string, namespace=self.getNamespace())
    if shard is None:
        shard = self.__shardmodel__(id=shard_key_string, namespace=self.getNamespace())
   
    funct = getattr(shard, functname)
    if funct == None:
      return
    
    funct(*args, **kwargs)
   
    retrydata['tries'] += 1
  
  
  """
  ' PURPOSE
  '   Returns the serialized name associated with this counter
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def getName(self):
    return self.key.id()
  
  
  """
  ' PURPOSE
  '   Returns the namespace of this counter
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def getNamespace(self):
    return self.key.namespace()
  
  
  """
  ' PURPOSE
  '   Returns all the possible shard keys associated with this counter
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def getAllShardKeys(self):
    name = self.getName()
    shard_key_strings = [self.SHARD_KEY_TEMPLATE.format(self.__shardmodel__.__name__, name, index)
                         for index in range(self.num_shards)]
    return [ndb.Key(self.__shardmodel__, shard_key_string, namespace=self.getNamespace())
            for shard_key_string in shard_key_strings]
  
  
  """
  ' PURPOSE
  '   A 'private' method that increases the amount of shards by the
  '   provided amount.
  ' PARAMETERS
  '   <int amount>
  ' RETURNS
  '   Nothing
  ' PUTS
  '   1 - on changing the amount of shards
  """
  @ndb.transactional
  def _increase_shards(self, amount):
    name = self.getName()
    if amount > 0:
      self.num_shards += amount
      self.put()
      

  """
  ' PURPOSE
  '   Provides some basic statistics about this counter
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def profile(self):
    all_keys = self.getAllShardKeys()
  
    keycount = 0

    for counter in ndb.get_multi(all_keys):
        if counter is not None:
            keycount += 1
  
    return dict(
      shards_available = len(all_keys),
      shards_used = keycount
    )