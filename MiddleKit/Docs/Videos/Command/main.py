from MiddleKit.Run.MySQLObjectStore import MySQLObjectStore
from Middle.Movie import Movie
from Middle.Person import Person
from Middle.Role import Role


def main():
    # Gain access to our package
    import os, sys
    sys.path.insert(1, os.path.abspath(os.pardir))

	# Set up the store
#	store = MySQLObjectStore(user='user', passwd='password')
	store = MySQLObjectStore()
	store.readModelFileNamed('Videos')

	movie = Movie()
	movie.setTitle('The Terminator')
	movie.setYear(1984)
	movie.setRating('r')
	store.addObject(movie)

	james = Person()
	james.setName('James Cameron')
	james.setBirthDate('8/16/1954')
	movie.addToDirectors(james)

	ahnuld = Person()
	ahnuld.setName('Arnold Schwarzenegger')
	ahnuld.setBirthDate('7/30/1947')
	store.addObject(ahnuld)

	terminator = Role()
	terminator.setKaracter('Terminator')
	terminator.setPerson(ahnuld)
	movie.addToCast(terminator)

	store.saveChanges()

if __name__=='__main__':
	main()
