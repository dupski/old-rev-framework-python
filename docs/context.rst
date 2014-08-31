.. _understanding-context:

===================================
Understanding and Using ``context``
===================================

Summary
=======

Many methods within the RevFramework accept a ``context`` parameter, and it
is good practise to make use of it in your own methods. This section explains
why.

Imagine we've created a model, and overriden the ``update`` method so it
recalculates some values every time a record is updated. ::
   
   def update(self, id, vals, context={}):
      super(MyModel, self).update(id, vals, context)
      self._recalculate_values(id)

   def _recalculate_values(self, id):
      
      # Do some calculations...
      
      # Save changes
      self.update(id, new_vals)

Can you see the problem with the above code? The problem is that we have
created an *infinite loop*, because any calls to the ``update`` function will
call the ``_recalculate_values`` function, which in-turn calls the ``update``
function again, and so the cycle continues!

So **context** is a way of passing additional, *contextual information* between
functions to help control their behaviour. Lets re-write the example above to
make use of context. ::
   
   def update(self, id, vals, context={}):
      super(MyModel, self).update(id, vals, context)
      
      if 'no_recalculate' not in context:
         self._recalculate_values(id)

   def _recalculate_values(self, id):
      
      # Do some calculations...
      
      # Save changes
      self.update(id, new_vals, {'no_recalculate' : True})

In the example above, we are using the context variable to pass a
*no_recalculate* parameter to the ``update`` method. This means that when the
``update`` method gets called for the second time, it won't then re-call the
``_recalculate_values`` method and cause an infinite loop.

There are lots of other times when ``context`` is useful. The remainder of this
section describes other places where it is important.

Client Context
==============

By default, when the RevClient application makes a request to a server-side API
method, the following context information is provided:

* **userid** - The logged-in user's id
* **tz** - The logged-in user's timezone
* **lang** - The logged-in user's language