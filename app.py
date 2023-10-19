import os
import uuid
import csv
from flask_login import LoginManager, UserMixin, login_required, login_user\
    , current_user #logout_user
from flask import Flask, render_template, request, redirect, url_for

from werkzeug.utils import secure_filename


from model import nlpNER,modelReco


UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'mysecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    """_summary_

    Args:
        UserMixin (_type_): _description_
    """
    pass

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def read_products_from_csv():
    """_summary_

    Returns:
        _type_: _description_
    """
    products = []
    with open(file = 'products.csv', mode = 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            products.append(row)
    return products

def user_from_csv():
    """_summary_

    Returns:
        _type_: _description_
    """
    inf = []
    with open(file = 'client.csv', mode = 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            inf.append(row)
    return inf

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

##-------------------------------------------------------------------------------

@login_manager.user_loader
def user_loader(email):
    user = User()
    user.id = email
    return user

def write_client_to_csv(email, password):
    with open(file = 'client.csv', mode = 'a', newline='') as file:
        fieldnames = ['id', 'password']
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writerow({'id': email, 'password': password})

def read_clients_from_csv():
    clients = []
    with open(file = 'client.csv', mode = 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            clients.append(row)
    return clients

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        write_client_to_csv(email, password)
        return redirect(url_for('login'))
    return render_template('register.html')


def check_user_credentials(email, password):
    clients = read_clients_from_csv()
    for client in clients:
        if client['id'] == email and client['password'] == password:
            return True
    return False

@app.route('/', methods=['GET', 'POST'])
def login():
    products = read_products_from_csv()
    if request.method == 'POST':
        email = request.form.get('email', None)  # Utiliser get() retournera None si la clé n'existe pas
        password = request.form.get('password', None)

        if email and password:
            if check_user_credentials(email, password):
                user = User()
                user.id = email
                login_user(user)
                # return redirect(url_for('protected'))
                return redirect(url_for('index'))
            else:
                error = "Invalid credentials"
                return render_template('login.html', error=error)
        else:
            error =  "Missing email or password"
            return render_template('login.html', error=error)
    return render_template('login.html', products=products)

@app.route('/index')
@login_required
def index():
    products = read_products_from_csv()
    return render_template('index.html',products=products)


##-------------------------------------------------------------------------------
def write_product_to_csv(name, price, filename,comm, brand,key,state):
    with open('products.csv', 'a', newline='') as file:
        fieldnames = ['id', 'name', 'price','client','img', 'comm', 'brand','key','state']
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Générer un ID aléatoire avec uuid
        product_id = str(uuid.uuid4())
        csv_writer.writerow({'id': product_id, 'name': name, 'price': price, 'client':current_user.id, 'img':filename,'comm':comm, 'brand':brand,'key':key, 'state':state})

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        comm = request.form['comm']

        brand,key = nlpNER.extOrg(comm)

        file = request.files['product_image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print(filename)

        state = modelReco.state('static/uploads/' + filename)
        print(state)

        write_product_to_csv(name, price, filename,comm,brand,key,state)
        return redirect(url_for('index'))
    return render_template('add_product.html')


# @app.route('/product/<int:product_id>', methods=['GET'])
@app.route('/product/<string:product_id>', methods=['GET'])
def product_detail(product_id):
    products = read_products_from_csv()
    product = next((item for item in products if item['id'] == product_id), None)

    if product:
        return render_template('product_detail.html', product=product)
    else:
        return 'Produit non trouvé', 404

#----------------------------------------------------------

@app.route('/edit_product/<string:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    products = read_products_from_csv()
    product = next((item for item in products if item['id'] == product_id), None)

    if not product:
        return 'Product not found', 404

    # Check if the logged-in user is the owner of the product
    if product['client'] != current_user.id:
        return 'You are not the owner of this product', 403

    if request.method == 'POST':
        # Update product details based on form data
        name = request.form['name']
        price = request.form['price']
        
        # Update the product in the CSV file
        for item in products:
            if item['id'] == product_id:
                item['name'] = name
                item['price'] = price
                # You can also update other fields here if needed

        # Write the updated product list back to the CSV file
        with open('products.csv', 'w', newline='') as file:
            fieldnames = ['id', 'name', 'price', 'client', 'img']
            csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(products)

        return redirect(url_for('index'))

    return render_template('edit_product.html', product=product)

# Create a delete product route
@app.route('/delete_product/<string:product_id>', methods=['GET','POST'])
@login_required
def delete_product(product_id):
    products = read_products_from_csv()
    product = next((item for item in products if item['id'] == product_id), None)

    if not product:
        return 'Product not found', 404

    # Check if the logged-in user is the owner of the product
    if product['client'] != current_user.id:
        return 'You are not the owner of this product', 403

    products = [item for item in products if item['id'] != product_id]

    # Write the updated product list back to the CSV file
    with open('products.csv', 'w', newline='') as file:
        fieldnames = ['id', 'name', 'price', 'client', 'img']
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(products)

    return redirect(url_for('index'))

#----------------------------------------------------------
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    client_name = request.form.get('client')
    product_id = request.form.get('product_id')

    with open('cart.csv', 'a', newline='') as csvfile:
        fieldnames = ['client', 'id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'client': current_user.id, 'id': product_id})

    return redirect(url_for('index'))

@app.route('/mesinfos', methods=['GET','POST'])
def mesinfos():
    infs = read_clients_from_csv()
    for i in infs:
        if i['id'] == str(current_user.id):  # Assurez-vous que les types des deux id correspondent
            # return render_template('mesinfos.html', product=i)  # Retourne les informations si une correspondance est trouvée
            if request.method == 'POST':
                    # Update product details based on form data
                    name = request.form['name']
                    price = request.form['price']

                    # Update the product in the CSV file
                    for item in infs:
                        if item['id'] == current_user.id:
                            item['password'] = price
                            item['id'] = name

                    # Write the updated product list back to the CSV file
                    with open('client.csv', 'w', newline='') as file:
                        fieldnames = ['id', 'password']
                        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                        csv_writer.writeheader()
                        csv_writer.writerows(infs)

                    
                    products = read_products_from_csv()
        # Update the product in the CSV file
                    for item in products:
                        if item['client'] == current_user.id:
                            item['client'] = name
                
                
                        # Write the updated product list back to the CSV file
                    with open('products.csv', 'w', newline='') as file:
                        fieldnames = ['id', 'name', 'price', 'client', 'img']
                        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                        csv_writer.writeheader()
                        csv_writer.writerows(products)
                    
                    # current_user.id = name

                    return redirect(url_for('index'))
            # print(i)
            return render_template('mesinfos.html', product=i) 




@app.route('/show_cart')
def show_cart():
    products_dict = {}
    with open('products.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products_dict[row['id']] = row
    
    # Charger le panier et ajouter les détails du produit
    cart = []
    with open('cart.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['client'] == current_user.id:  # Filtre pour le current_user.id
                product_id = row['id']
                if product_id in products_dict:
                    cart.append(products_dict[product_id])
                    
    return render_template('show_cart.html', products=cart)

@app.route('/pay')
def pay():
    return render_template('pay.html')

if __name__ == '__main__':
    app.run(debug=True)
