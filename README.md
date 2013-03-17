sublpress
=========

### Check it out on [dnstbr.me](http://dnstbr.me)

### Description

Sublepress is a Sublime Text 2 / 3 plugin to manage WordPress 3.5 installations from within Sublime Text. The mostly quick panel based system allows for managing settings, posts(and custom post types), pages and taxonomy terms of a WordPress blog.

### Feature List
- Create, Edit, Delete, Rename Posts
- Create, Edit, Delete, Rename Pages
- Create, Edit, Delete, Rename Posts of a Custom Post Type
- Create, Delete, Rename Terms in a Taxonomy
- Upload Media (with Assign as Featured Image action)
- Edit Terms and Taxonomies associated with a Post
- Change WordPress settings

### Installation
The most straightforward installation method is via [Will Bond's](http://wbond.net/) [Package Control](http://wbond.net/sublime_packages/package_control/package_developers). If you prefer, you can also clone (or copy the contents of) this repository into your Sublime Text `./Packages` folder:

    git clone https://github.com/dnstbr/sublpress.git

### Configuration
To start, you'll need to setup a WordPress site config to connect to. A settings file has been created for you in your 
<sublime package dir>/User/ folder. To edit it open the command palette and look for "WP: Manage Sites". A snippet has
been provided to make it easy to add new configurations, you can complete it by typing "site" without the quotes 
and pressing tab. You can continue pressing tab to cycle through the various options.

After adding a site connect to by finding "WP: Connect to Site" in the command palette.