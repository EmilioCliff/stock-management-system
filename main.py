from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class StockManager:
    def add_item(self, name, price, quantity=0) -> None:
        with current_app.app_context():
            existing_item = Stock.query.filter_by(item_name=name).first()
            if existing_item:
                print("Item already exist")
            else:
                item = Stock(item_name=name, item_price=price, item_quantity=quantity)
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
                item.item_price = new_price
                db.session.commit()
                print(f"Changed item price to {new_price}")
            else:
                print("Couldn't change item price")

    def sell_item(self, name, quantity_sold):
        with current_app.app_context():
            item = Stock.query.filter_by(item_name=name).first()
            if item:
                if item.item_quantity >= quantity_sold:
                    item.item_quantity -= quantity_sold
                    transaction = Transactions(item_id=item.id, sold_quantity=quantity_sold)
                    db.session.add(transaction)
                    db.session.commit()
                    print(f"Subtracted {quantity_sold} from {item.item_quantity}")
                else:
                    print(f"Not enough quantity to subtract {quantity_sold} from {item.item_quantity}")
            else:
                print("Couldn't find item")
        
    def display_stock(self):
        with current_app.app_context():
            items = Stock.query.all()
            for item in items:
                print(f"ID: {item.id}, ITEM: {item.item_name}, Quantity: {item.item_quantity}, Price: {item.item_price}")

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock-management.db'
db = SQLAlchemy(app)

class Stock(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), unique=True, nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)
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

# with app.app_context():
#     stock_manager = StockManager()
#     stock_manager.add_item_quantity("Chrome", 10)
#     stock_manager.remove_item("Kenya Cane")
#     stock_manager.update_item_price("Best Gin", 1000)
#     stock_manager.add_item("Chrome", 300, 2)
#     stock_manager.add_item("Best Gin", 500, 6)
#     stock_manager.add_item("Kenya Cane", 900)
#     stock_manager.display_stock()

if __name__ == '__main__':
    app.run(debug=True)