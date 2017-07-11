from flask import Flask, render_template, request, redirect, url_for, flash, jsonify


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


engine = create_engine('sqlite:///itemscatalog.db')
# bind the engine to the metadata of the Base class
# so that the declaratives can be accessed through a 
# DBSession instance

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#HTML escape tags are like this: & becomes &amp, < becomees &lt, etc

# # JSON API ENDPOINT FOR ITEMS
# @app.route(''/category/<int:category_id>/item/<int:item_id>/JSON')
# def itemJSON(category_id, item_id):
#     category = session.query(Category).filter_by(id=category_id).one()
#     items = session.query(Item).filter_by(category_id=category_id).all()
#     return jsonify(Items=[i.serialize for i in items])

# JSON API ENDPOINT FOR CATEGORIES
@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    categories = session.query(Category).filter_by(id=category_id).all()
    return jsonify(Categories=[c.serialize for c in categories])


# Show all categories
@app.route('/')
@app.route('/category/')
def showAllCategories():
    allCategories = session.query(Category)
    if 'username' in login_session:
        print login_session['username']
        return render_template('categories.html', categories=allCategories)
    else:
        return render_template('public_categories.html', categories=allCategories)
    # TODO: Render all Categories, not single category

    # cat = session.query(Category)
    # firstCategory = cat.first()
    
    # allItems = session.query(Item)
    # itemCatId = allItems.filter_by(category_id=firstCategory.id)

    # return render_template(
    #   'categories.html',
    #   blah={ 'name': 'blah', 'id': 1 },
    #   category=firstCategory,
    #   items=itemCatId
    # ) # variable on LEFT is in the template, variable RIGHT is in the function


# Add new category
@app.route('/category/new/', methods=['GET','POST'])
# missing category_id dummy variable?? when you add new item dont need it, but in view you do?
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        print 'create new catalog'
        newCategory = Category(name=request.form['categoryName'])
        session.add(newCategory)
        session.commit()
        flash("category has been added!")
        return redirect(url_for('showAllCategories'))
    return render_template('newCategory.html')


# Edit category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id): #/category/1/edit
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['category_name']:
            editedCategory.name = request.form['category_name']
        session.add(editedCategory)
        session.commit()
        flash("category has been edited!")
        return redirect(url_for('showAllCategories', category_id=category_id))
    else: #GET
        return render_template('editCategory.html', editedCategory=editedCategory)


# Delete category
@app.route('/category/<int:category_id>/delete/', methods = ['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash("category has been deleted!")
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('deleteCategory.html', category_id=categoryToDelete)


# Individual category page /category/123
@app.route('/category/<int:category_id>/')
def categoryPage(category_id):
    allItems = session.query(Item)
    category = session.query(Category).filter_by(id=category_id).one()
    filteredItems = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('item.html', items = filteredItems, cat = category, allItems = allItems)

# Add new item
@app.route('/category/<int:category_id>/new/', methods=['GET', 'POST'])
def addItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['itemName'], description=request.form['descriptionItem'],
            category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("New item %s has been added!" % (newItem.name))
        return redirect(url_for('categoryPage', category_id=category_id))
    else:
        return render_template('newItem.html', category_id=category_id)


#Edit item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        flash("item has been edited!")
        return redirect(url_for('categoryPage',category_id=category_id))
    else:
        return render_template('editItem.html', category_id=category_id, item_id=item_id, item=editedItem)


# Delete item
@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("item has been deleted!")
        return redirect(url_for('categoryPage', category_id=category_id))
    else:
        return render_template('deleteItem.html', category_id=category_id, item_id=item_id, deletedItem = itemToDelete)


# Create a state token to prevent request forgery
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    login_session['state'] = state
    print "hello"
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        # credentials = oauth_flow.step2_exchange(code)
        credentials = oauth_flow.step2_exchange(code)
        credentials = credentials.to_json()
        credentials = json.loads(credentials)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials['access_token']
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials['id_token']['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials['access_token'], 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNET - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # access_token = login_session['access_token']
    # if not access_token:
    access_token = login_session['credentials']['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # access_token = credentials.get(access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token#login_session['credentials']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['credentials'] 
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['access_token']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for("showAllCategories"))
    else:
        print "Disconnect did not work"
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# confused about __name__ == '__main__' when other modules imported
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)