from models import Stock, Transactions, db

class StockManager:
    def add_item(self, name, price, quantity=0) -> None:
        item = Stock(item_name=name, item_price=price, item_quantity=quantity)
        db.session.add(item)
        db.session.commit()
        print(f"{item} added to db")
    
    def remove_item(self, name):
        item = Stock.query.filter_by(item_name=name).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            print(f"Removed {item}")
        else:
            print(f"Item {item} not found")

    def add_item_quantity(self, name, quantity):
        item = Stock.query.filter_by(item_name=name).first()
        if item:
            item.item_quantity += quantity
            db.session.commit()
            print(f"added item quantity by {quantity}")
        else:
            print("Couldn't add item quantity")

    def update_item_price(self, name, new_price):
        item = Stock.query.filter_by(item_name=name).first()
        if item:
            item.item_price = new_price
            db.session.commit()
            print(f"Changed item price to {new_price}")
        else:
            print("Couldn't change item price")

    def sell_item(self, name, quantity_sold):
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
        items = Stock.query.all()
        for item in items:
            print(f"ID: {item.id}, ITEM: {item.item_name}, Quantity: {item.item_quantity}, Price: {item.item_price}")


