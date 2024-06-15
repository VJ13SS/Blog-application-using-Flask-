###importing the necessary libraries
from flask import Flask,render_template, redirect, url_for,request,session,flash
from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import timedelta

#app initialization and defining the secret key
app= Flask(__name__)
app.secret_key = ('J06x1r@13')

#configurations for sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) #db is then used to define models and to perform sql alchemy operations

#defining database model / Table

#User Table
class User(db.Model):
	id = db.Column(db.Integer,primary_key = True)
	name = db.Column(db.String(100),nullable = False)
	email = db.Column(db.String(100),nullable = False)
	password = db.Column(db.String(100),nullable = False)
	info = db.Column(db.Text,nullable = False)
	
	#creating a relationship with the post table
	#from the posts to acces / to backreference the user we do use the backref
	#passive_deletes is similar to ondelete cascade
	posts = db.relationship('Post', backref = 'user',passive_deletes = True)
	
	comments = db.relationship('Comments', backref = 'user',passive_deletes = True)
	
	liked_by = db.relationship('Likes',backref = 'user',passive_deletes = True)
	
	#user followers
	followers = db.relationship('Follows',backref = 'user',passive_deletes = True)#following the user
		
	
#Posts Table
class Post(db.Model):
	id = db.Column(db.Integer,primary_key = True)
	text = db.Column(db.Text,nullable = False)
	
	created_at = db.Column(db.String(25),nullable = False)
	
	author = db.Column(db.Integer,db.ForeignKey('user.id',ondelete = 'CASCADE'),nullable = False)#defined a foreign key to relate both the tables via the user.id
	#using ondelete = Cascade ..when the uer gets deleted,all the posts of the user gets deleted too
	post_comments = db.relationship('Comments', backref = 'post',passive_deletes = True)
	
	post_likes = db.relationship('Likes',backref = 'post',passive_deletes = True)
	
	
#comments Table
class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    text = db.Column(db.Text, nullable=False)
    
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)


#likes table
class Likes(db.Model):
	
	id = db.Column(db.Integer,primary_key = True)
	author = db.Column(db.Integer,db.ForeignKey('user.id',ondelete = 'CASCADE'),nullable = False)
	
	liked_post = db.Column(db.Integer,db.ForeignKey('post.id',ondelete = 'CASCADE'),nullable = False)
	
#Follows Table
class Follows(db.Model):
	id = db.Column(db.Integer,primary_key = True)
	
	#who is following
	follower = db.Column(db.Integer,db.ForeignKey('user.id',ondelete = 'CASCADE'),nullable = False)
	
	#whom is being followed(post owner)
	following = db.Column(db.String(25),nullable = False)
	
#permanent session
app.permanent_session_lifetime = timedelta(minutes = 5)


#User authentication


#Login page
@app.route('/', methods = ['POST','GET'])
def login():
	
	if 'user' in session:
		return redirect(url_for('home'))
		
	if request.method == 'POST':
		
		session.permanent = True
		
		user = request.form['name'].strip()
		lock = request.form['password']
		
		if not(user) or not(lock):
			flash('User not exists....!')
			return redirect(url_for('login'))			
			
		#checking if user exists in database		
		existing_user = User.query.filter_by(name = user).first()		
		
		#to check if the entered login details do matches or not
		if existing_user:#if user already exists
			user_password = User.query.filter_by(password = lock).first()
			
			if user_password:
				session['user'] = user
				session['password'] = lock
				return redirect(url_for('home'))
			else:
				flash('Invalid Credidentials')
				
		else:
			flash('User not exists...!')
			
	return render_template('Login_FP.html')

		
#sign in page
@app.route('/signin',methods = ['POST','GET'])
def signin():
	if request.method == 'POST':		
		
		#Fetching the entered data
		name = request.form['name']
		password = request.form['password']
		email = request.form['email']
				
		#checking if user exists
		existing_email = User.query.filter_by(email = email).first()
		
		if existing_email:
			flash('Account Already exists...!')
			return redirect(url_for('signin'))
				
		#Create new object
		if name!= '' and password!='':
		      new_user = User(name = name,password = password, email = email,info = 'User')
		      
		      #adding to database		
		      db.session.add(new_user)	
		      db.session.commit()
		      
		      flash('Account Created Successfully')
		      return redirect(url_for('login'))
				      
	return render_template('Sign_in_FP.html')


