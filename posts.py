import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess, webbrowser 
from wordpress_xmlrpc import *
from wordpress_xmlrpc.methods.posts import *
from wordpress_xmlrpc.methods.taxonomies import *
from wordpress_xmlrpc.methods.users import *  
import common, sublpress, command

class WordpressManagePostsCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows the user a list of WordPress posts (or any custom post type) """
	def __init__(self, *args, **kwargs):
		super(WordpressManagePostsCommand, self).__init__(*args, **kwargs)
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
		# initialize empty posts array
		self.posts = []  

		# grab post_type argument or substitute with a post type of post
		self.post_type = kwargs.get('post_type', 'post') 

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetPosts({ 'number': 200, 'post_type': self.post_type }))

		# add the thread to the list
		self.wc.add_thread(thread)

		# setup some options for the quick panel
		self.options = [['New ' + self.wc.unslugify(self.post_type), '']]

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# New Post (or Any Post Type)
		if index == 0:
			self.window.run_command('wordpress_new_post', {'post_type': self.post_type})
			return
		else:
			# loop through all of the retreived posts
			for post in self.posts:

				# check for a matching title for the selected quick panel option
				if post.title[:50] == self.options[index][0]:

					# show the user actions for this posts
					self.window.run_command('wordpress_post_action', {'id': post.id, 'title': post.title, 'post_type': self.post_type, 'is_wp': False})

	""" Called when a thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		# save the retreived posts
		self.posts = result

		# loop through all of the retreived posts
		for post in self.posts:

			# add the post title the quick panel options
			self.options.append([post.title[:50], post.content[:100]])

		# show the quick panel
		self.wc.show_quick_panel(self.options, self.panel_callback)

class WordpressDeletePostCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that deletes a WordPress post """
	def __init__(self, *args, **kwargs):
		super(WordpressDeletePostCommand, self).__init__(*args, **kwargs)
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
		# grab the active view
		self.view = self.window.active_view()

		# grab the id and title from the commands arguments, or the current view's status keys
		self.id = kwargs.get('id', self.view.get_status('Post ID'))
		self.title = kwargs.get('title', self.view.get_status('Post Title'))

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(DeletePost(self.id))

		# add the thread to the list
		self.wc.add_thread(thread)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		# close the post, if it's the current view
		if(self.view.get_status('Post ID') != ""):
			self.window.focus_view(self.view)
			self.window.run_command("close_file")

		# Display a successful status message
		sublime.status_message('Successfully deleted ' + self.title + '.')

class WordpressRenamePostCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that renames a WordPress post """
	def __init__(self, *args, **kwargs):
		super(WordpressRenamePostCommand, self).__init__(*args, **kwargs)
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
		# grab the active view
		self.view = self.window.active_view()

		# grab the id and title from the commands arguments, or the current view's status keys
		self.id = kwargs.get('id', self.view.get_status('Post ID'))
		self.title = kwargs.get('title', self.view.get_status('Post Title'))

		# show the input panel to input the name
		self.window.show_input_panel('Rename Post', self.title, self.doDone, None, None)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):

		self.view.set_status('Post Title', self.post.title)
		self.view.set_name(self.post.title)

		# Display a successful status message
		sublime.status_message('Successfully renamed ' + self.title + ' to ' + self.post.title + '.')

	""" Called when the input panel has received input """
	def doDone(self, name):
		# initialize an empty WordPress post
		self.post = WordPressPost()

		# assign the new name to this post
		self.post.title = name

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(EditPost(self.id, self.post))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)

class WordpressPostActionCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that displays a list of actions for a WordPress post """
	def __init__(self, *args, **kwargs):
		super(WordpressPostActionCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		is_wp = kwargs.get('is_wp', True)

		if is_wp and self.window.active_view().get_status('Post ID') == "":
			sublime.status_message('The current view is not a WordPress Post.')
			return

		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		#self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# grab the active view
		view = self.window.active_view()

		# grab the id, title, and type from the commands arguments, or the current view's status keys
		self.id = kwargs.get('id', view.get_status('Post ID'))
		self.title = kwargs.get('title', view.get_status('Post Title'))
		self.post_type = kwargs.get('post_type', view.get_status('Post Type'))

		# create a pretty string for the post type
		pretty = self.wc.unslugify(self.post_type)

		# setup some options for the quick panel
		self.options = ['Rename ' + pretty, 'Edit ' + pretty, 'Delete ' + pretty, 'Change ' + pretty + ' Status', 'Modify Terms and Taxes for ' + pretty, 'Change Parent ' + pretty, 'View ' + pretty, ]

		# show the quick panel
		self.wc.show_quick_panel(self.options, self.panel_callback)

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# rename post
		if index == 0:
			self.window.run_command('wordpress_rename_post', {'id': self.id, 'title': self.title}) # rename
			return

		# edit post
		if index == 1:
			self.window.run_command('wordpress_edit_post', {'id': self.id}) # edit
			return

		# delete post
		if index == 2:
			self.window.run_command('wordpress_delete_post', {'id': self.id, 'title': self.title}) # delete
			return

		# change post status
		if index == 3:  
			self.window.run_command('wordpress_modify_post_status', {'id': self.id}) # edit
			return

		# modify terms 
		if index == 4:
			self.window.run_command('wordpress_modify_post_terms', {'id': self.id}) # edit
			return

		# change parent
		if index == 5:
			self.window.run_command('wordpress_modify_post_parent', {'id': self.id, 'title': self.title, 'post_type': self.post_type}) #view
			return

		# view post
		if index == 6:
			self.window.run_command('wordpress_view_post', {'id': self.id, 'title': self.title}) #view
			return

class WordpressSavePostCommand(sublime_plugin.WindowCommand):       
	""" Sublime Command called when the user attempts to save a document """
	def __init__(self, *args, **kwargs):
		super(WordpressSavePostCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return True

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# grab the active view
		self.view = sublime.active_window().active_view()
		self.post_id = self.view.get_status('Post ID')

		# check if this view is a WordPress post
		if self.post_id:
			# create threaded API call because the http connections could take awhile
			thread = sublpress.WordpressApiCall(GetPost(self.post_id))

			# add the thread to the list
			self.wc.add_thread(thread)

			# initiate any threads we have
			self.wc.init_threads(self.thread_callback)

			return

		# run sublime's original save command
		self.view.run_command("save")

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		if type(result) is not WordPressPost and type(result) is bool and result == False:
			sublime.status_message('Unable to save ' + self.post.title + '.')
			return
		elif type(result) is bool and result == True:
			sublime.status_message('Successfully saved ' + self.post.title + '.')
			return

		self.post = result

		# retreive the new content from the  view the command was ran on
		self.post.content = self.view.substr(sublime.Region(0, self.view.size()))

		# adjust thumbnail to contain the attachment id
		if isinstance(self.post.thumbnail, dict):
			self.post.thumbnail = self.post.thumbnail['attachment_id']

		if self.post_id and self.post:
			# create threaded API call because the http connections could take awhile
			thread = sublpress.WordpressApiCall(EditPost(self.post.id, self.post))

			# add the thread to the list
			self.wc.add_thread(thread)

			# initiate any threads we have
			self.wc.init_threads(self.thread_callback)

		

class WordpressEditPostCommand(sublime_plugin.WindowCommand):
	""" Sublime Command called when the user selects an edit command from the quick panel """
	def __init__(self, *args, **kwargs):
		super(WordpressEditPostCommand, self).__init__(*args, **kwargs)
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
		thread = sublpress.WordpressApiCall(GetPost(kwargs.get('id')))
		self.view = self.window.active_view()
		
		# add the thread to the list
		self.wc.add_thread(thread)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		self.post = result

		# initialize sublime's status keys for this view
		status = { "Post ID": self.post.id, "Post Title": self.post.title, "Post Status": self.post.post_status, "Post Type": self.post.post_type }

		# send along some of the same data to be used for populating the view
		data = { "title": self.post.title, "content": self.post.content, "status": status }

		# run the insert command, lame workaround because we need a new textcommand for it's edit object
		sublime.set_timeout(lambda: self.view.run_command("wordpress_insert", data), 200)

		# display a status message
		sublime.status_message('Started editing ' + self.post.title + ' successfully.')

class WordpressNewPostCommand(sublime_plugin.WindowCommand):
	""" Sublime Command called when the user selects the create new post option in the quick panel """
	def __init__(self, *args, **kwargs):
		super(WordpressNewPostCommand, self).__init__(*args, **kwargs)
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
		# retreive post type
		self.post_type = kwargs.get('post_type', 'post')

		# show the input panel to receive the new posts title
		self.window.show_input_panel('New ' + self.post_type + ' Title', '', self.doDone, None, None)

	""" Called when the input panel has received input """
	def doDone(self, name):
		# initialize an empty wordpress post
		self.post = WordPressPost()

		# intialize the post with the inputted name and some empty content
		self.post.title = name
		self.post.content = ''
		self.post.post_type = self.post_type

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(NewPost(self.post))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called when the thread is finished executing """
	def thread_callback(self, result):
		self.post.id = result

		sublime.status_message('Successfully created ' + self.post.title)

		self.window.run_command('wordpress_edit_post', { 'id': self.post.id })

class WordpressViewPostCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that renames a WordPress post """
	def __init__(self, *args, **kwargs):
		super(WordpressViewPostCommand, self).__init__(*args, **kwargs)
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
		# grab the active view
		self.view = self.window.active_view()

		# grab the id and title from the commands arguments, or the current view's status keys
		self.id = kwargs.get('id', self.view.get_status('Post ID'))
		self.title = kwargs.get('title', self.view.get_status('Post Title'))

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetPost(self.id))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		webbrowser.open(result.link)

		

class WordpressModifyPostStatusCommand(sublime_plugin.WindowCommand):
	""" Sublime Command called when the user selects the option to modify the post status of a post """
	def __init__(self, *args, **kwargs):
		super(WordpressModifyPostStatusCommand, self).__init__(*args, **kwargs)
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

		# create threaded API calls because the http connections could take awhile
		thread = sublpress.WordpressApiCall(GetPost(self.post_id))
		thread2 = sublpress.WordpressApiCall(GetPostStatusList())
		
		# save a copy of the current view when ran
		self.view = self.window.active_view()
		
		# add the thread to the list
		self.wc.add_thread(thread)
		self.wc.add_thread(thread2)

	""" Called when the thread has returned a list of statuses and we need the user to choose one """
	def choose_status(self, statuses):
		self.statuses = statuses
		self.status_options = ["Choose a Status", ]

		pprint.pprint(self.statuses)

		for k, v in self.statuses.items():
			self.status_options.append(v)

		self.wc.show_quick_panel(self.status_options, self.choose_status_callback)

	""" Called when the user has chosen a status """
	def choose_status_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# Do Nothing
		if index == 0:
			self.choose_status(self.statuses)
			return

		# loop through all of the retreived taxonomies
		for k, v in self.statuses.items():
			# check for a matching title for the selected quick panel option
			if v == self.status_options[index]:
				self.cur_status = k
				self.update_post()

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		if type(result) is WordPressPost:
			self.post = result
		elif type(result) is dict:
			self.statuses = result
			self.choose_status(self.statuses)
		elif type(result) is bool and result == True:
			self.view.set_status('Post Status', self.cur_status)
			sublime.status_message('Post updated to have a status of "' + self.cur_status + '".')

	""" Called when the user wants to save the post with the status """
	def update_post(self):

		self.post.post_status = self.cur_status

		thread = sublpress.WordpressApiCall(EditPost(self.post.id, self.post))
		self.wc.add_thread(thread)
		self.wc.init_threads(self.thread_callback)


class WordpressModifyPostParentCommand(sublime_plugin.WindowCommand):
	""" Sublime Command called when the user selects the option to modify the parent of a page """
	def __init__(self, *args, **kwargs):
		super(WordpressModifyPostParentCommand, self).__init__(*args, **kwargs)
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
		self.page_id = kwargs.get('id', None)
		self.post_type = kwargs.get('post_type', None)

		if self.post_type != "page":
			sublime.status_message('This post isn\'t a page, trying anyway...')
			#return 

		# create threaded API calls because the http connections could take awhile
		#thread = sublpress.WordpressApiCall(GetPost(self.page_id))
		thread = sublpress.WordpressApiCall(GetPosts({ 'number': 200, 'post_type': self.post_type }))

		# save a copy of the current view when ran
		self.view = self.window.active_view()
		
		# add the thread to the list
		self.wc.add_thread(thread)
		#self.wc.add_thread(thread2)

	""" Called when the thread has returned a list of statuses and we need the user to choose one """
	def choose_page(self, pages):
		self.pages = pages
		self.page_options = ["Choose a Parent", ]

		for page in self.pages:
			if self.page_id == page.id:
				self.page = page

			self.page_options.append(page.title)

		self.wc.show_quick_panel(self.page_options, self.choose_page_callback)

	""" Called when the user has chosen a page """
	def choose_page_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		# Do Nothing
		if index == 0:
			self.choose_page(self.pages)
			return

		# loop through all of the retreived taxonomies
		for page in self.pages:
			# check for a matching title for the selected quick panel option
			if page.title == self.page_options[index]:
				self.new_page_id = page.id
				self.update_page()

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		if type(result) is list:
			self.pages = result
			self.choose_page(self.pages)
		elif type(result) is bool and result == True:
			sublime.status_message('Post updated to have a parent id of "' + self.new_page_id + '".')

	""" Called when the user wants to save the page with the new parent """
	def update_page(self):

		self.page.parent_id = self.new_page_id

		thread = sublpress.WordpressApiCall(EditPost(self.page.id, self.page))
		self.wc.add_thread(thread)
		self.wc.init_threads(self.thread_callback)