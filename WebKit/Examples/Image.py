from WebKit.HTTPContent import HTTPContent
try:
	import gd # GD module
except ImportError:
	gd = None
	try:
		import PIL # Python Imaging Library
		import PIL.Image
		import PIL.ImageDraw
		pil = PIL
	except ImportError:
		pil = None


class Image(HTTPContent):
	"""Dynamic image generation example.

	This example creates an image of a sinusoid.

	For more information on generating graphics, see
	http://python.org/topics/web/graphics.html.

	This example works with both PIL and GD.

	"""

	def defaultAction(self):
		if gd or pil:
			image = self.generatePNGImage()
			res = self.response()
			res.setHeader("Content-Type", "image/png")
			res.setHeader("Content-Length", str(len(image)))
			# Uncomment the following to suggest to the client that the
			# result should be saved to a file, rather than displayed in-line:
			# res.setHeader('Content-Disposition', 'attachment; filename=foo.png')
			self.write(image)
		else:
			self.writeln('<html><head><title>Image Demo</title>'
				'<body style="background-color:white;padding:16;font-family:sans-serif">'
				'<h2>WebKit Image Generation Demo</h2>'
				'<h4 style="color:red">Sorry:'
					' This page requires the Python Imaging Library or the GD module.</h4>'
				'</p>See <a href="http://python.org/topics/web/graphics.html">'
				'python.org/topics/web/graphics.html</a>.</p></body></html>')

	def generatePNGImage(self):
		"""Generate and return a PNG image using gdmodule."""
		import StringIO
		from math import sin, pi
		X, Y = (320, 160)
		def T(p):
			# map coordinates: (x=0..2pi, y=-1..1) => (0..X, Y..0)
			return (int((p[0]/(2*pi))*X), int(Y - ((p[1]+1)/2.0)*Y))
		white, black, blue = (255, 255, 255), (0, 0, 0), (0, 0, 255)
		if gd:
			im = gd.image((X, Y))
			white, black, blue = map(im.colorAllocate, (white, black, blue))
			font = gd.gdFontLarge
		else:
			im = pil.Image.new('RGB', (X, Y), white)
			draw = pil.ImageDraw.Draw(im)
		def text(pos, string, color):
			pos = T(pos)
			if gd:
				im.string(font, pos, string, color)
			else:
				draw.text(pos, string, color)
		text((2.7, 0.8), 'y=sin(x)', black)
		def lines(points, color):
			points = map(T, points)
			if gd:
				im.lines(points, color)
			else:
				draw.line(points, color)
		lines(((0,0), (2*pi, 0)), black) # x-axis
		lines(((0,-1), (0,1)), black) # y-axis
		def f(x): # sin function
			return (x, sin(x))
		lines(map(f, map(lambda x: x*2*pi/X, xrange(X+1))), blue)
		f = StringIO.StringIO()
		if gd:
			im.writePng(f)
		else:
			im.save(f, 'png')
		return f.getvalue()
