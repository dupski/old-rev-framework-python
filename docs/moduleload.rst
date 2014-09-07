.. _module-load-cycle:

=============
Module System
=============

Overview
========

The Rev Framework ships with an extremely powerful and flexible module system
that allows re-usable software components to be built, which can easily be
incorporated, extended and customised inside other components.

The primary aims of the module system are:

 * Loose coupling of modules, so standard components can be easily re-used
   in multiple applications without modification

 * Dependency tracking and resolution. The system should be able to
   automatically install all dependencies when installing a new module, or
   when updating it (including other Rev modules)

 * Easy upgrades during development and in the live environment (no messing
   about with migration files!!)

 * All aspects of modules (including the Rev Core modules) should be extensible,
   allowing developers maximum flexibility

Components of a Rev Module
==========================

The Folder
----------

A Rev Module consists of a folder inside one of the folders specified in your
``module_path`` setting in the Rev Configuration (TODO: Document that!)

The name of the folder you create is very important:

 * The folder name determines the **module name**, which is then stored in the
   database, and used to reference your module from other modules.
   
 * It is important that your module name does not conflict with any Python
   standard module names, otherwise you wont be able to use those python
   modules!
   
For these reasons, we recommend choosing a name with a prefix, for example
``myapp_customers`` and ``myapp_products``.

The standard for all python modules is to use **lowercase only** for the folder
name.

The Configuration File
----------------------

There are a minimum of two files required to turn your folder into a valid Rev
Module:

 * **__init__.py** - All python modules must have one of these! This can be just
   an empty text file.

 * **__rev__.conf** - The configuration file that tells the Rev Framework
   about your module

Below is an example ``__rev__.conf`` which contains the minimum information
required: ::

   # MyApp (TM) - Customers Module configuration file
   
   name = "MyApp Customers Module"
   version = "1.0"
   depends = ['rev_base', 'myapp_base']

As you can see, the ``__rev__.conf`` file uses python-syntax, so data structures
such as arrays and dictionaries are possible, and comments are added by putting
a ``#`` at the start of the line.

Other Bits TODO... :)
---------------------

Module Load Process
===================

The Rev Framework's module system has a number of hooks that allow you to
implement custom behaviour before, during and after all the modules are loaded.

This section describes Rev's module load cycle and the hooks available!

Module Load Stages
------------------

 * **Metadata Update** - When the Rev Framework starts, after loading its
   configuration and connecting to the database, it scans all of the module
   folders on the ``module_path``, and checks that all the information in the
   ``__rev__.conf`` files matches what is in the database.
   
 * **Schedule Updates** - Depending on various factors (such as command line
   switches, or module version changes), the system may mark modules as 'To Be
   Installed', 'To Be Updated' or 'To Be Removed'. The user can then accept or
   reject any changes before they are applied.
 
 * **Boot Modules** - Once the module metadata has been refreshed, and any
   required install / update / remove proceedures have been selected, the
   system then boots each module in turn, in dependency order (using the
   ``depends`` information from the ``__rev__.conf`` files).

Module Boot Stages
------------------

This section describes the boot process for a particular module. This process
is repeated for every installed module in the dependency tree.

 * **Module Import** - The first stage in loading a module is for it to be
   'imported'. This is a standard Python import, so the  ``__init__.py`` file
   will be run at this stage.
   
 * **Load Models** - The next stage is to load all the models that the module
   contains (all sub-classes of RevModel). As part of this process, any missing
   database collections, constraints and indexes will be created
 
 * **Load Data** - The final stage of the module boot process is to make sure
   any standard data that the module comes with is loaded into the database.
   When this stage completes, the ``db_version`` property of the module will
   be updated to match the ``version`` in the module's ``__rev__.conf``

Post Boot Stages
----------------

Once all the individual modules are loaded, the following final actions are
carried out:

 * **Model Verification** - Now that all models are loaded, it is possible to
   verify that all of the specified model relationships are valid.

Module Load Hooks
=================

The Rev Framework allows a number of hook points during the module loading
process.

Module load hooks can be implemented directly within the ``__init__.py`` file of
a module, and any return values will be ignored.

Before Model Load
-----------------

This hook is invoked immediately after the **Module Import** stage and before
the **Load Models** stage. ::

  def before_model_load(registry, db_module_info)

After Model Load
----------------

This hook is invoked immediately after the **Load Models** stage, and before the
before the **Load Data** stage. ::

  def after_model_load(registry, db_module_info)

After Data Load
---------------

This hook is invoked immediately after the **Load Data** stage. ::

  def after_data_load(registry, db_module_info)

After App Load
--------------

This hook is executed on each module in turn, once all the installed modules
have been fully loaded.

  def after_app_load(registry, db_module_info)
