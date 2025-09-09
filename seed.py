
from app import app, db, Team, Stadium, Event, Player, Customer, StadiumOwner, Concession, MenuItem, Parking
from datetime import date, time
from sqlalchemy import text

def seed_data():
    with app.app_context():
        # Clear existing data (SQLite compatible)
        db.drop_all()
        db.create_all()

        # BBL Teams with Enhanced Information
        teams_data = [
            {
                "team_name": "Adelaide Strikers", 
                "home_ground": "Adelaide Oval", 
                "tagline": "Strike First, Strike Hard",
                "about": "The Adelaide Strikers are a professional Twenty20 franchise cricket team based in Adelaide, South Australia. Known for their aggressive batting and strategic gameplay.",
                "founding_year": 2011,
                "championships_won": 1,
                "team_color": "Blue and Gold",
                "color1": "#003d82",
                "color2": "#ffd100",
                "coach_name": "Jason Gillespie",
                "owner_name": "South Australian Cricket Association",
                "fun_fact": "First BBL team to win a championship after finishing last in the regular season.",
                "team_logo": "/static/img/teams/adelaide-strikers-logo.png",
                "home_city": "Adelaide",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Brisbane Heat", 
                "home_ground": "The Gabba", 
                "tagline": "Feel the Heat",
                "about": "The Brisbane Heat represents Queensland in the Big Bash League, known for their explosive batting lineup and passionate fanbase.",
                "founding_year": 2011,
                "championships_won": 1,
                "team_color": "Teal and Orange",
                "color1": "#e74c3c",
                "color2": "#f39c12",
                "coach_name": "Wade Seccombe",
                "owner_name": "Cricket Australia",
                "fun_fact": "First BBL team to score 200+ runs in a final.",
                "team_logo": "/static/img/teams/brisbane-heat-logo.png",
                "home_city": "Brisbane",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Hobart Hurricanes", 
                "home_ground": "Blundstone Arena", 
                "tagline": "Purple Rain",
                "about": "Tasmania's premier T20 team, the Hobart Hurricanes are known for their fighting spirit and strong bowling attack.",
                "founding_year": 2011,
                "championships_won": 0,
                "team_color": "Purple and Silver",
                "color1": "#9b59b6",
                "color2": "#3498db",
                "coach_name": "Jeff Vaughan",
                "owner_name": "Cricket Tasmania",
                "fun_fact": "Only BBL team representing Tasmania, creating a unique island fortress atmosphere.",
                "team_logo": "/static/img/teams/hobart-hurricanes-logo.png",
                "home_city": "Hobart",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Melbourne Renegades", 
                "home_ground": "Marvel Stadium", 
                "tagline": "Red Revolution",
                "about": "The Melbourne Renegades bring excitement to Marvel Stadium with their attacking cricket and innovative strategies.",
                "founding_year": 2011,
                "championships_won": 1,
                "team_color": "Red and Black",
                "color1": "#e74c3c",
                "color2": "#2c3e50",
                "coach_name": "David Saker",
                "owner_name": "Cricket Victoria",
                "fun_fact": "Play their home games in a domed stadium, creating unique playing conditions.",
                "team_logo": "/static/img/teams/melbourne-renegades-logo.png",
                "home_city": "Melbourne",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Melbourne Stars", 
                "home_ground": "Melbourne Cricket Ground", 
                "tagline": "Green Machine",
                "about": "Melbourne's premier cricket franchise, playing at the iconic MCG with a star-studded lineup of international players.",
                "founding_year": 2011,
                "championships_won": 0,
                "team_color": "Green and Gold",
                "color1": "#2ecc71",
                "color2": "#f1c40f",
                "coach_name": "Peter Moores",
                "owner_name": "Cricket Victoria",
                "fun_fact": "Most successful BBL team in regular season but yet to win a championship.",
                "team_logo": "/static/img/teams/melbourne-stars-logo.png",
                "home_city": "Melbourne",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Perth Scorchers", 
                "home_ground": "Perth Stadium", 
                "tagline": "Scorch the Earth",
                "about": "The most successful BBL franchise with multiple championships, known for their consistent performance and strong team culture.",
                "founding_year": 2011,
                "championships_won": 4,
                "team_color": "Orange and Black",
                "color1": "#e67e22",
                "color2": "#2c3e50",
                "coach_name": "Adam Voges",
                "owner_name": "Western Australian Cricket Association",
                "fun_fact": "Most successful BBL team with 4 championships and consistent finals appearances.",
                "team_logo": "/static/img/teams/perth-scorchers-logo.png",
                "home_city": "Perth",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Sydney Sixers", 
                "home_ground": "Sydney Cricket Ground", 
                "tagline": "Magenta Army",
                "about": "Based at the historic SCG, the Sydney Sixers are known for their tactical brilliance and championship-winning mentality.",
                "founding_year": 2011,
                "championships_won": 3,
                "team_color": "Magenta and Black",
                "color1": "#e91e63",
                "color2": "#9c27b0",
                "coach_name": "Greg Shipperd",
                "owner_name": "Cricket NSW",
                "fun_fact": "Second most successful BBL team with 3 championships including back-to-back titles.",
                "team_logo": "/static/img/teams/sydney-sixers-logo.png",
                "home_city": "Sydney",
                "team_type": "T20 Franchise"
            },
            {
                "team_name": "Sydney Thunder", 
                "home_ground": "Sydney Showground Stadium", 
                "tagline": "Thunder Nation",
                "about": "Sydney's second BBL franchise, known for their entertainment value and strong community connection in Western Sydney.",
                "founding_year": 2011,
                "championships_won": 1,
                "team_color": "Lime Green and Purple",
                "color1": "#9b59b6",
                "color2": "#f1c40f",
                "coach_name": "Shane Bond",
                "owner_name": "Cricket NSW",
                "fun_fact": "Known for their unique team song and strong connection to Western Sydney communities.",
                "team_logo": "/static/img/teams/sydney-thunder-logo.png",
                "home_city": "Sydney",
                "team_type": "T20 Franchise"
            }
        ]

        for team_info in teams_data:
            team = Team(**team_info)
            db.session.add(team)
        db.session.commit()

        # Enhanced Stadium Information
        stadiums_data = [
            {
                "name": "Adelaide Oval", 
                "location": "Adelaide, South Australia", 
                "capacity": 53583,
                "contact_number": "+61 8 8300 3800",
                "opening_year": 1871,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 140,
                "floodlight_quality": "Excellent",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "One of the world's most picturesque cricket grounds, Adelaide Oval combines historic charm with modern facilities.",
                "image_url": "/static/img/stadiums/adelaide-oval.jpg",
                "latitude": -34.9155,
                "longitude": 138.5956
            },
            {
                "name": "The Gabba", 
                "location": "Brisbane, Queensland", 
                "capacity": 42000,
                "contact_number": "+61 7 3896 4000",
                "opening_year": 1895,
                "pitch_type": "Traditional Turf",
                "boundary_length": 156,
                "floodlight_quality": "Excellent",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "Brisbane's fortress, known for its challenging conditions and passionate Queensland cricket supporters.",
                "image_url": "/static/img/stadiums/the-gabba.jpg",
                "latitude": -27.4856,
                "longitude": 153.0378
            },
            {
                "name": "Blundstone Arena", 
                "location": "Hobart, Tasmania", 
                "capacity": 20000,
                "contact_number": "+61 3 6282 0400",
                "opening_year": 1989,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 145,
                "floodlight_quality": "Very Good",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "Tasmania's premier cricket venue, offering spectacular views of Mount Wellington and the Derwent River.",
                "image_url": "/static/img/stadiums/blundstone-arena.jpg",
                "latitude": -42.8607,
                "longitude": 147.2802
            },
            {
                "name": "Marvel Stadium", 
                "location": "Melbourne, Victoria", 
                "capacity": 56347,
                "contact_number": "+61 3 8625 7700",
                "opening_year": 2000,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 152,
                "floodlight_quality": "Excellent",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "Melbourne's only fully enclosed stadium, providing weather protection and unique acoustic atmosphere for cricket.",
                "image_url": "/static/img/stadiums/marvel-stadium.jpg",
                "latitude": -37.8164,
                "longitude": 144.9470
            },
            {
                "name": "Melbourne Cricket Ground", 
                "location": "Melbourne, Victoria", 
                "capacity": 100024,
                "contact_number": "+61 3 9657 8888",
                "opening_year": 1854,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 160,
                "floodlight_quality": "World Class",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "The world's largest cricket stadium and home of Australian cricket, steeped in over 160 years of sporting history.",
                "image_url": "/static/img/stadiums/mcg.jpg",
                "latitude": -37.8200,
                "longitude": 144.9834
            },
            {
                "name": "Perth Stadium", 
                "location": "Perth, Western Australia", 
                "capacity": 61266,
                "contact_number": "+61 8 6101 1200",
                "opening_year": 2018,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 148,
                "floodlight_quality": "World Class",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "Australia's newest major cricket venue, featuring state-of-the-art facilities and stunning architecture.",
                "image_url": "/static/img/stadiums/perth-stadium.jpg",
                "latitude": -31.9505,
                "longitude": 115.8605
            },
            {
                "name": "Sydney Cricket Ground", 
                "location": "Sydney, New South Wales", 
                "capacity": 48601,
                "contact_number": "+61 2 9360 6601",
                "opening_year": 1848,
                "pitch_type": "Traditional Turf",
                "boundary_length": 155,
                "floodlight_quality": "Excellent",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "Australia's most historic cricket ground, known for its Members' and Ladies' pavilions and rich sporting heritage.",
                "image_url": "/static/img/stadiums/scg.jpg",
                "latitude": -33.8915,
                "longitude": 151.2247
            },
            {
                "name": "Sydney Showground Stadium", 
                "location": "Sydney, New South Wales", 
                "capacity": 21500,
                "contact_number": "+61 2 9704 1111",
                "opening_year": 2012,
                "pitch_type": "Drop-in Pitch",
                "boundary_length": 140,
                "floodlight_quality": "Very Good",
                "has_dressing_rooms": True,
                "has_practice_nets": True,
                "description": "A modern, intimate venue perfect for T20 cricket, located in Sydney's west with excellent transport links.",
                "image_url": "/static/img/stadiums/sydney-showground.jpg",
                "latitude": -33.7969,
                "longitude": 150.9681
            }
        ]

        for stadium_info in stadiums_data:
            stadium = Stadium(**stadium_info)
            db.session.add(stadium)
        db.session.commit()

        # Sample Matches
        teams = Team.query.all()
        stadiums = Stadium.query.all()

        events_data = [
            {"event_name": "Adelaide Strikers vs Brisbane Heat", "event_date": date(2025, 12, 10), "start_time": time(19, 15), "home_team_id": teams[0].id, "away_team_id": teams[1].id, "stadium_id": stadiums[0].id},
            {"event_name": "Hobart Hurricanes vs Melbourne Renegades", "event_date": date(2025, 12, 11), "start_time": time(19, 15), "home_team_id": teams[2].id, "away_team_id": teams[3].id, "stadium_id": stadiums[2].id},
            {"event_name": "Melbourne Stars vs Perth Scorchers", "event_date": date(2025, 12, 12), "start_time": time(19, 15), "home_team_id": teams[4].id, "away_team_id": teams[5].id, "stadium_id": stadiums[4].id},
            {"event_name": "Sydney Sixers vs Sydney Thunder", "event_date": date(2025, 12, 13), "start_time": time(19, 15), "home_team_id": teams[6].id, "away_team_id": teams[7].id, "stadium_id": stadiums[6].id}
        ]

        for event_info in events_data:
            event = Event(**event_info)
            db.session.add(event)
        db.session.commit()

        # Users
        users_data = [
            {"name": "Admin User", "email": "admin@example.com", "phone": "1234567890", "password": "adminpassword", "role": "admin"},
            {"name": "Stadium Owner", "email": "owner@example.com", "phone": "0987654321", "password": "ownerpassword", "role": "stadium_owner"},
            {"name": "Test User", "email": "user@example.com", "phone": "1122334455", "password": "userpassword", "role": "customer"}
        ]

        for user_info in users_data:
            user = Customer(name=user_info['name'], email=user_info['email'], phone=user_info['phone'], role=user_info['role'])
            user.set_password(user_info['password'])
            db.session.add(user)
        db.session.commit()

        # Assign stadium to owner
        owner = Customer.query.filter_by(email='owner@example.com').first()
        stadium = Stadium.query.first()
        stadium_owner_assignment = StadiumOwner(owner_id=owner.id, stadium_id=stadium.id)
        db.session.add(stadium_owner_assignment)
        db.session.commit()

        # Enhanced Player Data with Cricket Statistics
        players_data = {
            "Adelaide Strikers": [
                {"name": "Travis Head", "age": 30, "batting_style": "Left-hand bat", "bowling_style": "Right-arm off-break", "player_role": "Batsman", "is_captain": True, "jersey_number": 7, "nationality": "Australia"},
                {"name": "Alex Carey", "age": 33, "batting_style": "Left-hand bat", "bowling_style": "Right-arm medium", "player_role": "Wicket-keeper", "is_wicket_keeper": True, "jersey_number": 15, "nationality": "Australia"},
                {"name": "Rashid Khan", "age": 26, "batting_style": "Right-hand bat", "bowling_style": "Right-arm leg-break googly", "player_role": "All-rounder", "jersey_number": 17, "nationality": "Afghanistan"}
            ],
            "Brisbane Heat": [
                {"name": "Chris Lynn", "age": 34, "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break", "player_role": "Batsman", "is_captain": True, "jersey_number": 10, "nationality": "Australia"},
                {"name": "Marnus Labuschagne", "age": 30, "batting_style": "Right-hand bat", "bowling_style": "Right-arm leg-break", "player_role": "Batsman", "jersey_number": 22, "nationality": "Australia"},
                {"name": "Spencer Johnson", "age": 28, "batting_style": "Left-hand bat", "bowling_style": "Left-arm fast", "player_role": "Bowler", "jersey_number": 25, "nationality": "Australia"}
            ],
            "Hobart Hurricanes": [
                {"name": "Matthew Wade", "age": 37, "batting_style": "Left-hand bat", "bowling_style": "Right-arm medium", "player_role": "Wicket-keeper", "is_wicket_keeper": True, "is_captain": True, "jersey_number": 45, "nationality": "Australia"},
                {"name": "D'Arcy Short", "age": 29, "batting_style": "Left-hand bat", "bowling_style": "Right-arm off-break", "player_role": "All-rounder", "jersey_number": 9, "nationality": "Australia"},
                {"name": "Riley Meredith", "age": 28, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast", "player_role": "Bowler", "jersey_number": 16, "nationality": "Australia"}
            ],
            "Melbourne Renegades": [
                {"name": "Aaron Finch", "age": 38, "batting_style": "Right-hand bat", "bowling_style": "Right-arm medium", "player_role": "Batsman", "is_captain": True, "jersey_number": 5, "nationality": "Australia"},
                {"name": "Shaun Marsh", "age": 41, "batting_style": "Left-hand bat", "bowling_style": "Right-arm off-break", "player_role": "Batsman", "jersey_number": 3, "nationality": "Australia"},
                {"name": "Kane Richardson", "age": 33, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast-medium", "player_role": "Bowler", "jersey_number": 4, "nationality": "Australia"}
            ],
            "Melbourne Stars": [
                {"name": "Glenn Maxwell", "age": 36, "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break", "player_role": "All-rounder", "is_captain": True, "jersey_number": 32, "nationality": "Australia"},
                {"name": "Marcus Stoinis", "age": 35, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast-medium", "player_role": "All-rounder", "jersey_number": 61, "nationality": "Australia"},
                {"name": "Adam Zampa", "age": 32, "batting_style": "Right-hand bat", "bowling_style": "Right-arm leg-break googly", "player_role": "Bowler", "jersey_number": 99, "nationality": "Australia"}
            ],
            "Perth Scorchers": [
                {"name": "Ashton Turner", "age": 32, "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break", "player_role": "Batsman", "is_captain": True, "jersey_number": 13, "nationality": "Australia"},
                {"name": "Mitch Marsh", "age": 33, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast-medium", "player_role": "All-rounder", "jersey_number": 1, "nationality": "Australia"},
                {"name": "Jason Behrendorff", "age": 34, "batting_style": "Left-hand bat", "bowling_style": "Left-arm fast-medium", "player_role": "Bowler", "jersey_number": 5, "nationality": "Australia"}
            ],
            "Sydney Sixers": [
                {"name": "Moises Henriques", "age": 38, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast-medium", "player_role": "All-rounder", "is_captain": True, "jersey_number": 4, "nationality": "Australia"},
                {"name": "Josh Philippe", "age": 27, "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break", "player_role": "Wicket-keeper", "is_wicket_keeper": True, "jersey_number": 39, "nationality": "Australia"},
                {"name": "Sean Abbott", "age": 32, "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast-medium", "player_role": "All-rounder", "jersey_number": 72, "nationality": "Australia"}
            ],
            "Sydney Thunder": [
                {"name": "Chris Green", "age": 31, "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break", "player_role": "All-rounder", "is_captain": True, "jersey_number": 55, "nationality": "Australia"},
                {"name": "Alex Hales", "age": 35, "batting_style": "Right-hand bat", "bowling_style": "Right-arm medium", "player_role": "Batsman", "jersey_number": 8, "nationality": "England"},
                {"name": "Daniel Sams", "age": 32, "batting_style": "Left-hand bat", "bowling_style": "Left-arm fast-medium", "player_role": "All-rounder", "jersey_number": 20, "nationality": "Australia"}
            ]
        }

        for team_name, player_list in players_data.items():
            team = Team.query.filter_by(team_name=team_name).first()
            for player_data in player_list:
                player = Player(
                    player_name=player_data['name'],
                    team_id=team.id,
                    age=player_data.get('age'),
                    batting_style=player_data.get('batting_style'),
                    bowling_style=player_data.get('bowling_style'),
                    player_role=player_data.get('player_role'),
                    is_captain=player_data.get('is_captain', False),
                    is_wicket_keeper=player_data.get('is_wicket_keeper', False),
                    nationality=player_data.get('nationality'),
                    jersey_number=player_data.get('jersey_number')
                )
                db.session.add(player)
        db.session.commit()

        # Concessions and Menu Items
        for stadium in Stadium.query.all():
            concession = Concession(name=f"{stadium.name} Food Court", category="Food", stadium_id=stadium.id)
            db.session.add(concession)
            db.session.commit()

            # Comprehensive Vegetarian Menu with Dietary Information
            menu_items_data = [
                # Main Vegetarian Dishes
                {"name": "Gourmet Veggie Burger", "description": "Plant-based patty with avocado, tomato, lettuce, and vegan aioli on artisan bun. Contains gluten.", "price": 18.50, "category": "Main", "is_vegetarian": True, "is_available": True},
                {"name": "Margherita Pizza (Personal)", "description": "Wood-fired pizza with fresh mozzarella, basil, and organic tomato sauce. Contains dairy and gluten.", "price": 16.00, "category": "Main", "is_vegetarian": True, "is_available": True},
                {"name": "Paneer Tikka Wrap", "description": "Grilled cottage cheese with mint chutney, onions, and peppers in spinach tortilla. Contains dairy.", "price": 14.50, "category": "Main", "is_vegetarian": True, "is_available": True},
                {"name": "Buddha Bowl", "description": "Quinoa, roasted vegetables, chickpeas, hummus, and tahini dressing. Vegan and gluten-free.", "price": 17.00, "category": "Main", "is_vegetarian": True, "is_available": True},
                
                # Snacks and Appetizers
                {"name": "Vegetable Samosas (3 pieces)", "description": "Crispy pastry parcels filled with spiced potato and peas. Vegan. Contains gluten.", "price": 9.50, "category": "Snack", "is_vegetarian": True, "is_available": True},
                {"name": "Falafels with Hummus", "description": "House-made chickpea falafels served with creamy hummus and pita bread. Vegan.", "price": 12.00, "category": "Snack", "is_vegetarian": True, "is_available": True},
                {"name": "Loaded Nachos (Veggie)", "description": "Corn chips topped with cheese, jalapeños, guacamole, and sour cream. Contains dairy.", "price": 13.50, "category": "Snack", "is_vegetarian": True, "is_available": True},
                {"name": "Spring Rolls (4 pieces)", "description": "Fresh vegetables wrapped in rice paper with sweet chili dipping sauce. Vegan and gluten-free.", "price": 8.00, "category": "Snack", "is_vegetarian": True, "is_available": True},
                
                # Sides
                {"name": "Sweet Potato Fries", "description": "Crispy sweet potato wedges with rosemary seasoning. Vegan and gluten-free.", "price": 9.00, "category": "Side", "is_vegetarian": True, "is_available": True},
                {"name": "Garden Salad", "description": "Mixed greens, cherry tomatoes, cucumber, and balsamic vinaigrette. Vegan and gluten-free.", "price": 8.50, "category": "Side", "is_vegetarian": True, "is_available": True},
                {"name": "Garlic Bread", "description": "Toasted sourdough with herb butter. Contains dairy and gluten.", "price": 6.50, "category": "Side", "is_vegetarian": True, "is_available": True},
                {"name": "Onion Rings", "description": "Beer-battered onion rings with aioli dip. Contains gluten.", "price": 8.00, "category": "Side", "is_vegetarian": True, "is_available": True},
                
                # Beverages
                {"name": "Fresh Orange Juice", "description": "Freshly squeezed Valencia oranges. Vegan and gluten-free.", "price": 6.00, "category": "Drink", "is_vegetarian": True, "is_available": True},
                {"name": "Coconut Water", "description": "Pure coconut water from young coconuts. Vegan and gluten-free.", "price": 5.50, "category": "Drink", "is_vegetarian": True, "is_available": True},
                {"name": "Kombucha (Ginger & Turmeric)", "description": "Fermented tea with probiotics and natural flavors. Vegan and gluten-free.", "price": 7.00, "category": "Drink", "is_vegetarian": True, "is_available": True},
                {"name": "Premium Coffee", "description": "Single-origin arabica coffee. Available with oat milk. Can be vegan.", "price": 4.50, "category": "Drink", "is_vegetarian": True, "is_available": True},
                {"name": "Craft Soda (Various)", "description": "Artisanal sodas including elderflower, ginger beer, and cola. Vegan.", "price": 5.00, "category": "Drink", "is_vegetarian": True, "is_available": True},
                
                # Desserts
                {"name": "Vegan Chocolate Brownie", "description": "Rich chocolate brownie made without dairy or eggs. Vegan. Contains gluten.", "price": 8.00, "category": "Dessert", "is_vegetarian": True, "is_available": True},
                {"name": "Seasonal Fruit Bowl", "description": "Fresh seasonal fruits with mint and lime. Vegan and gluten-free.", "price": 7.50, "category": "Dessert", "is_vegetarian": True, "is_available": True}
            ]

            for item_data in menu_items_data:
                menu_item = MenuItem(**item_data, concession_id=concession.id)
                db.session.add(menu_item)
            db.session.commit()

        # Parking
        for stadium in Stadium.query.all():
            parking = Parking(zone=f"{stadium.name} General Parking", capacity=500, rate_per_hour=10.0, stadium_id=stadium.id)
            db.session.add(parking)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    print("Starting database seeding...")
    try:
        with app.app_context():
            seed_data()
            print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
