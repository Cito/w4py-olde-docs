<?xml version='1.0' encoding='utf-8'?>
<?kid #
import os
import sys
import time
uname = os.uname()

?>
<html xmlns:kid="http://naeblis.cx/ns/kid#">
  <head>
    <title>System Information</title>
  </head>
  <body>
    <h1>Kid System Info Demo</h1>
    <p>
      Time: <b kid:content="time.strftime('%C %c')"/>
    </p>


    <h2>Useful Variables</h2>
    <table border="1" cellspacing="0" >
      <tr>
        <th>local variable</th>
        <th>value</th>
        <th>description</th>
      </tr>
      <tr>
        <td><b>fields</b></td>
        <td kid:content="fields"/>
        <td>This contains the PUT/GET variables you need to access for forms.</td>
      </tr>
      <tr>
        <td><b>req</b></td>
        <td kid:content="req"/>
        <td>Rarely used unless you need special info about the request.</td>
      </tr><tr>
        <td><b>resp</b></td>
        <td kid:content="resp"/>
        <td>You might want to set special HTTP header types using this.  Or cookies too.</td>
      </tr>
      <tr>
        <td><b>__file__</b></td>
        <td kid:content="__file__"/>
        <td></td>
      </tr>
      <tr>
        <td><b>req.serverSidePath()</b></td>
        <td kid:content="req.serverSidePath()"/>
        <td></td>
      </tr>
      <tr>
        <td><b>os.path.abspath(__file__)</b></td>
        <td kid:content="os.path.abspath(__file__)"/>
        <td></td>
      </tr>
    </table>
    


    <h2>Environment</h2>
    <table>
      <tr kid:for="k,v in os.environ.items()">
        <td kid:content="k"/>
        <td kid:content="v"/>
      </tr>
    </table>
    
    
  </body>
</html>
