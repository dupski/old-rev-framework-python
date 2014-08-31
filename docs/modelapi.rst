.. _model-api:

============
RevModel API
============

RevModel is the base class of all data models in a RevFramework app. The code
snippet below shows an example of creating a model.::

	from rev.core.models import RevModel
	import rev.core.fields
	
	COLOURS = [
		('red', 'Red'),
		('green', 'Green'),
		('blue', 'Blue'),
	]
	
	class MyModel(RevModel):
		_name = 'myapp.model'
		_description = 'A Data Model for use in my application'
		
		# Data fields
		item_name = fields.TextField('Item Name')
		colour = fields.selection('Colour', COLOURS)
		size_length = fields.FloatField('Length (cm)')
		size_width = field.FloatField('Width (cm)')


The following code snippet shows how the above model can then be used in
application code.::

	mymodel = self.registry.get('myapp.model')
	
	# Find items that have length greater than ($gt) 10cm
	items = mymodel.find({'size_length' : {'$gt' : 10}})
	
	# Print out the names of all the matching items
	for item in items:
		print(item.item_name)


RevModel Methods
================

The code snippet above shows the use of the **find()** method. Of course there
are many more methods available for RevModel and these are listed below:

.. py:function:: create(vals[, context={}])

   Creates a new record, and returns the new **id** of the created record.
   
   Any value errors will raise a ``rev.core.exceptions.ValidationException``
   
   **Parameters:**
   
   * **vals** - this should be a dictionary object containing the data that you
     want to create in the database
   * **context** - See :ref:`understanding-context`

.. py:function:: update(id, vals[, context={}])
   
   Updates an existing record, using the new values specified in vals, and
   returns True on success.
   
   Any value errors will raise a ``rev.core.exceptions.ValidationException``
   
   **Parameters**
   
   * **id** - the id of the record to update
   * **vals** - the fields and values that you want to update
   * **context** - See :ref:`understanding-context`