#logout
@app.route('/logout')
def logout():
	if 'user' in session:
		session.pop('user')
		session.pop('password')
	
	flash('Logged out Successfully')
	return redirect(url_for('login'))


#main page


#home page
@app.route('/home')
def home():
	if 'user' in session :
		user_name = session['user']
		
		#to get the user from the database
		user = User.query.filter_by(name = user_name).first()
		
		#to access all the posts of the obtained user
		posts = Post.query.filter_by(author = user.id).all()
		
		user_followers = user.followers
		length_F = len(user_followers)
			
		return render_template('Home_FP.html',current_user = user,display_posts = posts[: : -1],total_followers = length_F)

#edit profile
@app.route('/editprofile/<id>',methods =['GET','POST'])
def editprofile(id):
	user = User.query.filter_by(id = id).first()
	
	if user:
		if request.method == 'POST':
			edited_name = request.form['name'].strip()
			edited_info = request.form['info'].strip()
			
			if edited_name:
				user.name = edited_name
				
			if edited_info:
				user.info = edited_info	
						
			#adding new user name to session
			session['user'] = user.name
			
			db.session.commit()
			return redirect(url_for('home'))
			
		return render_template('Editprofile_FP.html')
		
	else:
		return redirect(url_for('home'))

#create a post
@app.route('/createpost', methods = ['GET', 'POST'])
def create_post():
	if request.method == 'POST':
		
		post = request.form['post']
		user = session['user']
		
		created_by = User.query.filter_by(name = user).first()
		
		date = datetime.date.today()
		
		#If post not empty
		if post:
			flash('Blog Created Successfully')
			
			new_post = Post(text = post,author = created_by.id,created_at = date)
			
			db.session.add(new_post)
			db.session.commit()
	return render_template('CreatePosts_FP.html',default = '')
	

#viewing user posts
@app.route('/viewposts',methods =['GET','POST'])
def viewposts():
	
	#taking all post,commemts
	posts = Post.query.all()
	
	#posts[ : :-1] --> to view the latest posts first
	return render_template('Viewposts_FP.html',user_posts = posts[::-1],search = 0)#search is 0 means to display the user's post's'
	

#search user posts
@app.route('/search-user',methods = ['GET','POST'])
def search_user():
	if request.method == 'POST':
		searched_user = request.form['find_user'].strip()
		
		if not searched_user:
			flash('User dosent exists...!')
		
		else:
			#to get the searched user
			user = User.query.filter_by(name = searched_user).first()
			
			if user:
				return render_template('Viewposts_FP.html',todisplay = user,search = 1)#search is 1means to display the user profile
				
			else:
				flash('User dosent exists...!')
		
		return redirect(url_for('viewposts'))


#liking the posts
@app.route('/likepost/<id>')
def likepost(id):
	user = session['user']
	
	#obtaining the user
	liked_by = User.query.filter_by(name = user).first()
	#obtaining the current post
	post = Post.query.filter_by(id = id).first()
	#recieving the like object
	like = Likes.query.filter_by(author =liked_by.id,liked_post = id).first()
	
	#if user has already liked the post
	if like:
		db.session.delete(like)
		db.session.commit()
		
	else:
		new_like = Likes(liked_post = post.id,author = liked_by.id)
		db.session.add(new_like)
		db.session.commit()
		
	return redirect('/postdetails/' + id )
	
	
