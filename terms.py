# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess
from wordpress_xmlrpc import *
from wordpress_xmlrpc.methods.posts import *
from wordpress_xmlrpc.methods.taxonomies import *
from wordpress_xmlrpc.methods.users import *
import common, sublpress, command  

class WordpressManageTaxesCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows the user a list of WordPress taxonomies, or for a specific post type"""
	def __init__(self, *args, **kwargs):
		super(WordpressManageTaxesCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetTaxonomies())

		# add the thread to the list
		self.wc.add_thread(thread)

	""" Called when a thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		self.taxes = result
		#self.options = ['New Taxonomy']
		self.options = []

		for tax in self.taxes:
			self.options.append(tax.name)

		self.wc.show_quick_panel(self.options, self.panel_callback)

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		#if index == 0:
			#self.window.run_command('wordpress_new_term')
			#return

		# loop through all of the retreived taxonomies
		for tax in self.taxes:

			# check for a matching title for the selected quick panel option
			if tax.name == self.options[index]:
				# show the user actions for this taxonomy
				self.window.run_command('wordpress_manage_terms', { 'taxonomy': tax.name })

class WordpressManageTermsCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows the user a list of WordPress terms for a specific taxonomy"""
	def __init__(self, *args, **kwargs):
		super(WordpressManageTermsCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		self.taxonomy = kwargs.get('taxonomy', None)

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetTerms(self.taxonomy))

		# add the thread to the list
		self.wc.add_thread(thread)

	""" Called when a thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		self.terms = result
		self.options = ['New Term']

		for term in self.terms:
			self.options.append(term.name)

		self.wc.show_quick_panel(self.options, self.panel_callback)

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# create new term
		if index == 0:
			self.window.run_command('wordpress_new_term')
			return

		# loop through all terms
		for term in self.terms:
			if term.name == self.options[index]:
				self.window.run_command('wordpress_term_action', {'id': term.id, 'name': term.name, 'taxonomy': self.taxonomy})

class WordpressRenameTermCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows allows the user to rename a taxonomy term """
	def __init__(self, *args, **kwargs):
		super(WordpressRenameTermCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called when the input panel has received input """
	def doDone(self, name):
		# save the old name
		self.old_name = self.term.name

		# assign the new name to this term
		self.term.name = name

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(EditTerm(self.term.id, self.term))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# initialize an empty WordPress term
		self.term = WordPressTerm()

		# grab the id, name, and taxonomy from the commands arguments
		self.term.id = kwargs.get('id', None)
		self.term.name = kwargs.get('name', None)
		self.term.taxonomy = kwargs.get('taxonomy', None)

		# make sure we have a valid term
		if self.term.id == None or self.term.name == None:
			sublime.status_message('No term id or name specified.')
		else:
			self.window.show_input_panel('Rename Term', self.term.name, self.doDone, None, None)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		# Display a successful status message
		sublime.status_message('Successfully renamed ' + self.old_name + ' to ' + self.term.name + '.')

class WordpressNewTermCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows allows the user to create a new taxonomy term """
	def __init__(self, *args, **kwargs):
		super(WordpressNewTermCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called when the input panel has received input """
	def doDone(self, name):
		# initialize an empty WordPress term
		self.term = WordPressTerm()
		self.term.taxonomy = 'category'
		#new_term.parent = parent_cat.id
		self.term.name = name

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(NewTerm(self.term))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		self.window.show_input_panel('New Term Name', '', self.doDone, None, None)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		self.term.id = result

		# Display a successful status message
		sublime.status_message('Successfully created ' + self.term.name + ' with id of ' + self.term.id + '.')

class WordpressDeleteTermCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows allows the user to delete a new taxonomy term """
	def __init__(self, *args, **kwargs):
		super(WordpressDeleteTermCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(DeleteTerm(kwargs.get('taxonomy', None), kwargs.get('id')))

		# add the thread to the list
		self.wc.add_thread(thread)
		

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		sublime.status_message(' Successfully deleted term.')

class WordpressTermActionCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that displays a list of actions for a WordPress term """
	def __init__(self, *args, **kwargs):
		super(WordpressTermActionCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()
		
	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		self.taxonomy = kwargs.get('taxonomy', None)
		self.id = kwargs.get('id', None)
		self.name = kwargs.get('name', None)

		self.options = ['Rename Term', 'Delete Term']

		self.wc.show_quick_panel(self.options, self.panel_callback)

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# rename term
		if index == 0:
			self.window.run_command('wordpress_rename_term', { 'id': self.id, 'name': self.name, 'taxonomy': self.taxonomy })

		# delete term
		if index == 1:
			self.window.run_command('wordpress_delete_term', { 'id': self.id, 'name': self.name, 'taxonomy': self.taxonomy })

	""" Called when the thread is finished executing """  
	def thread_callback(self, result, *args, **kwargs):
		pass

class WordpressModifyPostTermsCommand(sublime_plugin.WindowCommand):
	""" Sublime Command called when the user selects the option to modify the terms and taxes of a post from the quick panel """
	def __init__(self, *args, **kwargs):
		super(WordpressModifyPostTermsCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# grab the passed in post id
		self.post_id = kwargs.get('id', None)
		self.selected_terms = []

		# create threaded API calls because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetPost(self.post_id))
		thread2 = sublpress.WordpressApiCall(GetTaxonomies())
		
		# save a copy of the current view when ran
		self.view = self.window.active_view()
		
		# add the thread to the list
		self.wc.add_thread(thread)
		self.wc.add_thread(thread2)

	""" Called when the thread has returned a list of taxonomies and we need the user to choose one """
	def choose_taxonomy(self, taxes):
		self.taxes = taxes
		self.taxonomy_options = ["Choose a Taxonomy", ]

		for tax in self.taxes:
			self.taxonomy_options.append(tax.name)

		self.wc.show_quick_panel(self.taxonomy_options, self.choose_taxonomy_callback)

	""" Called when the user has chosen a taxonomy """
	def choose_taxonomy_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# Do Nothing
		if index == 0:
			self.choose_taxonomy(self.taxes)
			return

		# loop through all of the retreived taxonomies
		for tax in self.taxes:
			# check for a matching title for the selected quick panel option
			if tax.name == self.taxonomy_options[index]:
				self.cur_tax = tax
				thread = sublpress.WordpressApiCall(GetTerms(tax.name))
				self.wc.add_thread(thread)
				self.wc.init_threads(self.thread_callback)

	""" Called when the thread has returned a list of terms and we need the user to choose one """
	def choose_term(self, terms):
		self.terms = terms
		self.term_options = [["Save Post", "with the terms marked below"], ]

		for term in self.terms:
			term_description = term.description
			if not term.description:
				term_description = "No Description"

			if term.id in self.selected_terms:
				self.term_options.append([self.wc.prefix.decode('utf8')  + term.name, "ID " + term.id + ": " + term_description])
			else:
				self.term_options.append([term.name, "ID " + term.id + ": " + term_description])

		self.wc.show_quick_panel(self.term_options, self.choose_term_callback)

	""" Called when the user has chosen a term """
	def choose_term_callback(self, index):
		# the user cancelled 0he panel
		if index == -1:
			return 

		# save the new terms
		if index == 0:
			self.update_post()
			return

		# loop through all of the retreived terms
		for term in self.terms:

			# split up the second line by the colon
			parts = self.term_options[index][1].partition(':')

			# check for a matching id for the selected quick panel option
			if term.id == parts[0][3:]:
				if term.id not in self.selected_terms:
					self.selected_terms.append(term.id)
				else:
					self.selected_terms.remove(term.id)
				self.choose_term(self.terms)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		if type(result) is WordPressPost:
			self.post = result
			
			for term in self.post.terms:
				self.selected_terms.append(term.id)
		elif type(result) is list:
			if type(result[0]) is WordPressTerm:
				self.choose_term(result)
			if type(result[0]) is WordPressTaxonomy:
				self.choose_taxonomy(result)
		elif type(result) is bool and result == True:
			sublime.status_message('Post updated with new terms and taxes')
				
	""" Called when the user wants to save the post with the new taxes and terms """
	def update_post(self):

		self.post.terms = [term for term in self.terms if term.id in self.selected_terms]
		#pprint.pprint(self.post.terms)

		thread = sublpress.WordpressApiCall(EditPost(self.post.id, self.post))
		self.wc.add_thread(thread)
		self.wc.init_threads(self.thread_callback)
