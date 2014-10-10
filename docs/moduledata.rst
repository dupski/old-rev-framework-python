.. _module-data:

===========
Module Data
===========

Overview
========

The Rev Framework is designed to allow app builders to create reusable
components that can be completely customised for each application they are used
in, but without needing to modify the original component.

One of the ways this is achieved is by storing the majority of the metadata of
the component, such as the specification of its form and list views, in the
database (and then caching it in-memory at run time).

The framework then allows modules that 'depend' on the re-usable component, to
modify the component's metadata to match the specific app's requirements. 


The Module 'data' folder
========================

TODO:

 * YAML File Format
 
 * Record Format (model name, id, etc.)