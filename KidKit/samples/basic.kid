<?xml version='1.0' encoding='utf-8'?>
<?kid
# This is the first example in the tutorial.

# import some stuff
import time
?>
<html xmlns="http://www.w3.org/1999/xhtml"
	  xmlns:kid="http://naeblis.cx/ns/kid#"
>
  <head>
	<title>A Kid Template</title>
  </head>
  <body>
	<p>
	  The current time is 
	  <span kid:content="time.strftime('%C %c')">
		Locale Specific Date/Time
	  </span>.
	</p>
  </body>
</html>