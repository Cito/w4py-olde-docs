<?xml version='1.0' encoding='utf-8'?>
<?kid #
import os

curdir = os.path.dirname( __file__ )
?>
<html xmlns="http://www.w3.org/1999/xhtml"
	  xmlns:kid="http://naeblis.cx/ns/kid#"
>
  <head>
	<title>A Kid Template</title>
  </head>
  <body>
  
  	<h1>Contents of folder: <span kid:replace="curdir" /></h1>
  	
  	<p>
		<span kid:omit="" kid:for="f in os.listdir(curdir)" >
			<a href="{f}"><span kid:replace="f"/></a><br/>
		</span>
	</p>
  </body>
</html>