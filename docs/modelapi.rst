.. _model-api:

============
RevModel API
============

Creating Models
===============

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

Using Models in Application Code
================================

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

Searching and Reading Data
--------------------------

.. py:function:: find([criteria={}[, read_fields=[][, order_by=None[, limit=0[, offset=0[, count_only=False[, context={}]]]]]]])

   The ``find`` function is responsible for **finding and retrieving** data from
   the database
   
   You can return all data from a model simply using the following code: ::
   
      mymodel.find({}, read_fields='*')
   
   If you just want to count the number of matching records, you can use the
   ``count_only`` option, like so: ::
   
     people.find({'first_name' : 'Bob'}, count_only=True)
   
   ``find()`` returns a list of dictionaries containing the matching records, or
   if ``count_only`` is set, just the number of matching records.
   
   **Parameters:**
   
   * **criteria** - the criteria to use (TODO: Expand on this!)
   * **read_fields** - a list of field names to return, or the string '*' to
     return all fields. NOTE: '_id' is always returned.
   * **order_by** - a list of (field_name, direction) pairs (e.g.
     ``order_by=[('gender','desc'), ('first_name', 'asc')]``)
   * **limit** - the maximum number of records to return
   * **offset** - how many records to offset the start of the results from. This
     usefus when e.g. you have already retrieved the first 20 results and you
     want to retrieve the next 20 (in which case you'd set ``offset=20``)
   * **count_only** - set this to True if you just want to return the total
     number of matching records
   * **context** - See :ref:`understanding-context`

Creating, Updating and Deleting Data
------------------------------------

.. py:function:: create(vals[, context={}])

   Creates a new record, and returns the new **id** of the created record.
   
   Any value errors will raise a ``rev.core.exceptions.ValidationError``
   
   **Parameters:**
   
   * **vals** - this should be a dictionary object containing the data that you
     want to create in the database
   * **context** - See :ref:`understanding-context`

.. py:function:: update(ids, vals[, context={}])
   
   Updates one or more existing records using the new values specified in vals,
   and returns True on success.
   
   Any value errors will raise a ``rev.core.exceptions.ValidationError``
   
   **Parameters**
   
   * **ids** - a list of record ids to update
   * **vals** - the fields and values that you want to set
   * **context** - See :ref:`understanding-context`

.. py:function:: delete(ids, vals[, context={}])
   
   Deletes one or more existing records by their id.
   Returns True on success.
   
   **Parameters**
   
   * **ids** - a list of the record ids to be deleted
   * **context** - See :ref:`understanding-context`