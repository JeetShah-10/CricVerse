"""
Comprehensive Australian Vegetarian Concessions Generator
Creates 8-10 diverse cuisine concession stalls per stadium with 10-15 vegetarian items each
"""

import random
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from app import app, db
from models import Concession, MenuItem, Stadium
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveAussieConcessionGenerator:
    def __init__(self):
        # Diverse Australian vegetarian concession concepts
        self.concession_concepts = [
            {
                'name': 'Aussie Veggie Grill',
                'category': 'Australian BBQ',
                'description': 'Traditional Australian BBQ flavors with a vegetarian twist',
                'menu_items': [
                    ('Veggie Snags & Onions', 'Classic Australian vegetarian sausages with caramelized onions on a buttery roll', 8.50, 12.00),
                    ('Halloumi Burger', 'Grilled halloumi with beetroot, lettuce, tomato, and Aussie sauce', 14.00, 18.00),
                    ('Mushroom & Barley Patty', 'House-made patty with native herbs and bush tomato relish', 13.50, 17.50),
                    ('Grilled Corn on the Cob', 'Sweet corn with herb butter and parmesan', 6.00, 9.00),
                    ('Veggie Kebabs', 'Marinated vegetables and tofu on skewers', 11.00, 15.00),
                    ('Pumpkin & Feta Salad', 'Roasted pumpkin with feta, rocket, and pepitas', 12.00, 16.00),
                    ('Damper Bread', 'Traditional Australian bread with golden syrup butter', 5.50, 8.00),
                    ('Lamington Slice', 'Classic sponge cake with coconut and raspberry jam', 4.50, 7.00),
                    ('ANZAC Biscuits (3)', 'Traditional oat and coconut biscuits', 4.00, 6.50),
                    ('Lemon Myrtle Iced Tea', 'Refreshing native Australian tea', 5.00, 7.50),
                    ('Flat White Coffee', 'Perfect Australian-style coffee', 4.50, 6.50),
                    ('Bundaberg Ginger Beer', 'Iconic Australian ginger beer', 4.00, 6.00),
                    ('Meat Pie (Veggie)', 'Traditional pastry with lentil and vegetable filling', 7.50, 11.00),
                    ('Sausage Roll (Veggie)', 'Flaky pastry with seasoned vegetable filling', 6.50, 9.50),
                    ('Potato Wedges', 'Crispy wedges with sour cream and sweet chili', 8.00, 12.00)
                ]
            },
            {
                'name': 'Mediterranean Mezze Bar',
                'category': 'Mediterranean',
                'description': 'Fresh Mediterranean flavors perfect for cricket matches',
                'menu_items': [
                    ('Mezze Platter for Two', 'Hummus, tzatziki, olives, feta, dolmades, and pita', 22.00, 28.00),
                    ('Falafel Wrap', 'Crispy falafels with tahini, salad, and pickles', 12.00, 16.00),
                    ('Greek Village Salad', 'Tomatoes, cucumber, olives, feta, and oregano', 13.00, 17.00),
                    ('Spanakopita', 'Spinach and feta in crispy phyllo pastry', 8.50, 12.50),
                    ('Halloumi & Grilled Veggie Stack', 'Layered with zucchini, eggplant, and capsicum', 15.00, 19.00),
                    ('Turkish Delight', 'Rose and lemon flavored confection', 3.50, 5.50),
                    ('Baklava', 'Honey-soaked phyllo with nuts', 6.00, 9.00),
                    ('Pita Bread & Dips Trio', 'Fresh pita with hummus, baba ganoush, tzatziki', 9.50, 13.50),
                    ('Mediterranean Stuffed Capsicum', 'Bell peppers with rice, herbs, and pine nuts', 11.00, 15.00),
                    ('Greek Yoghurt with Honey', 'Thick yoghurt drizzled with native honey', 7.00, 10.00),
                    ('Lemon & Herb Potatoes', 'Roasted baby potatoes with Mediterranean herbs', 8.00, 11.50),
                    ('Fresh Mint Lemonade', 'Cooling drink with fresh mint', 5.50, 8.00),
                    ('Turkish Coffee', 'Strong coffee with traditional preparation', 4.00, 6.00),
                    ('Ouzo Mocktail', 'Anise-flavored non-alcoholic beverage', 6.00, 9.00),
                    ('Vegetarian Moussaka', 'Layered eggplant with béchamel sauce', 16.00, 20.00)
                ]
            },
            {
                'name': 'Asian Fusion Kitchen',
                'category': 'Asian Fusion',
                'description': 'Modern Asian cuisine with fresh Australian ingredients',
                'menu_items': [
                    ('Buddha Bowl', 'Quinoa, edamame, avocado, pickled veg, miso dressing', 16.00, 20.00),
                    ('Vegetable Ramen', 'Rich vegetable broth with noodles and seasonal vegetables', 15.00, 19.00),
                    ('Tofu Bao Buns (3)', 'Steamed buns with marinated tofu and Asian slaw', 13.00, 17.00),
                    ('Vegetable Pad Thai', 'Rice noodles with tofu, bean sprouts, and lime', 14.00, 18.00),
                    ('Korean Bibimbap', 'Rice bowl with seasoned vegetables and gochujang', 15.50, 19.50),
                    ('Miso Glazed Eggplant', 'Japanese-style glazed eggplant with sesame', 12.00, 16.00),
                    ('Vegetable Spring Rolls (4)', 'Crispy rolls with sweet and sour sauce', 9.00, 13.00),
                    ('Thai Green Curry (Veg)', 'Coconut curry with vegetables and jasmine rice', 16.50, 20.50),
                    ('Teriyaki Mushroom Burger', 'Portobello mushroom with Asian slaw', 13.50, 17.50),
                    ('Matcha Ice Cream', 'Premium green tea ice cream', 6.50, 9.50),
                    ('Mango Sticky Rice', 'Traditional Thai dessert', 8.00, 11.00),
                    ('Green Tea', 'Premium Japanese sencha', 3.50, 5.50),
                    ('Lychee Sparkling Water', 'Refreshing Asian-inspired drink', 4.50, 6.50),
                    ('Vietnamese Iced Coffee (Veg)', 'Strong coffee with condensed oat milk', 5.50, 8.00),
                    ('Kimchi Fried Rice', 'Spicy fermented cabbage with vegetables', 13.00, 17.00)
                ]
            },
            {
                'name': 'Italian Trattoria',
                'category': 'Italian',
                'description': 'Authentic Italian flavors with fresh Australian produce',
                'menu_items': [
                    ('Margherita Pizza (Personal)', 'San Marzano tomatoes, fresh mozzarella, basil', 16.00, 20.00),
                    ('Vegetarian Pasta Primavera', 'Seasonal vegetables with garlic and olive oil', 17.00, 21.00),
                    ('Eggplant Parmigiana', 'Layers of eggplant, tomato sauce, and cheese', 18.00, 22.00),
                    ('Arancini Balls (4)', 'Risotto balls with mozzarella center', 11.00, 15.00),
                    ('Caprese Salad', 'Buffalo mozzarella, tomato, basil, balsamic glaze', 14.00, 18.00),
                    ('Bruschetta Trio', 'Three varieties on toasted sourdough', 12.00, 16.00),
                    ('Mushroom Risotto', 'Creamy arborio rice with mixed mushrooms', 19.00, 23.00),
                    ('Tiramisu', 'Classic coffee-flavored dessert', 8.50, 12.00),
                    ('Gelato (2 scoops)', 'Artisan gelato - vanilla, chocolate, or pistachio', 7.00, 10.00),
                    ('Italian Soda', 'Sparkling water with fruit syrups', 4.50, 6.50),
                    ('Espresso', 'Traditional Italian coffee', 3.50, 5.00),
                    ('Limoncello Mocktail', 'Lemon-flavored refreshing drink', 6.00, 8.50),
                    ('Focaccia Bread', 'Herb-topped Italian flatbread', 6.50, 9.50),
                    ('Pesto Gnocchi', 'Potato dumplings with basil pesto', 16.50, 20.50),
                    ('Italian Antipasto Plate', 'Selection of cheeses, olives, and vegetables', 20.00, 24.00)
                ]
            },
            {
                'name': 'Mexican Cantina',
                'category': 'Mexican',
                'description': 'Vibrant Mexican cuisine with fresh, healthy options',
                'menu_items': [
                    ('Vegetarian Burrito Bowl', 'Black beans, rice, guacamole, salsa, cheese', 15.00, 19.00),
                    ('Quesadillas (Veg)', 'Cheese and vegetable filled tortillas', 12.00, 16.00),
                    ('Nachos Supreme (Veg)', 'Corn chips with beans, cheese, jalapeños, guacamole', 16.00, 20.00),
                    ('Veggie Tacos (3)', 'Soft shells with seasoned vegetables and lime', 13.00, 17.00),
                    ('Mexican Street Corn', 'Grilled corn with lime, chili, and cotija cheese', 8.00, 11.00),
                    ('Black Bean Enchiladas', 'Corn tortillas with black beans and cheese sauce', 16.50, 20.50),
                    ('Churros with Chocolate', 'Fried dough pastry with rich chocolate sauce', 8.50, 12.00),
                    ('Fresh Guacamole & Chips', 'House-made guacamole with corn tortilla chips', 10.00, 14.00),
                    ('Mexican Rice Bowl', 'Cilantro lime rice with roasted vegetables', 12.50, 16.50),
                    ('Horchata', 'Traditional rice and cinnamon drink', 5.00, 7.50),
                    ('Agua Fresca', 'Fresh fruit water - watermelon or cucumber', 4.50, 6.50),
                    ('Mexican Hot Chocolate', 'Spiced chocolate drink', 5.50, 8.00),
                    ('Vegetarian Tamales (2)', 'Corn masa with cheese and green chiles', 11.00, 15.00),
                    ('Pozole (Veg)', 'Traditional hominy soup with vegetables', 13.50, 17.50),
                    ('Tres Leches Cake', 'Three milk sponge cake', 7.50, 10.50)
                ]
            },
            {
                'name': 'Indian Spice Junction',
                'category': 'Indian',
                'description': 'Authentic Indian vegetarian cuisine with aromatic spices',
                'menu_items': [
                    ('Butter Chicken (Paneer)', 'Creamy tomato curry with paneer and rice', 18.00, 22.00),
                    ('Palak Paneer', 'Spinach curry with cottage cheese', 16.00, 20.00),
                    ('Vegetable Biryani', 'Fragrant basmati rice with mixed vegetables', 17.00, 21.00),
                    ('Dal Makhani', 'Rich black lentil curry with cream', 14.00, 18.00),
                    ('Chole Bhature', 'Spicy chickpeas with fried bread', 15.00, 19.00),
                    ('Samosas (4)', 'Crispy pastries with spiced potato filling', 8.00, 12.00),
                    ('Naan Bread (Garlic)', 'Traditional Indian bread with garlic and herbs', 5.00, 8.00),
                    ('Mango Lassi', 'Yogurt drink with fresh mango', 6.00, 9.00),
                    ('Gulab Jamun (3)', 'Sweet milk dumplings in rose syrup', 7.00, 10.00),
                    ('Masala Chai', 'Spiced tea with milk and cardamom', 4.00, 6.00),
                    ('Tandoori Vegetables', 'Clay oven roasted seasonal vegetables', 15.50, 19.50),
                    ('Raita', 'Cooling yogurt with cucumber and mint', 5.50, 8.50),
                    ('Vegetable Korma', 'Mild coconut curry with mixed vegetables', 16.50, 20.50),
                    ('Papadum (4)', 'Crispy lentil wafers with chutneys', 6.00, 9.00),
                    ('Kulfi', 'Traditional Indian ice cream with pistachios', 6.50, 9.50)
                ]
            },
            {
                'name': 'Healthy Harvest',
                'category': 'Health Food',
                'description': 'Nutritious, organic options for health-conscious fans',
                'menu_items': [
                    ('Superfood Salad Bowl', 'Quinoa, kale, berries, nuts, and tahini dressing', 16.50, 20.50),
                    ('Acai Bowl', 'Acai with granola, fresh fruit, and coconut', 14.00, 18.00),
                    ('Green Smoothie', 'Spinach, banana, mango, and coconut water', 8.00, 11.00),
                    ('Avocado Toast (Sourdough)', 'Smashed avocado with seeds and microgreens', 12.00, 16.00),
                    ('Veggie Protein Bowl', 'Lentils, chickpeas, quinoa, and roasted vegetables', 17.00, 21.00),
                    ('Raw Energy Balls (4)', 'Dates, nuts, and superfood powder', 7.00, 10.00),
                    ('Kale Chips', 'Dehydrated kale with nutritional yeast', 6.00, 9.00),
                    ('Coconut Water', 'Fresh young coconut water', 5.00, 7.50),
                    ('Chia Pudding', 'Overnight chia with berries and almonds', 9.00, 12.50),
                    ('Cold-pressed Juice', 'Green vegetable and fruit blend', 8.50, 12.00),
                    ('Gluten-free Wrap', 'Hummus and vegetable wrap in rice paper', 13.00, 17.00),
                    ('Kombucha', 'Probiotic fermented tea drink', 6.50, 9.50),
                    ('Spirulina Smoothie Bowl', 'Blue-green algae with tropical fruits', 15.00, 19.00),
                    ('Raw Chocolate Slice', 'Cacao, dates, and nuts - no baking required', 8.00, 11.50),
                    ('Herbal Tea Selection', 'Chamomile, peppermint, or ginger', 4.00, 6.50)
                ]
            },
            {
                'name': 'American Diner',
                'category': 'American',
                'description': 'Classic American comfort food with vegetarian options',
                'menu_items': [
                    ('Veggie Burger Deluxe', 'Plant-based patty with all the fixings', 16.00, 20.00),
                    ('Mac & Cheese Bowl', 'Creamy macaroni with three cheese blend', 13.00, 17.00),
                    ('Loaded Sweet Potato Fries', 'With black beans, cheese, and sour cream', 12.00, 16.00),
                    ('Grilled Cheese Sandwich', 'Three cheese blend on sourdough', 10.00, 14.00),
                    ('Caesar Salad (Veg)', 'Romaine lettuce with parmesan and croutons', 13.50, 17.50),
                    ('Onion Rings', 'Beer-battered and crispy with ranch dip', 9.00, 13.00),
                    ('Milkshake', 'Vanilla, chocolate, or strawberry', 7.00, 10.00),
                    ('Apple Pie Slice', 'Traditional with vanilla ice cream', 8.50, 12.00),
                    ('Buffalo Cauliflower Wings', 'Spicy battered cauliflower with blue cheese', 11.00, 15.00),
                    ('Root Beer Float', 'Classic American soda with vanilla ice cream', 6.50, 9.50),
                    ('Pancakes (3)', 'Fluffy pancakes with maple syrup and butter', 12.00, 16.00),
                    ('Coleslaw', 'Creamy cabbage and carrot salad', 5.50, 8.50),
                    ('Cheese Fries', 'Golden fries topped with melted cheese', 10.00, 14.00),
                    ('Veggie Chili Bowl', 'Three-bean chili with cornbread', 14.00, 18.00),
                    ('Chocolate Brownie Sundae', 'Warm brownie with ice cream and sauce', 9.50, 13.00)
                ]
            },
            {
                'name': 'Lebanese Garden',
                'category': 'Lebanese',
                'description': 'Fresh Lebanese cuisine with vegetarian specialties',
                'menu_items': [
                    ('Vegetarian Mezza Feast', 'Selection of Lebanese appetizers and dips', 24.00, 28.00),
                    ('Falafel Plate', 'Fresh falafels with tahini, salad, and pita', 15.00, 19.00),
                    ('Tabbouleh Salad', 'Parsley, tomato, and bulgur with lemon dressing', 11.00, 15.00),
                    ('Stuffed Vine Leaves (6)', 'Rice and herb filling in grape leaves', 12.00, 16.00),
                    ('Manakish', 'Flatbread with za\'atar and olive oil', 8.00, 12.00),
                    ('Vegetarian Kibbeh', 'Bulgur and vegetable fritters', 10.00, 14.00),
                    ('Muhammara', 'Spicy walnut and pomegranate dip with pita', 9.50, 13.50),
                    ('Fattoush Salad', 'Mixed greens with pomegranate and sumac', 13.00, 17.00),
                    ('Lebanese Rice', 'Fragrant rice with vermicelli and almonds', 7.00, 10.00),
                    ('Baklava Assortment', 'Mixed honey-soaked pastries with nuts', 8.50, 12.50),
                    ('Ayran', 'Salted yogurt drink with mint', 4.50, 6.50),
                    ('Lebanese Coffee', 'Strong coffee with cardamom', 4.00, 6.00),
                    ('Rose Water Lemonade', 'Refreshing drink with rose essence', 5.50, 8.00),
                    ('Cheese Fatayer (3)', 'Triangular pastries filled with cheese', 9.00, 13.00),
                    ('Knafeh', 'Sweet cheese pastry with syrup', 9.50, 13.50)
                ]
            },
            {
                'name': 'German Beer Garden',
                'category': 'German',
                'description': 'Authentic German flavors perfect for stadium dining',
                'menu_items': [
                    ('Vegetarian Bratwurst', 'Plant-based sausage with sauerkraut and mustard', 12.00, 16.00),
                    ('Pretzel with Beer Cheese', 'Traditional soft pretzel with warm cheese dip', 9.00, 13.00),
                    ('Sauerkraut & Potato Salad', 'Traditional German side dishes', 8.00, 11.00),
                    ('Vegetable Schnitzel', 'Breaded eggplant with lemon and herbs', 16.00, 20.00),
                    ('German Potato Dumplings', 'Kartoffelknödel with mushroom gravy', 13.00, 17.00),
                    ('Red Cabbage Salad', 'Sweet and sour red cabbage with apples', 7.50, 10.50),
                    ('Black Forest Cake', 'Chocolate cake with cherries and cream', 8.50, 12.00),
                    ('Apple Strudel', 'Flaky pastry with cinnamon apples', 7.00, 10.00),
                    ('German Mustard Selection', 'Three types with crusty bread', 6.00, 9.00),
                    ('Non-alcoholic Beer', 'Traditional German alcohol-free beer', 5.00, 7.50),
                    ('Apfelschorle', 'Apple juice with sparkling water', 4.50, 6.50),
                    ('Spaetzle', 'Traditional egg noodles with herbs', 10.00, 14.00),
                    ('Cheese Spaetzle', 'Noodles with melted cheese and onions', 14.00, 18.00),
                    ('Rye Bread Sandwich', 'Open-faced with vegetables and cheese', 11.00, 15.00),
                    ('Lebkuchen', 'Spiced gingerbread cookies (3)', 5.50, 8.50)
                ]
            }
        ]
        
        # Stadium zones for concession placement
        self.location_zones = [
            'North Stand Concourse', 'South Stand Concourse', 'East Stand Upper', 'West Stand Upper',
            'Premium Club Level', 'Family Zone', 'General Admission', 'Members Reserve',
            'Corporate Box Level', 'Ground Floor Concourse'
        ]
        
        # Operating hours options
        self.opening_hours = [
            '2 hours before match - 30 minutes after',
            '3 hours before match - 1 hour after',
            'Gates open - Match end',
            'All day during events'
        ]

    def clear_existing_concessions(self):
        """Clear all existing concession and menu item data"""
        with app.app_context():
            try:
                logger.info("🗑️ Clearing existing concession data...")
                
                # Clear menu items first (foreign key constraint)
                db.session.execute(text("DELETE FROM menu_item"))
                db.session.execute(text("DELETE FROM concession"))
                db.session.commit()
                
                logger.info("✅ Existing concession data cleared successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Error clearing concession data: {e}")
                db.session.rollback()
                return False

    def generate_concessions_for_stadium(self, stadium_id: int, stadium_name: str) -> Tuple[List[Dict], List[Dict]]:
        """Generate 8-10 diverse concessions for a specific stadium"""
        
        # Randomly select 8-10 concession concepts for this stadium
        num_concessions = random.randint(8, 10)
        selected_concepts = random.sample(self.concession_concepts, min(num_concessions, len(self.concession_concepts)))
        
        concessions = []
        menu_items = []
        
        for concept in selected_concepts:
            # Create concession
            location_zone = random.choice(self.location_zones)
            opening_hours = random.choice(self.opening_hours)
            
            concession_data = {
                'stadium_id': stadium_id,
                'name': concept['name'],
                'category': concept['category'],
                'location_zone': location_zone,
                'opening_hours': opening_hours,
                'description': concept['description']
            }
            concessions.append(concession_data)
            
            # Select 10-15 menu items for this concession
            num_items = random.randint(10, 15)
            selected_items = random.sample(concept['menu_items'], min(num_items, len(concept['menu_items'])))
            
            for item_name, item_desc, min_price, max_price in selected_items:
                # Generate random price within range
                price = round(random.uniform(min_price, max_price), 2)
                
                menu_item_data = {
                    'concession_name': concept['name'],  # Temporary key for mapping
                    'name': item_name,
                    'description': item_desc,
                    'price': price,
                    'category': self._determine_item_category(item_name),
                    'is_available': True,
                    'is_vegetarian': True  # All items are vegetarian
                }
                menu_items.append(menu_item_data)
        
        return concessions, menu_items

    def _determine_item_category(self, item_name: str) -> str:
        """Determine the category of a menu item based on its name"""
        item_lower = item_name.lower()
        
        if any(word in item_lower for word in ['burger', 'sandwich', 'wrap', 'bowl', 'curry', 'pasta', 'pizza', 'biryani']):
            return 'Main Course'
        elif any(word in item_lower for word in ['salad', 'fries', 'chips', 'bread', 'rice']):
            return 'Side Dish'
        elif any(word in item_lower for word in ['coffee', 'tea', 'juice', 'water', 'smoothie', 'beer', 'soda']):
            return 'Beverage'
        elif any(word in item_lower for word in ['cake', 'ice cream', 'dessert', 'brownie', 'cookie', 'pudding']):
            return 'Dessert'
        elif any(word in item_lower for word in ['samosa', 'spring roll', 'nachos', 'dips']):
            return 'Appetizer'
        else:
            return 'Snack'

    def populate_all_stadiums(self):
        """Populate all stadiums with comprehensive concession data"""
        with app.app_context():
            try:
                stadiums = Stadium.query.all()
                total_concessions = 0
                total_menu_items = 0
                
                logger.info(f"🏟️ Found {len(stadiums)} stadiums to populate")
                
                for stadium in stadiums:
                    logger.info(f"🏏 Processing stadium: {stadium.name}")
                    
                    # Generate concessions and menu items for this stadium
                    concessions_data, menu_items_data = self.generate_concessions_for_stadium(
                        stadium.id, stadium.name
                    )
                    
                    # Create concession objects and track their IDs
                    concession_id_map = {}
                    
                    for concession_data in concessions_data:
                        concession = Concession(**concession_data)
                        db.session.add(concession)
                        db.session.flush()  # Get the ID
                        
                        concession_id_map[concession_data['name']] = concession.id
                        total_concessions += 1
                    
                    # Create menu item objects
                    for menu_item_data in menu_items_data:
                        concession_id = concession_id_map[menu_item_data['concession_name']]
                        
                        # Remove the temporary key
                        del menu_item_data['concession_name']
                        menu_item_data['concession_id'] = concession_id
                        
                        menu_item = MenuItem(**menu_item_data)
                        db.session.add(menu_item)
                        total_menu_items += 1
                    
                    db.session.commit()
                    logger.info(f"✅ Added {len(concessions_data)} concessions and {len(menu_items_data)} menu items for {stadium.name}")
                
                logger.info(f"🎉 Successfully created {total_concessions} concessions and {total_menu_items} menu items across {len(stadiums)} stadiums")
                return True, total_concessions, total_menu_items
                
            except Exception as e:
                logger.error(f"❌ Error populating stadiums: {e}")
                db.session.rollback()
                return False, 0, 0

    def run_complete_concession_update(self):
        """Execute complete concession data update process"""
        logger.info("🚀 Starting comprehensive Australian concession data update...")
        
        # Step 1: Clear existing data
        if not self.clear_existing_concessions():
            logger.error("❌ Failed to clear existing concession data")
            return False
        
        # Step 2: Populate all stadiums with new data
        success, concessions_count, items_count = self.populate_all_stadiums()
        
        if success:
            logger.info(f"✅ Concession data update completed successfully!")
            logger.info(f"📊 Summary: {concessions_count} concessions with {items_count} menu items")
            return True
        else:
            logger.error("❌ Concession data update failed")
            return False

def main():
    """Main function to run the concession data update"""
    generator = ComprehensiveAussieConcessionGenerator()
    return generator.run_complete_concession_update()

if __name__ == "__main__":
    main()