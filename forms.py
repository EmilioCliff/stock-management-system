from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired

class AddForm(FlaskForm):
    item_name = StringField(label="Stock Name", validators=[DataRequired()])
    item_quantity = IntegerField(label="Stock Quantity", validators=[DataRequired()])
    buying_price = FloatField(label="Buying Price", validators=[DataRequired()])
    selling_price = FloatField(label="Selling Price", validators=[DataRequired()])
    submit = SubmitField("Add")

class EditForm(FlaskForm):
    item_name = StringField(label="Stock Name", validators=[DataRequired()])
    buying_price = FloatField(label="Buying Price", validators=[DataRequired()])
    selling_price = FloatField(label="Selling Price", validators=[DataRequired()])
    submit = SubmitField("Edit")

class Restocked(FlaskForm):
    item_name = StringField(label="Item Name")
    item_quantity = IntegerField(label="Added Quantity", validators=[DataRequired()])
    submit = SubmitField("Add")

class Sold(FlaskForm):
    item_name = StringField(label="Item Name")
    item_quantity = IntegerField(label="Sold Quantity", validators=[DataRequired()])
    submit = SubmitField("Add")