#following user
@app.route('/follow-user/<id>')
def connect(id):
	
	#the person who tends to follow
	user = session['user']
	visited_user = User.query.filter_by(name = user).first()
	
	profile_owner = User.query.filter_by(id = id).first()
	
	
	if not(visited_user):
		flash('User dosent Exists')
		return redirect(url_for('viewposts'))
		
	#checks if the visited user follows/is connected with the account holder
	isFollowing = Follows.query.filter_by(follower = id,following = visited_user.name).first()
	
	#if follows/connected already
	if isFollowing:
		
		db.session.delete(isFollowing)
	
	else:
		newFollow = Follows(follower = id,following = user)
		db.session.add(newFollow)
		
	db.session.commit()
	
	return redirect('/user/' + id)
	

#edit a post
@app.route('/editpost/<id>',methods = ['GET', 'POST'])
def editpost(id):
	post = Post.query.filter_by(id = id).first()
	
	if request.method == 'POST':
		edited_post = request.form['post']
		
		#updating the edited post
		post.text = edited_post
		db.session.commit()
		
		return redirect('/postdetails/' + id)
	
	return render_template('CreatePosts_FP.html',default = post.text)


#view a user
@app.route('/user/<id>')
def viewuser(id):
	
	user = User.query.filter_by(id = id).first()
	
	#the one who inspects or visits the profile
	visited = session['user']
	visited_user = User.query.filter_by(name = visited).first()
	
	if not visited_user:
		flash('User not Online')
		return redirect('/')
	
	#checks if the visited user follows the account holder
	isFollowing = Follows.query.filter_by(follower = id,following = visited_user.name).first()
	
	if isFollowing:
		following = 1#user already follows the account holder
	else:
		following = 0
	
	#to get all the posts of the user
	user_posts = user.posts#we do have a post column in user table which is a foreign key realting the post table
	length_P = len(user_posts)
	
	user_followers = user.followers
	length_F = len(user_followers)
	
	return render_template('UserPosts_FP.html',profile_viewed = visited_user.name,view_user = user,view_user_posts = user_posts[: : -1],total_posts = length_P,total_followers = length_F,Follow =following)

#delete a post
@app.route('/deletepost/<id>')#<id> is the dynamic variable passed (check Home_FP.html to know how it is passed)
def deletepost(id):
	#getting the post using the post id
	post = Post.query.filter_by(id = id).first()
	
	if post:
		db.session.delete(post)
		db.session.commit()
	
	return redirect(url_for('home'))


#view a post,likes,add comments
@app.route('/postdetails/<id>',methods = ['POST','GET'])
def viewpost(id):
	current_post = Post.query.filter_by(id = id).first()
	user = session['user']
	
	if request.method == 'POST':
		comment = request.form['comment']
		
		#User who visits the post
		commented_by = User.query.filter_by(name = user).first()
		
		if comment:
			new_comment = Comments(text = comment,author = commented_by.id,post_id = id)
			#adding mew comment
			db.session.add(new_comment)
			db.session.commit()
			
		else:
			flash('Comment cannot be empty...!')
	
	#getting the total numner of comments
	post_comments = Comments.query.filter_by(post_id = id).all()
	length_c =len(post_comments)
	
	#getting the total number of likes
	post_likes = Likes.query.filter_by(liked_post = id).all()
	length_l = len(post_likes)
	
	
	#checking if user liked the post or not
	liked_by = User.query.filter_by(name = user).first()
	
	if(Likes.query.filter_by(author = liked_by.id,liked_post = current_post.id).first()):
		liked_by_user = 1#User had liked the post
	else:
		liked_by_user = 0#Iser has not liked the post
	
	return render_template('Post_FP.html',post = current_post,comments = post_comments,current_user = user,total_comments = length_c,total_likes = length_l,likes = post_likes,user_liked = liked_by_user)


#delete comment
@app.route('/deletecomment/<comment_id>/<post_id>')
def deletecomment(comment_id,post_id):
	
	comment = Comments.query.filter_by(id = comment_id).first()
	
	db.session.delete(comment)
	db.session.commit()
	
	return redirect('/postdetails/' + post_id)


if __name__ == '__main__':
	with app.app_context():
		#db.drop_all()#to drop the database
		db.create_all()#to create the database
	app.run(debug = True)
