<?xml version='1.0' encoding='utf-8'?>
<html xmlns:kid="http://naeblis.cx/ns/kid#">
  <?kid
  	# set my indentation	
  	
  	# Notice that this (?kid...?) block is just inside (html).  That makes
  	# it "local-level", where the 'fields' variable is available.
  	# If this block were outside (html), then fields would not be available yet.
  	
  	name = fields.get('name') or 'stranger'
  ?>
  <head>
    <title>Kid Form Demo</title>
  </head>
  <body>
    <h1>Kid Form Demo</h1>
    <p>
    	Hello <b kid:content="name"/>, how are you?
    </p>

    <form action="" method="get">
    	Enter your name here:
		<input type="text" name="name" />
		<input type="submit" name="Submit" value="Submit" />
	</form>
  </body>
</html>
