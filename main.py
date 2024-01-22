from flask import Flask, current_app, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_bootstrap import Bootstrap5
from forms import AddForm, EditForm, Restocked, Sold
import json
from sqlalchemy.orm.attributes import flag_modified

# Define stockmanager that will have methods for daily operations
class StockManager:
    def transact(self, item_id, sold_quantity, added_quantity):
        item = Stock.query.get_or_404(item_id)
        action = {
            'purchase': {'quantity':int(added_quantity), 'price':item.buying_price}, 
            'sold': {'quantity':int(sold_quantity), 'price_sold':item.selling_price, 'b_price': item.buying_price}
            }
        action_json = json.dumps(action)
        transaction = Transactions(item_id=item_id, actions=action_json)
        db.session.add(transaction)
        db.session.commit()

    def add_item(self, name, b_price, s_price, quantity=0) -> None:
        with current_app.app_context():
            existing_item = Stock.query.filter_by(item_name=name).first()
            if existing_item:
                return False
            else:
                item = Stock(item_name=name.lower(), buying_price=b_price, selling_price=s_price, item_quantity=quantity)
                db.session.add(item)
                db.session.commit()
                self.transact(Stock.query.filter_by(item_name=name).first().id, 0, quantity)
                return True
    
    def remove_item(self, name):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                db.session.delete(item)
                db.session.commit()
                return True
            else:
                return False

    def add_item_quantity(self, name, quantity):
        with current_app.app_context():
            print(name, quantity)
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                self.transact(item.id, 0, quantity)
                item.item_quantity += quantity
                db.session.commit()
                return True
            else:
                return False


    def update_item_s_price(self, name, new_price):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.selling_price = new_price
                db.session.commit()
                # print(f"Changed item price to {new_price}")
                return True
            else:
                # print("Item not found")
                return False

    def update_item_b_price(self, name, new_price):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.buying_price = new_price
                db.session.commit()
                # print(f"Changed item price to {new_price}")
                return True
            else:
                # print("Item not found")
                return False

    def sell_item(self, name, quantity_sold):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                print(f"Subtracted {quantity_sold} from {item.item_quantity}")
                if item.item_quantity >= quantity_sold:
                    item.item_quantity -= quantity_sold
                    self.transact(item.id, quantity_sold, 0)
                    return True
                else:
                    # print(f"Not enough quantity to subtract {quantity_sold} from {item.item_quantity}")
                    return False
            else:
                # print("Couldn't find item")
                return 1
        
    # def display_stock(self):
    #     with current_app.app_context():
    #         items = Stock.query.all()
    #         for item in items:
    #             print(f"ID: {item.id}, ITEM: {item.item_name}, Quantity: {item.item_quantity}, Buying Price: {item.buying_price}, Selling Price: {item.selling_price}")

    def number_of_selled_items(self, start_date=None, end_date=None):
        if start_date is not None and end_date is not None:
            transactions = Transactions.query.filter(db.and_(Transactions.timestamp >= start_date, Transactions.timestamp <= end_date)).order_by(Transactions.item_id).all()
        else:
            transactions = db.session.execute(db.select(Transactions).order_by(Transactions.item_id)).scalars()
        quantity_sold = []
        count = 0
        current_transaction = None
        for transaction in transactions:
            actions_dumps = json.loads(transaction.actions)
            if current_transaction is None:
                current_transaction = transaction.item_id
            if current_transaction == transaction.item_id:
                count += actions_dumps['sold']['quantity']
            else:
                item = Stock.query.get_or_404(current_transaction)
                quantity_sold.append([item.item_name, count, actions_dumps['sold']['b_price'], actions_dumps['sold']['price_sold']])
                current_transaction = transaction.item_id
                count = actions_dumps['sold']['quantity']
        if current_transaction is not None:
            item = Stock.query.get_or_404(current_transaction)
            quantity_sold.append([item.item_name, count, actions_dumps['sold']['b_price'], actions_dumps['sold']['price_sold']])
        data_plus_profit = []
        # print(quantity_sold)
        for data in quantity_sold:
            profit = (data[3] - data[2])*data[1]
            data_plus_profit.append(data + [profit])
        sorted_data_list = sorted(data_plus_profit, key=lambda x: x[1], reverse=True)
        # print(sorted_data_list)
        return sorted_data_list
    
    def add_kiraka(self, customer_name, item_name, quantity_borrowed):
        existing_customer = Kiraka.query.filter_by(customer_name=customer_name).first()
        print(existing_customer)
        if existing_customer is not None:
            print("Customer already exist")
            return False
        item = Stock.query.filter_by(item_name=item_name).first()
        # print(item)
        items_owned = {
            'items': [{'item_name': item_name, 'quantity_borrowed': quantity_borrowed, 'price_bought': item.selling_price}]
        }
        deni = Kiraka(customer_name=customer_name.lower(), items_owned=items_owned)
        db.session.add(deni)
        db.session.commit()
        return True

    def add_to_existing_kiraka(self, customer_name, item_name, quantity_borrowed):
        deni = Kiraka.query.filter_by(customer_name=customer_name).first()
        present = 0
        for item in deni.items_owned['items']:
            if item['item_name'] == item_name:
                item['quantity_borrowed'] += quantity_borrowed
                present = 1
                print(item['quantity_borrowed'], quantity_borrowed)
                flag_modified(deni, 'items_owned')
                break
        if present == 0:
            item = Stock.query.filter_by(item_name=item_name).first()
            new_item = {'item_name': item_name, 'quantity_borrowed': quantity_borrowed, 'price_bought':item.selling_price}
            deni.items_owned['items'].append(new_item)
            flag_modified(deni, 'items_owned')
        db.session.commit()

    def calculate_total_owned(self, customer_name):
        deni = Kiraka.query.filter_by(customer_name=customer_name).first()
        total = 0
        for item in deni.items_owned['items']:
            total += item['quantity_borrowed'] * item['price_bought']
        return total
    
    def pay_item_owned(self, customer_name, item_name):
        deni = Kiraka.query.filter_by(customer_name=customer_name).first()
        for item in deni.items_owned['items']:
            if item['item_name'] == item_name:
                deni.items_owned['items'].remove(item)
                break
        flag_modified(deni, 'items_owned')
        if len(deni.items_owned['items']) == 0:
            db.session.delete(deni)
        db.session.commit()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'asasdsdfwefqwfsdvfvdf'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock-management.db'
