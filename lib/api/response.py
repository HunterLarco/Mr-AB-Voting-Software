"""
' Error Responses
"""
__ERROR__RESPONSES__ = {
  000 : "An unexpected error occurred",
  001 : "Parameter Missing",
  002 : "Access Denied",
  003 : "Error Code 404",

  100 : "Game %s Doesn't Exist",
  101 : "Voting is Closed"
}


"""
' PURPOSE
'   Throws an error response, consisting of a error code
'   and error message.
' PARAMETERS
'   <int code>
'   <Tuple dataStruct>
'   <boolean **kwarg compiled>
' RETURNS
'   A dict
' NOTES
'   1. the 'dataStruct' is used to customize information in an error message
'   2. when compiled is true the dict is serialized into JSON format
"""
def throw(code, dataStruct=(), compiled=False):
  response = {
    'stat' : 'fail',
    'code' : code,
    'message' : __ERROR__RESPONSES__[code] % dataStruct
  }
  return compile(response) if compiled else response


"""
' PURPOSE
'   Returns a successful response. May take additional data to add to the response.
' PARAMETERS
'   <Dict **kwarg data>
' RETURNS
'   A dict
"""
def reply(data={}):
  data['stat'] = 'ok'
  return data


"""
' PURPOSE
'   JSON serializes a given dict
' PARAMETERS
'   <Dict JSON>
' RETURNS
'   A string
"""
def compile(JSON):
  import json
  return json.dumps(JSON)