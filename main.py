from flask import Flask, current_app, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bootstrap import Bootstrap5
from forms import AddForm, EditForm, Restocked, Sold

# Define stockmanager that will have methods for daily operations
class StockManager:
    def transact(self, item_id, sold_quantity, added_quantity):
        transaction = Transactions(item_id=item_id, sold_quantity=sold_quantity, added_quantity=added_quantity)
        db.session.add(transaction)
        db.session.commit()

    def add_item(self, name, b_price, s_price, quantity=0) -> None:
        with current_app.app_context():
            existing_item = Stock.query.filter_by(item_name=name).first()
            if existing_item:
                print("Item already exist")
            else:
                item = Stock(item_name=name, buying_price=b_price, selling_price=s_price, item_quantity=quantity)
                db.session.add(item)
                db.session.commit()
                self.transact(Stock.query.filter_by(item_name=name).first().id, 0, quantity)
                print(f"{item.item_name} added to db")
    
    def remove_item(self, name):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                db.session.delete(item)
                db.session.commit()
                print(f"Removed {item.item_name}")
            else:
                print(f"Item {name} not found")

    def add_item_quantity(self, name, quantity):
        with current_app.app_context():
            print(name, quantity)
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                self.transact(item.id, 0, quantity)
                item.item_quantity += quantity
                db.session.commit()
                print(f"added item quantity by {quantity}")
            else:
                print("Couldn't add item quantity")


    def update_item_s_price(self, name, new_price):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.selling_price = new_price
                db.session.commit()
                print(f"Changed item price to {new_price}")
            else:
                print("Couldn't change item price")

    def update_item_b_price(self, name, new_price):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.buying_price = new_price
                db.session.commit()
                print(f"Changed item price to {new_price}")
            else:
                print("Couldn't change item price")

    def sell_item(self, name, quantity_sold):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                print(f"Subtracted {quantity_sold} from {item.item_quantity}")
                if item.item_quantity >= quantity_sold:
                    item.item_quantity -= quantity_sold
                    self.transact(item.id, quantity_sold, 0)
                    # transaction = Transactions(item_id=item.id, sold_quantity=quantity_sold, added_quantity=0)
                    # db.session.add(transaction)
                    # db.session.commit()
                else:
                    print(f"Not enough quantity to subtract {quantity_sold} from {item.item_quantity}")
            else:
                print("Couldn't find item")
        
    def display_stock(self):
        with current_app.app_context():
            items = Stock.query.all()
            for item in items:
                print(f"ID: {item.id}, ITEM: {item.item_name}, Quantity: {item.item_quantity}, Buying Price: {item.buying_price}, Selling Price: {item.selling_price}")

    def number_of_selled_items(self):
        transactions = db.session.execute(db.select(Transactions).order_by(Transactions.item_id)).scalars()
        quantity_sold = {}
        count = 0
        current_transaction = None
        for transaction in transactions:
            if current_transaction == None:
                current_transaction = transaction.item_id
            if current_transaction == transaction.item_id:
                count += transaction.sold_quantity
            else:
                item = Stock.query.get_or_404(current_transaction)
                quantity_sold[item.item_name] = {"quantity_sold":count}
                current_transaction = transaction.item_id
                count = transaction.sold_quantity
        if current_transaction is not None:
            item = Stock.query.get_or_404(current_transaction)
            quantity_sold[item.item_name] = {"quantity_sold": count}
        for item, details in quantity_sold.items():
            item_to_calculate = Stock.query.filter_by(item_name=item).first()
            profit = (item_to_calculate.selling_price - item_to_calculate.buying_price)*details['quantity_sold']
            print(f"{item}:{details['quantity_sold']} has made a profit of {profit}")


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
    sold_quantity = db.Column(db.Integer, nullable=False)
    added_quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

stock_manager = StockManager()

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/add", methods=['POST', 'GET'])
def add():
    add_form = AddForm()
    if request.method == 'POST':
        print('Adding')
        name = add_form.item_name.data
        b_price = add_form.buying_price.data
        s_price = add_form.selling_price.data
        quantity = add_form.item_quantity.data
        stock_manager.add_item(name, b_price, s_price, quantity)
        return redirect(url_for('stock'))
    return render_template("add.html", form=add_form) 

@app.route("/stock", methods=['POST', 'GET'])
def stock():
    all_stocks = db.session.execute(db.select(Stock)).scalars().all()
    if request.method == "POST":
        search_query = request.form.get('search', '')
        results = Stock.query.filter(Stock.item_name.ilike(f'%{search_query}%')).all()
        return render_template("stock.html", all_stocks=results)
    return render_template("stock.html", all_stocks=all_stocks)

@app.route("/stock/delete/<int:stockId>", methods=['POST', 'GET'])
def delete(stockId):
    print('Before printing')
    if request.method == "POST":
        stock_to_delete = Stock.query.filter_by(id=stockId).first().item_name
        stock_manager.remove_item(stock_to_delete)
        print('Deleting')
    return redirect(url_for('home'))


@app.route("/edit/<int:stock_id>", methods=['POST', 'GET'])
def edit(stock_id):
    stock_to_edit = db.get_or_404(Stock, stock_id)
    edit_form = EditForm(
        item_name=stock_to_edit.item_name,
        buying_price=stock_to_edit.buying_price,
        selling_price=stock_to_edit.selling_price
    )
    if request.method == "POST":
        new_b_price = float(edit_form.buying_price.data)
        new_s_price = float(edit_form.selling_price.data)
        stock_manager.update_item_b_price(stock_to_edit.item_name, new_b_price)
        stock_manager.update_item_s_price(stock_to_edit.item_name, new_s_price)
        return redirect(url_for('stock'))
    return render_template('edit.html', form=edit_form)

@app.route("/intransactions")
def intransactions():
    all_transactions = db.session.execute(db.select(Transactions)).scalars().all()
    buy_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, transaction.added_quantity, db.get_or_404(Stock, transaction.item_id).buying_price*transaction.added_quantity, (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in all_transactions if transaction.added_quantity > 0]
    return render_template("purchasetransactions.html", transactions=buy_transactions)

@app.route("/outtransactions")
def outtransactions():
    all_transactions = db.session.execute(db.select(Transactions)).scalars().all()
    sold_transactions = [[db.get_or_404(Stock, transaction.item_id).item_name, transaction.sold_quantity, db.get_or_404(Stock, transaction.item_id).buying_price*transaction.sold_quantity, (transaction.timestamp).strftime("%Y-%m-%d %H:%M:%S")]for transaction in all_transactions if transaction.sold_quantity > 0]
    return render_template("soldtransactions.html", transactions=sold_transactions)

@app.route("/restock", methods=['POST', 'GET'])
def restock():
    all_items = Stock.query.all()
    if request.method == "POST":
        item_restocked_name = request.form.get('stockName', '')
        added_quantity = request.form.get('restockQuantity', '')
        stock_manager.add_item_quantity(item_restocked_name, int(added_quantity))
        return redirect(url_for('stock'))
    return render_template("restock.html", stocks=all_items)

@app.route("/sold", methods=['POST', 'GET'])
def sold():
    all_items = Stock.query.all()
    if request.method == "POST":
        item_sold_name = request.form.get('stockName', '')
        sold_quantity = request.form.get('restockQuantity', '')
        stock_manager.sell_item(item_sold_name, int(sold_quantity))
        return redirect(url_for('stock'))
    return render_template("sold.html", stocks=all_items)

# with app.app_context():
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


if __name__ == '__main__':
    app.run(debug=True)