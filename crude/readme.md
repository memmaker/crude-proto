Crude 1.0
=========

a 1.6k loc project.

This is a very flexible but crude Tool, like a hammer. It's a thin wrapper around mongodb.
It is very easy to create new models and all the crud pages will be auto-generated.
You can access all the data via a powerful command line tool similar to Apple's Spotlight.
Of course all the crud operations are also exposed via a JSON API.

Features
========
 - CRUD with a simplified and flexible schema that can be defined at run-time
 - Automatic JSON API for all the data
 - Passwordless login via Sign In with Ethereum
 - Deployed via container
 - Web based command line interface for navigation and search
 - Add multiple data models at once at run-time by copy-pasting a JSON schema
 - Supports custom indices and unique constraints
 - Supports required fields
 - Drop in custom fields

BUGFIX
======
 -

Use-cases
=========
 - Instant Backend for Mobile Apps
 - Knowledge Base
 - Collection Management System
 - Much more...

Nice to have
============

 - More keyboard shortcuts

Clients
=======
 - API Client that supports SiWe


Out of Scope
============
 - SSL / TLS                (use a reverse proxy)
 - Special Field Types      (these are too use-case specific)


Keyboard Shortcuts
==================

Ctrl + Space -> Open crude command line interface

Context Related Shortcuts
=========================

On a "read" page:

"e" -> Edit the entry


Custom field types
==================

1. Add implementation for custom field type in crude/fields in a .py file.
2. Add template macros for custom field type in crude/templates/fields

The filenames without the extension must match.

display_template and display_fields
===================================

display_fields is always needed and defaults to all fields.

display_template is optional and defaults to the " ".join(field) implementation.

If display_template is defined, display_fields should contain all the fields being used by display_template.


Relationships & Indexes
=======================

This example with two models can be copy-pasted into the create model form in crude.

The "indexes" list supports entry with full index syntax of mongodb (see: https://www.mongodb.com/docs/manual/reference/method/db.collection.createIndex/).

The "fts_index_fields" just takes a list of field names and creates a full text index on them.

This example also shows how to use setup relationships.

A relationship is defined by setting the field.type to "related" and adding a key for the "related_model".

If you want to make the reciprocal relationship visible on the other model, you can add a key for the "foreign_relations" on that model.

You can add the reverse relationships there by specifying the "related_model" and "related_field" keys.

[{
    "name": "users",
    "indexes": [
        {
            "keys": {"email": 1},
            "options": {"unique": true}
        }
    ],
    "fts_index_fields": ["name", "email"],
    "fields": [
        {
            "name": "name",
            "type": "text"
            "required": true
        },
        {
            "name": "my_customers",
            "type": "related",
            "related_model": "customers"
        },
        {
            "name": "email",
            "type": "email"
        }
    ]
},
{
    "name": "customers",
    "fields": [
        {
            "name": "name",
            "type": "text"
        }
    ],
    "foreign_relations": [
        {
            "name": "works_for",
            "related_model": "users",
            "related_field": "my_customers"
        }
    ]
}]

Compound IDs
============

References to related entries are stored in a so called compound ID.
This is a string that contains the model name and the ID of the related entry.

For example:
products/62e02a681841fe7d8364f830 or companies/62e02a5c1841fe7d8364f82f


Valid Field Types
=================

'related',
'checkbox',
'color',
'date',
'datetime-local',
'email',
'file',
'hidden',
'image',
'month',
'number',
'password',
'range',
'tel',
'text',
'time',
'url',
'week'
