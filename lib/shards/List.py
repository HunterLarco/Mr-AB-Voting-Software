"""
' Common Package Imports  
"""
from google.appengine.ext import ndb
import generic


"""
' PURPOSE
'   A decorator that's presence indicates to the DynamicShardManager
'   that this method ir run statically and will access shards as it wishes,
'   not randomly as default.
"""
def static(funct):
  setattr(funct, '__static__', True)
  return funct


"""
' PURPOSE
'   The ndb.Model for Integer Shards
"""
class ListShard(ndb.Model):
  value = ndb.PickleProperty(indexed=False)
  
  
  """
  ' PURPOSE
  '   Removes all instances of a given 'item' from
  '   The provided shard manager. The static decorator
  '   will copy the method into the manager itself. Call it from
  '   the manager.
  ' PARAMETERS
  '   <DynamicShardManager manager>
  '   <Object item>
  ' RETURNS
  '   Nothing
  """
  @classmethod
  @static
  def remove(self, manager, item):
    keys = manager.getAllShardKeys()
    for shard in ndb.get_multi(keys):
      if shard == None:
        continue
      
      DATA = dict(tries=0)
      shard._remove(DATA, item)
      
      if DATA['tries'] > 1:
        manager._increase_shards(2)
      
      
  """
  ' PURPOSE
  '   A private method...
  '   Removes a given item from the data in this shard
  '   While also monitoring for transaction failure. On
  '   Failure more shards will be allocated to the corresponding
  '   Shard Manager.
  ' PARAMETERS
  '   <dict retrydata>
  '   <Object item>
  ' RETURNS
  '   Nothing
  ' NOTES
  '   retrydata is used to count retries by utilizing pass-by-reference
  """
  @ndb.transactional
  def _remove(self, retrydata, item):
    if item in self.value:
      self.value.remove(item)
      self.put()
    retrydata['tries'] += 1
  
  
  """
  ' PURPOSE
  '   Returns the default value a single shard
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  @classmethod
  def getDefaultValue(self):
    return []
  
  
  """
  ' Purpose
  '   Get the current value of this shard
  ' PARAMETERS
  '   None
  ' RETURNS
  '   Nothing
  """
  def getValue(self):
    return self.__class__.getDefaultValue() if self.value == None else self.value
  
  
  """
  ' PURPOSE
  '   When totaling the value for all shards connected,
  '   this function calculate that value which is stored
  '   in obj.value
  ' PARAMETERS
  '   <DynamicShardManager.ValueObject  obj>
  ' RETURNS
  '   Nothing
  ' NOTES
  '   obj is used to enable pass-by-reference data
  '   instead of pass-by-value so that all functions
  '   leave persistant changes
  """
  def computeValue(self, obj):
    obj.value += self.getValue()
  
  
  """
  ' PURPOSE
  '   Add an item to this shard
  ' PARAMETERS
  '   <int amount>
  ' RETURNS
  '   Nothing
  ' PUTS
  '   1 ~ on change
  """
  def add(self, item):
    value = self.getValue()
    value.append(item)
    self.value = value
    self.put()



"""
' PURPOSE
'   Given a name and namespace, return a Shard Manager if one exists, or
'   create a new one if it doesn't and return that
' PARAMETERS
'   <String name>
'   <String **kwarg namespace>
' RETURNS
'   A ndb.Model instance
' PUTS
'   1 - when a new DynamicShard is created
"""
def getOrCreate(name, namespace=None):
  return generic.getOrCreate(ListShard, name, namespace=namespace)