from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Define stockmanager that will have methods for daily operations
class StockManager:
    def add_item(self, name, b_price, s_price, quantity=0) -> None:
        with current_app.app_context():
            existing_item = Stock.query.filter_by(item_name=name).first()
            if existing_item:
                print("Item already exist")
            else:
                item = Stock(item_name=name, buying_price=b_price, selling_price=s_price, item_quantity=quantity)
                db.session.add(item)
                db.session.commit()
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
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.item_quantity += quantity
                db.session.commit()
                print(f"added item quantity by {quantity}")
            else:
                print("Couldn't add item quantity")

    def update_item_price(self, name, new_price):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                item.selling_price = new_price
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
                    transaction = Transactions(item_id=item.id, sold_quantity=quantity_sold)
                    db.session.add(transaction)
                    db.session.commit()
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


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock-management.db'
db = SQLAlchemy(app)

class Stock(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), unique=True, nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    transactions = db.relationship("Transactions", back_populates="itemname")

class Transactions(db.Model):
    __tablename__ = "Transactions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("stock.id"))
    itemname = db.relationship("Stock", back_populates="transactions")
    sold_quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

with app.app_context():
    stock_manager = StockManager()
    # stock_manager.sell_item("Best Gin", 1)
    # stock_manager.add_item_quantity("Chrome", 10)
    # stock_manager.sell_item("Chrome", 3)
    # stock_manager.add_item_quantity("Kenya Cane", 5)
    # stock_manager.sell_item("Kenya Cane", 2)
#     stock_manager.remove_item("Kenya Cane")
#     stock_manager.update_item_price("Best Gin", 1000)
    # stock_manager.add_item("Chrome", 300, 500, 2)
    # stock_manager.add_item("Best Gin", 500, 550, 6)
    # stock_manager.add_item("Kenya Cane", 900, 1200)
    # stock_manager.display_stock()
    stock_manager.number_of_selled_items()


if __name__ == '__main__':
    app.run(debug=True)