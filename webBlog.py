import webapp2
import jinja2
import os
import re

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class BlogHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		return render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class Welcome(BlogHandler):
	def get(self):
		self.render('welcome.html')


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):
	def get(self):
		self.render('signup.html')

	def post(self):
		have_error = False
		user_name = self.request.get('username')
		user_password = self.request.get('password')
		verify_password = self.request.get('verify')
		user_email = self.request.get('email')

		params = dict(username = user_name, email = user_email)

		if not valid_username(user_name):
			params['error_username'] = "That's not a valid username."
			have_error = True

		if not valid_password(user_password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif user_password != verify_password:
			params['error_verify'] = "Your passwords didn't match."
			have_error = True

		if not valid_email(user_email):
			params['error_email'] = "That's not a valid email."
			have_error = True

		if have_error:
			self.render('signup.html', **params)
		else:
			self.redirect('/blog/newpost')

### Blog methods

def blog_key(name = 'default'):
	return db.Key.from_path('blogs', name)

class Post(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

	def render(self):
		self._render_text = self.content.replace('\n', '<br>')
		return render_str("post.html", p = self)

class BlogFront(BlogHandler):
	def get(self):
		posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
		self.render("front.html", posts = posts)

class PostPage(BlogHandler):
	def get(self, post_id):
		key = db.Key.from_path('Post', int(post_id), parent = blog_key())
		post = db.get(key)

		if not post:
			self.error(404)
			return

		self.render("permalink.html", post = post)

class NewPost(BlogHandler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		subject = self.request.get('subject')
		content = self.request.get('content')

		if subject and content:
			p = Post(parent = blog_key(), subject = subject, content = content)
			p.put()
			self.redirect('/blog/%s' % str(p.key().id()))
		else:
			error = "Subject and content, please!"
			self.render("newpost.html", subject = subject, content = content, error = error)


app = webapp2.WSGIApplication([('/', Welcome),
								('/signup', Signup),
								('/blog/?', BlogFront),
								('/blog/([0-9]+)', PostPage),
								('/blog/newpost', NewPost)
								], debug=True)
