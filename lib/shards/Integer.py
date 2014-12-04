"""
' Common Package Imports  
"""
from google.appengine.ext import ndb
import generic


"""
' PURPOSE
'   The ndb.Model for Integer Shards
"""
class IntegerShard(ndb.Model):
  value = ndb.IntegerProperty(indexed=False)
  
  
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
    return 0
  
  
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
  '   Add an amount to this shard
  ' PARAMETERS
  '   <int amount>
  ' RETURNS
  '   Nothing
  ' PUTS
  '   1 ~ on change
  """
  def add(self, amount):
    if amount == 0:
      return
    self.value = self.getValue() + amount
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
  return generic.getOrCreate(IntegerShard, name, namespace=namespace)