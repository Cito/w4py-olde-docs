from Common import *
from Component import Component


class HierarchicalComponent(Component):
	'''
	This class adds the ability for components to be nested in a hierarchical fashion.
	'''
	
	
	## Init ##
	
	def __init__(self):
		Component.__init__(self)
		self._subcomponents = []
		self._transaction = None


	## Structure ##

	def subcomponents(self):
		''' Returns a _copy_ of the list of the subcomponents. Protecting the original list is important as the class internals may depend on it. For components with no subcomponents, this method may return None or []. '''
		return self._subcomponents[:]

	def addSubcomponent(self, newComponent):
		self._subcomponents.append(newComponent)

	def removeSubcomponent(self, component):
		self._subcomponents.remove(component)

	def setSubcomponents(self, newList):
		self._subcomponents = newList


	## Access ##
	
	def transaction(self):
		''' Returns the transaction during a transaction. '''
		return self._transaction


	## Request-response cycles ##

	def awake(self, trans):
		''' Stores a reference to the transaction, then sends awake() to all subcomponents. '''
		self._transaction = trans
		for component in self._subcomponents:
			component.awake(trans)
	
	def respond(self, trans):
		''' Sends this message to all subcomponents. '''
		for component in self._subcomponents:
			component.respond(trans)

	def sleep(self, trans):
		''' Sends sleep() to all subcomponents in reverse order, then release the component's reference to the transaction. '''
		components = self._subcomponents[:]
		components.reverse()
		for component in components:
			component.sleep(trans)
		self._transaction = None