db = SQLAlchemy(app)

class Stock(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), unique=True, nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    transactions = db.relationship("Transactions", back_populates="itemname", cascade="all, delete-orphan")

class Transactions(db.Model):
    __tablename__ = "Transactions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("stock.id"))
    itemname = db.relationship("Stock", back_populates="transactions")
    actions = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    """
    {
        'purchase': {'quantity':added_quantity, 'price':item.buying_price}, 
        'sold': {'quantity':sold_quantity, 'price_sold':item.selling_price, 'b_price': item.buying_price}
    }
    """

class Kiraka(db.Model):
    __tablename__ = "Kiraka"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(250), unique=True,nullable=False)
    items_owned = db.Column(db.JSON)
    """
    {
        'items': [{'item_name': item_name, 'quantity_borrowed': quantity_borrowed, 'price_bought': item.selling_price}]
    }
    """

with app.app_context():
    db.create_all()

stock_manager = StockManager()

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/add", methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        name = request.form.get("itemName", "").lower()
        b_price = request.form.get("buyingPrice", "")
        s_price = request.form.get("sellingPrice", "")
        quantity = request.form.get("itemQuantity", "")
        success = stock_manager.add_item(name, b_price, s_price, quantity)
        if not success:
            flash('Item already exists')
            return redirect(url_for("add"))
        else:
            flash('Item added successfully')
        return redirect(url_for('stock'))
    return render_template("add.html") 

@app.route("/stock", methods=['POST', 'GET'])
def stock():
    all_stocks = db.session.query(Stock).order_by(Stock.item_name).all()
    if request.method == "POST":
        search_query = request.form.get('search', '').lower()
        results = Stock.query.filter(Stock.item_name.ilike(f'%{search_query}%')).all()
        return render_template("stock.html", all_stocks=results)
    return render_template("stock.html", all_stocks=all_stocks)

@app.route("/stock/delete/", methods=['POST', 'GET'])
def delete():
    stockId = request.args.get('stock_id')
    print(stockId)
    stock_to_delete = Stock.query.filter_by(id=stockId).first().item_name
    success = stock_manager.remove_item(stock_to_delete)
    if not success:
        flash("Couldn't delete item. Try Again")
    else:
        flash("Item deleted successfully")
    return redirect(url_for('stock'))


