(function(){
  
  GATEWAY = '/api/';

  function XMLHTTPInstance(data, callback, onerror){
    var timeMemory,
        argumentMemory,
        usedfunct,
        callback = callback || new Function(),
        onerror = onerror || new Function(),
        data = data || {};

    function CreateCorsRequest(method, url){
      var xhr = !!window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject("Microsoft.XMLHTTP");
      if ("withCredentials" in xhr) {
        xhr.open(method, url, true);
      } else if (typeof XDomainRequest != "undefined") {
        xhr = new XDomainRequest();
        xhr.open(method, url);
      } else {
        // CORS not supported.
        xhr = null;
      }
      return xhr;
    }

    function SetupRequest(requestargs, method, url){
      if(requestargs.callee.caller != RequestJSRetry)
        timeMemory = 0;
      usedfunct = requestargs.callee;
      argumentMemory = requestargs;
      var xmlhttp = CreateCorsRequest(method, url);
      if(!xmlhttp){
        OnError(new ErrorEvent(-1, 'Cors Not Enabled In This Browser'));
        return;
      }
      xmlhttp.onreadystatechange = OnResponse;
      xmlhttp.onerror = OnError;
      return xmlhttp;
    }

    function OnResponse(event){
      var xmlhttp = event.target;
      if (xmlhttp.readyState==4){
        if(xmlhttp.status==200){
          var data = JSON.parse(event.target.response);
          if(data.stat == 'fail'){
            onerror(new ErrorEvent(data.code, data.message, data));
          }else{
            callback(data);
          }
        }else{
          onerror(new ErrorEvent(-1, 'Unknown Server Error'));
        };
      };
    }

    this.post = function(url){
      var xmlhttp = SetupRequest(arguments, 'POST', url);
      if(!xmlhttp) return;
      xmlhttp.send(JSON.stringify(data));
    }

    this.get = function(url){
      var xmlhttp = SetupRequest(arguments, 'POST', url);
      xmlhttp.send();
    }

    function OnError(event){
      onerror(new ErrorEvent(-2, 'Request Error!'));
    }

    function RequestJSRetry(){
      usedfunct.apply(this,argumentMemory);
    };

    var ErrorEvent = function(errorcode,message,response){
      var event = this;
      this.__response__ = response;
      this.stat = 'fail';
      this.code = errorcode;
      this.message = message;
      this.retry = function(){
        timeout = Math.pow(2,timeMemory);
        timeMemory++;
        if(timeout>60){timeout=60};
        console.warn('Retrying Request In "'+timeout+'" Seconds');
        setTimeout(RequestJSRetry,timeout*1000);
      };
      this.warn = function(message){
        console.warn(message+'\n    Error Code: '+event.code+'\n    Error Message: "'+event.message+'"');
      };
      this.error = function(message){
        console.error(message+'\n    Error Code: '+event.code+'\n    Error Message: "'+event.message+'"');
      };
    };
  }

  window.Request = function Request(url, body, OnSuccess, errormap){
    function __success__(event){
      if(typeof Request.overhead == 'function')
        if(false == Request.overhead(event)) return;
      if(typeof OnSuccess == 'function') OnSuccess(event);
    }
    function __error__(event){
      if(typeof Request.overhead == 'function')
        if(false == Request.overhead(event.__response__)) return;
      if(!errormap) errormap = {};
      if(!!errormap.always) errormap.always(event);
      if(!!errormap[event.code]) return errormap[event.code](event);
      if(!!errormap.default) return errormap.default(event);
      console.warn('Unhandled Error');
    }
    var instance = new XMLHTTPInstance(body, __success__, __error__);
    instance.post(GATEWAY+url);
  }
  
})();