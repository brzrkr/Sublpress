sublpress
=========

### You can also leave feedback at [dnstbr.me/labs/sublpress](http://dnstbr.me/index.php/labs/sublpress)

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

### Screenshots
<div style="width:50%;float:left;">
	<h3>Choosing a WordPress Host ("WP: Connect to Site")</h3>
	<img src="http://cl.zombierelief.com/image/180V1X3M1P3f/Image%202013.03.17%2011:29:42%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>After Selecting a Host </h3>
	<img src="http://cl.zombierelief.com/image/1f0g0D0E0W0p/Image%202013.03.17%2011:30:00%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>Edit Settings ("WP: Edit Settings")</h3>
	<img src="http://cl.zombierelief.com/image/0X3g3E1K220e/Image%202013.03.17%2011:30:11%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>Manage All Pages ("WP: Manage all Pages")</h3>
	<img src="http://cl.zombierelief.com/image/3g3C2E2A2y2M/Image%202013.03.17%2011:30:28%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>Page or Post Actions ("WP: Post Actions")</h3>
	<img src="http://cl.zombierelief.com/image/112k1f0X1w26/Image%202013.03.17%2011:30:42%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>Term Management for Page or Post ("WP: Post Actions")</h3>
	<img src="http://f.cl.ly/items/0y1x2G171z1J093C2p0c/Image%202013.03.17%2011:31:00%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>List of Actions ("WP:")</h3>
	<img src="http://f.cl.ly/items/3w0H1e2d2b1V0C313z13/Image%202013.03.17%2011:27:15%20AM.png" />
</div>
<div style="width:50%;float:left;">
	<h3>Example Site Config ("WP: Manage Site")</h3>
	<img src="http://cl.zombierelief.com/image/1R293w2q2P37/Image%202013.03.17%2011:28:42%20AM.png" />
</div>

### Installation (waiting on approval for Package Control)
Clone (or copy the contents of) this repository into your Sublime Text `./Packages` folder:

    git clone https://github.com/dnstbr/sublpress.git

### Configuration
To start, you'll need to setup a WordPress site config to connect to. A settings file has been created for you in your 
<sublime package dir>/User/ folder. To edit it open the command palette and look for "WP: Manage Sites". A snippet has
been provided to make it easy to add new configurations, you can complete it by typing "site" without the quotes 
and pressing tab. You can continue pressing tab to cycle through the various options.

After adding a site connect to by finding "WP: Connect to Site" in the command palette.