@app.route("/edit/<int:stock_id>", methods=['POST', 'GET'])
def edit(stock_id):
    stock_to_edit = db.get_or_404(Stock, stock_id)
    edit_form = EditForm(
        item_name=stock_to_edit.item_name.title(),
        buying_price=stock_to_edit.buying_price,
        selling_price=stock_to_edit.selling_price
    )
    if request.method == "POST":
        new_b_price = float(edit_form.buying_price.data)
        new_s_price = float(edit_form.selling_price.data)
        stock_manager.update_item_b_price(stock_to_edit.item_name, new_b_price)
        stock_manager.update_item_s_price(stock_to_edit.item_name, new_s_price)
        flash('Item edited successfully')
        return redirect(url_for('stock'))
    return render_template('edit.html', form=edit_form)

@app.route("/intransactions", methods=['POST', 'GET'])
def intransactions():
    all_transactions = db.session.execute(db.select(Transactions)).scalars().all()
    if request.method == "POST":
        start_date = datetime.strptime(request.form.get("startDate", ""), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("endDate", ""), "%Y-%m-%d")
        result = Transactions.query.filter(db.and_(Transactions.timestamp >= start_date, Transactions.timestamp <= end_date)).all()
        buy_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, json.loads(transaction.actions)['purchase']['quantity'], json.loads(transaction.actions)['purchase']['price']*json.loads(transaction.actions)['purchase']['quantity'], (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in result if json.loads(transaction.actions)['purchase']['quantity'] > 0]
        return render_template("purchasetransactions.html", transactions=buy_transactions)
    buy_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, json.loads(transaction.actions)['purchase']['quantity'], json.loads(transaction.actions)['purchase']['price']*json.loads(transaction.actions)['purchase']['quantity'], (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in all_transactions if json.loads(transaction.actions)['purchase']['quantity'] > 0]
    return render_template("purchasetransactions.html", transactions=buy_transactions)

@app.route("/outtransactions")
def outtransactions():
    all_transactions = db.session.execute(db.select(Transactions)).scalars().all()
    if request.method == "POST":
        start_date = datetime.strptime(request.form.get("startDate", ""), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("endDate", ""), "%Y-%m-%d")
        result = Transactions.query.filter(db.and_(Transactions.timestamp >= start_date, Transactions.timestamp <= end_date)).all()
        sold_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, json.loads(transaction.actions)['sold']['quantity'], json.loads(transaction.actions)['sold']['price_sold']*json.loads(transaction.actions)['sold']['quantity'], (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in result if json.loads(transaction.actions)['sold']['quantity'] > 0]
        return render_template("soldtransactions.html", transactions=sold_transactions)
    sold_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, json.loads(transaction.actions)['sold']['quantity'], json.loads(transaction.actions)['sold']['price_sold']*json.loads(transaction.actions)['sold']['quantity'], (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in all_transactions if json.loads(transaction.actions)['sold']['quantity'] > 0]
    return render_template("soldtransactions.html", transactions=sold_transactions)

@app.route("/restock", methods=['POST', 'GET'])
def restock():
    all_items = Stock.query.all()
    if request.method == "POST":
        item_restocked_name = request.form.get('stockName', '').lower()
        added_quantity = request.form.get('restockQuantity', '')
        success = stock_manager.add_item_quantity(item_restocked_name, int(added_quantity))
        if not success:
            flash("Item not found")
            return redirect(url_for('restock'))
        else:
            flash("Item restocked successfully")
        return redirect(url_for('stock'))
    return render_template("restock.html", stocks=all_items)

@app.route("/sold", methods=['POST', 'GET'])
def sold():
    all_items = Stock.query.all()
    if request.method == "POST":
        item_sold_name = request.form.get('stockName', '').lower()
        sold_quantity = request.form.get('restockQuantity', '')
        success = stock_manager.sell_item(item_sold_name, int(sold_quantity))
        if success:
            flash("Item sold successfully")
        elif success == 1:
            flash("Item not found")
            return redirect(url_for('sold'))
        else:
            flash("Not enough stock to sell this amount")
            return redirect(url_for('sold'))
        return redirect(url_for('stock'))
    return render_template("sold.html", stocks=all_items)

@app.route("/profit", methods=['POST', 'GET'])
def profit():
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get("startDate", ""), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("endDate", ""), "%Y-%m-%d")
        data_sold = stock_manager.number_of_selled_items(start_date=start_date, end_date=end_date)
    data_sold = stock_manager.number_of_selled_items()
    return render_template("profit.html", all_data=data_sold)

@app.route("/kiraka", methods=['POST', 'GET'])
def kiraka():
    db.session.query(Stock).order_by(Stock.item_name).all()
    kiraka_data = db.session.query(Kiraka).order_by(Kiraka.customer_name).all()
    if request.method == "POST":
       search_query = request.form.get('search', '').lower()
       results = Kiraka.query.filter(Kiraka.customer_name.ilike(f'%{search_query}%')).all()
       return render_template("kiraka.html", all_data=results)
    return render_template("kiraka.html", all_data=kiraka_data)

@app.route("/new_deni", methods=['POST', 'GET'])
def new_deni():
    all_items = Stock.query.all()
    if request.method == "POST":
        customer_name = request.form.get('customerName', '').lower()
        print(customer_name)
        item_burrowed = request.form.get('stockName', '').lower()
        quantity_burrowed = int(request.form.get('burrowedQuantity', ''))
        success = stock_manager.add_kiraka(customer_name=customer_name, item_name=item_burrowed, quantity_borrowed=quantity_burrowed)
        if not success:
            print('im being printed')
            flash("Customer already exists")
            return redirect(url_for('new_deni'))
        else:
            flash("Customer added successfully")
        return redirect(url_for('kiraka'))
    return render_template('add_customer.html', stocks=all_items)

@app.route("/existing_deni/<int:customer_id>", methods=['POST', 'GET'])
def existing_deni(customer_id):
    customer_details = Kiraka.query.get_or_404(customer_id)
    all_items_owned = customer_details.items_owned['items']
    existing_items = [stock for stock in all_items_owned]
    available_stocks = Stock.query.all()
    if request.method == "POST":
        customer_name = customer_details.customer_name
        item_burrowed = request.form.get('stockName', '').lower()
        quantity_burrowed = int(request.form.get('burrowedQuantity', ''))
        stock_manager.add_to_existing_kiraka(customer_name=customer_name, item_name=item_burrowed, quantity_borrowed=quantity_burrowed)
        return redirect(url_for('kiraka'))
    return render_template('add_kiraka.html', existing_items=existing_items, available_stocks=available_stocks, customer=customer_details)

@app.route("/pay_deni/<int:customer_id>", methods=['POST', 'GET'])
def pay_deni(customer_id):
    customer_details = Kiraka.query.get_or_404(customer_id)
    items_owned = customer_details.items_owned['items']
    if request.method == "POST":
        selected_items = request.form.getlist('selected_items')
        for item_name in selected_items:
            stock_manager.pay_item_owned(customer_name=customer_details.customer_name, item_name=item_name.lower())
        flash("Item Paid For")
        return redirect(url_for('kiraka'))
    return render_template('pay_deni.html', items_owned=items_owned, customer=customer_details)

# with app.app_context():
    # stock_manager.add_to_existing_kiraka('Ruben Hodge', 'Jameson', 2)
    # stock_manager = StockManager()
    # stock_manager.sell_item("Best Gin", 6)
    # stock_manager.add_item_quantity("Chrome", 10)
    # stock_manager.sell_item("Chrome", 3)
    # stock_manager.add_item_quantity("Best Gin", 8)
    # stock_manager.sell_item("Kenya Cane", 2)
    # stock_manager.sell_item("General Meakings", 10)
    # stock_manager.remove_item("Best Gin")
    # stock_manager.update_item_price("Best Gin", 1000)
    # stock_manager.add_item("Chrome", 300, 500, 2)
    # stock_manager.add_item("Best Gin", 500, 550, 6)
    # stock_manager.add_item("Kenya Cane", 900, 1200)
    # stock_manager.add_item("General Meakings", 400, 750, 13)
    # stock_manager.display_stock()
    # stock_manager.number_of_selled_items()
    # stock_manager.number_of_selled_items()

if __name__ == '__main__':
    app.run(debug=True)