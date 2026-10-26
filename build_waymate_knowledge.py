"""
Script to build and update the WayMate knowledge base directly from waymate-client repository.
Extracts trip details, vehicles & maintenance rules, navigation & GPS features,
app settings, authentication workflows, translations, and guides into structured knowledge.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any

WAYMATE_CLIENT_DIR = Path(__file__).resolve().parent.parent / "waymate-client"
OUTPUT_FILE = Path(__file__).resolve().parent / "scraped_website.json"
OUTPUT_BACKUP = Path(__file__).resolve().parent / "waymate_knowledge.json"

def generate_waymate_knowledge() -> List[Dict[str, Any]]:
    knowledge_entries: List[Dict[str, Any]] = []

    # 1. Main Application Overview
    knowledge_entries.append({
        "url": "waymate://about",
        "title": "About WayMate - Adventure Passion Hub",
        "content": (
            "WayMate (Cộng đồng Đam mê Phượt) is the ultimate adventure travel, motorcycle, and road trip assistant app. "
            "It combines real-time trip planning, GPS routes & Google Maps preview, vehicle garage & maintenance tracking "
            "(engine oil replacements and service history for bikes and cars), rider telemetry (distance, avg speed, max velocity, "
            "elevation profile), pit stops & lodging management, rider community feeds, verified rider badges, and dual-language "
            "support (English and Vietnamese) with Dark/Light theme modes and Metric/Imperial units."
        ),
        "metadata": {
            "type": "guide",
            "category": "overview",
            "tags": ["about", "overview", "waymate", "features", "introduction"]
        }
    })

    # 2. Ha Giang Extreme Northern Loop Trip
    knowledge_entries.append({
        "url": "waymate://trips/trip-1",
        "title": "Trip: Ha Giang Extreme Northern Loop (Vòng Cung Hà Giang)",
        "content": (
            "Trip ID: trip-1. Title: Ha Giang Extreme Northern Loop (Cung đường phượt đỉnh cao Vòng cung Hà Giang). "
            "Rider: Minh 'Apex' Nguyen (Badge: Ha Giang Master / Bậc thầy Hà Giang). "
            "Bike Model: Adventure Tourer 1200. Distance: 350 km. Average Velocity: 48 km/h. Max Velocity: 82 km/h. "
            "Group Size: 4 / 6 Riders. Duration: 3 Days, 2 Nights (3 Ngày, 2 Đêm). Dates: Nov 12 - Nov 14, 2026. "
            "Category: Nearby Vietnam. Likes: 142. Comments: 28. "
            "Total Estimated Cost: 4,200,000 VND ($170 USD). "
            "Description: Epic mountain pass ride conquering Ma Pi Leng Pass, Tu San Canyon, and the dramatic winding limestone passes of Northern Vietnam. "
            "Hành trình chinh phục Đèo Mã Pí Lèng hùng vĩ, hẻm Tu Sản và những cung đèo ngoạn mục tại địa đầu Tổ quốc. "
            "Destination: Ma Pi Leng Pass, Ha Giang (Đèo Mã Pí Lèng, Pải Lủng, Mèo Vạc, Hà Giang, Vietnam). "
            "Coordinates: Latitude 23.2386, Longitude 105.4194. Google Maps URL: https://maps.app.goo.gl/MaPiLengPass. "
            "Planned Pit Stops (Eat & Drink): "
            "1. Pho Cu Thanh - Dong Van (Local Breakfast, Rating: 4.9 ⭐, Cost: 50,000 VND / $2). "
            "2. Ma Pi Leng Sunset Coffee (Viewpoint Rest, Rating: 4.8 ⭐, Cost: 40,000 VND / $1.5). "
            "Destinations & Landmarks: "
            "1. Ma Pi Leng Pass Skywalk (Stop: 1.5 hrs, Fee: Free). "
            "2. Lung Cu Flag Tower Landmark (Stop: 2 hrs, Fee: 20,000 VND). "
            "Stays & Hotel Lodging: "
            "1. Dong Van Cliffside Homestay (Price: 450,000 VND/night, Status: Booked). "
            "2. Du Gia Waterfall Ecolodge (Price: 380,000 VND/night, Status: Reserved)."
        ),
        "metadata": {
            "type": "trip",
            "category": "trips",
            "tags": ["ha giang", "trip-1", "ma pi lung", "dong van", "northern vietnam", "adventure tourer"]
        }
    })

    # 3. Pacific Coast Highway 1 Cruising Trip
    knowledge_entries.append({
        "url": "waymate://trips/trip-2",
        "title": "Trip: Pacific Coast Highway 1 Cruising (Cao tốc Thái Bình Dương)",
        "content": (
            "Trip ID: trip-2. Title: Pacific Coast Highway 1 Cruising (Lướt gió ven biển Cao tốc Thái Bình Dương Highway 1). "
            "Rider: Sarah Jenkins (Badge: Coast Rider / Tay lái Ven Biển). "
            "Bike Model: Triumph Tiger 900 GT. Distance: 720 km. Average Velocity: 75 km/h. Max Velocity: 110 km/h. "
            "Group Size: 2 / 4 Riders. Duration: 4 Days (4 Ngày). Dates: Dec 01 - Dec 04, 2026. "
            "Category: International Global Tours. Likes: 289. Comments: 41. "
            "Total Estimated Cost: 14,500,000 VND ($580 USD). "
            "Description: Ocean breeze and cliffs along Bixby Creek Bridge, Big Sur, and coastal highway sunset runs. "
            "Gió biển lộng và vách đá hùng vĩ qua Cầu Bixby Creek, Big Sur và hoàng hôn rực rỡ bên bờ đại dương. "
            "Destination: Bixby Creek Bridge, Big Sur (Highway 1, Monterey County, California, USA). "
            "Coordinates: Latitude 36.3714, Longitude -121.9018. "
            "Planned Pit Stops (Eat & Drink): "
            "1. Nepenthe Coastal Grill (Seafood Lunch, Rating: 4.7 ⭐, Cost: $45 USD). "
            "2. Big Sur Bakery (Coffee & Pastry, Rating: 4.9 ⭐, Cost: $12 USD). "
            "Destinations & Landmarks: "
            "1. Bixby Creek Bridge Overlook (Stop: 45 mins, Fee: Free). "
            "2. McWay Falls Cove (Stop: 1 hr, Fee: $10 Parking). "
            "Stays & Hotel Lodging: "
            "1. Glen Oaks Big Sur Cabins (Price: $180 USD/night, Status: Available)."
        ),
        "metadata": {
            "type": "trip",
            "category": "trips",
            "tags": ["pacific coast", "highway 1", "california", "big sur", "triumph", "international"]
        }
    })

    # 4. Saigon to Da Lat Highland Pine Ride Trip
    knowledge_entries.append({
        "url": "waymate://trips/trip-3",
        "title": "Trip: Saigon to Da Lat Highland Pine Ride (Sài Gòn - Đà Lạt)",
        "content": (
            "Trip ID: trip-3. Title: Saigon to Da Lat Highland Pine Ride (Phượt Sài Gòn - Đà Lạt Thành Phố Ngàn Hoa). "
            "Rider: Hoang Lam (Badge: Highland Explorer / Thám hiểm Cao nguyên). "
            "Bike Model: Superbike 1000 RR. Distance: 310 km. Average Velocity: 55 km/h. Max Velocity: 90 km/h. "
            "Group Size: 5 / 8 Riders. Duration: 2 Days, 1 Night (2 Ngày, 1 Đêm). Dates: Nov 20 - Nov 21, 2026. "
            "Category: Nearby Vietnam. Likes: 312. Comments: 56. "
            "Total Estimated Cost: 2,500,000 VND ($100 USD). "
            "Description: Crisp pine forest breezes, winding Prenn Pass switchbacks, and sunset over Tuyen Lam Lake in Da Lat. "
            "Uốn lượn qua Đèo Prenn, xuyên qua rừng thông ngát hương và ngắm hoàng hôn bên Hồ Tuyền Lâm, Đà Lạt. "
            "Destination: Da Lat City, Lam Dong (Đà Lạt, Lâm Đồng, Vietnam). "
            "Coordinates: Latitude 11.9404, Longitude 108.4583. Google Maps URL: https://maps.app.goo.gl/DaLatCityVietnam. "
            "Planned Pit Stops (Eat & Drink): "
            "1. Banh Can Le - Da Lat (Local Breakfast, Rating: 4.9 ⭐, Cost: 40,000 VND). "
            "2. Tui Mo To Cafe (Viewpoint Rest, Rating: 4.8 ⭐, Cost: 60,000 VND). "
            "Destinations & Landmarks: "
            "1. Tuyen Lam Lake & Pine Hill (Stop: 2 hrs, Fee: Free). "
            "2. Lang Biang Peak Summit (Stop: 3 hrs, Fee: 50,000 VND). "
            "Stays & Hotel Lodging: "
            "1. Pine Valley Eco Homestay (Price: 450,000 VND/night, Status: Booked)."
        ),
        "metadata": {
            "type": "trip",
            "category": "trips",
            "tags": ["da lat", "saigon", "prenn pass", "lam dong", "superbike 1000 rr", "nearby"]
        }
    })

    # 5. Vehicles & Maintenance Garage Tracker
    knowledge_entries.append({
        "url": "waymate://garage",
        "title": "My Vehicles & Maintenance Tracker Guide",
        "content": (
            "WayMate Garage allows riders and drivers to manage motorcycles and cars, monitor odometer (ODO km), "
            "and track essential maintenance schedules. "
            "Default Maintenance Intervals: "
            "- Motorcycles: Engine oil replacement recommended every 3,000 km (or 6 months). "
            "- Cars: Engine oil replacement recommended every 5,000 km (or 6 months) for synthetic oils. "
            "Oil Status Calculation: "
            "- Next Oil Due ODO = Last Oil ODO + Oil Interval Km. "
            "- Remaining Km = Next Oil Due ODO - Current ODO. "
            "- Status is 'Good' when remaining km > 500 km. "
            "- Status is 'Due Soon' when remaining km <= 500 km or overdue. "
            "Service History Tracking: Users can log oil changes and service records including Service Type "
            "(e.g., Motul 300V Factory Line 10W-40, Brembo Brake Pads, Valve Check, Tires), Service Date, ODO at service, "
            "Cost in VND, and Service Notes/Location."
        ),
        "metadata": {
            "type": "vehicle",
            "category": "garage",
            "tags": ["garage", "maintenance", "oil change", "odo", "service history", "vehicles"]
        }
    })

    # 6. Registered Vehicle: Superbike 1000 RR
    knowledge_entries.append({
        "url": "waymate://vehicles/veh-1",
        "title": "Vehicle: Superbike 1000 RR (Sport Performance)",
        "content": (
            "Vehicle ID: veh-1. Model: Superbike 1000 RR. Brand: Sport Performance. Type: Motorcycle (bike). "
            "Plate Number: 59-A1 999.54. Current ODO: 8,420 km. Year: 2024. "
            "Last Oil Change: Date 2026-09-15 at 6,500 km. Oil Interval: 3,000 km. Next Oil Due: 9,500 km (1,080 km remaining, Status: Good). "
            "Service History: "
            "1. Motul 300V Factory Line 10W-40 & Racing Filter (2026-09-15, ODO: 6,500 km, Cost: 1,650,000 VND, Notes: Full synthetic ester core race oil & performance filter). "
            "2. Front & Rear Brembo Brake Pads (2026-05-15, ODO: 10,500 km, Cost: 2,800,000 VND, Notes: Sintered pads for mountain pass braking). "
            "3. 10,000 KM Major Valve Check & Fluid Flush (2026-04-20, ODO: 10,000 km, Cost: 4,500,000 VND, Notes: Authorized Service Center, brake fluid & final drive oil flushed)."
        ),
        "metadata": {
            "type": "vehicle",
            "category": "garage",
            "tags": ["superbike 1000 rr", "motul 300v", "brembo", "motorcycle", "sport"]
        }
    })

    # 7. Registered Vehicle: Honda CB500X
    knowledge_entries.append({
        "url": "waymate://vehicles/veh-2",
        "title": "Vehicle: Honda CB500X",
        "content": (
            "Vehicle ID: veh-2. Model: Honda CB500X. Brand: Honda. Type: Motorcycle (bike). "
            "Plate Number: 29-A1 369.58. Current ODO: 28,900 km. Year: 2022. "
            "Last Oil Change: Date 2026-07-02 at 26,000 km. Oil Interval: 3,000 km. Next Oil Due: 29,000 km (100 km remaining, Status: Due Soon ⚠️). "
            "Service History: "
            "1. Castrol Power1 Racing Oil & Chain Maintenance (2026-07-02, ODO: 26,000 km, Cost: 650,000 VND, Notes: DID 520 chain cleaned and lubricated with Motorex spray). "
            "2. Pirelli Scorpion Trail II Tire Set (2026-02-18, ODO: 22,000 km, Cost: 6,200,000 VND, Notes: Dual sport touring tires mounted & balanced)."
        ),
        "metadata": {
            "type": "vehicle",
            "category": "garage",
            "tags": ["honda cb500x", "adventure", "honda", "castrol", "pirelli", "due soon"]
        }
    })

    # 8. Registered Vehicle: Ford Ranger Raptor 4x4
    knowledge_entries.append({
        "url": "waymate://vehicles/veh-3",
        "title": "Vehicle: Ford Ranger Raptor 4x4",
        "content": (
            "Vehicle ID: veh-3. Model: Ford Ranger Raptor 4x4. Brand: Ford. Type: Car / Support Truck. "
            "Plate Number: 51D-924.12. Current ODO: 41,200 km. Year: 2024. "
            "Last Oil Change: Date 2026-06-25 at 38,000 km. Oil Interval: 5,000 km. Next Oil Due: 43,000 km (1,800 km remaining, Status: Good). "
            "Service History: "
            "1. Synthetic Diesel Oil & Fuel Filter (2026-06-25, ODO: 38,000 km, Cost: 2,600,000 VND, Notes: Full service inspection prior to road trip support vehicle duties)."
        ),
        "metadata": {
            "type": "vehicle",
            "category": "garage",
            "tags": ["ford ranger raptor", "car", "support vehicle", "diesel oil"]
        }
    })

    # 9. Google Maps & Navigation Features
    knowledge_entries.append({
        "url": "waymate://navigation",
        "title": "WayMate Google Maps Integration & GPX Route Export",
        "content": (
            "WayMate offers deep Google Maps navigation and route visualization: "
            "- Preview Trip on Google Maps: Automatically opens the exact pinned destination or custom map link in Google Maps on both mobile (Android/iOS) and web. "
            "- GPS Coordinates Pinning: Users can pin exact latitude and longitude coordinates for any mountain pass, campsite, viewpoint, or landmark. "
            "- Quick Popular Pins: Instant coordinates for popular spots like Ma Pi Leng Pass (23.2386, 105.4194), Da Lat City (11.9404, 108.4583), Bixby Creek Bridge (36.3714, -121.9018). "
            "- Custom Map Links: Users can paste Google Maps shortened links (e.g., https://maps.app.goo.gl/...) directly when posting trips. "
            "- GPX Route Export: Export GPS route data for motorcycle GPS devices (Garmin, BMW Motorrad Navigator, Quad Lock)."
        ),
        "metadata": {
            "type": "guide",
            "category": "navigation",
            "tags": ["google maps", "gpx", "gps", "coordinates", "navigation", "routes"]
        }
    })

    # 10. Rider Profile, Achievements & Badges
    knowledge_entries.append({
        "url": "waymate://profile",
        "title": "Rider Profile, Badges & Achievements",
        "content": (
            "WayMate Profile showcases rider identity, stats, and accomplishments: "
            "- Verified Rider Status & PRO Badge: Designates authentic and experienced road captains. "
            "- Badges & Milestones: "
            "  1. 'Iron Butt 1000km': Conquering 1,000+ km long-distance endurance rides. "
            "  2. 'Ha Giang Master' (Bậc thầy Hà Giang): Conquering the legendary northern loop. "
            "  3. 'Coast Rider' (Tay lái Ven Biển): Scenic coastal highway cruiser. "
            "  4. 'Highland Explorer' (Thám hiểm Cao nguyên): Conquering mountain passes and highlands. "
            "  5. 'Trailblazer': Leading group tours and discovering new trails. "
            "- Primary Ride & Helmet Comms Setup: Displays bike model and intercom gear (e.g. Cardo Packtalk, Sena 50S). "
            "- Saved Favorite Trips: Quick bookmarking of trips to access anytime."
        ),
        "metadata": {
            "type": "guide",
            "category": "profile",
            "tags": ["profile", "badges", "iron butt", "ha giang master", "gear", "comms"]
        }
    })

    # 11. Authentication, Google 1-Tap & Password Recovery
    knowledge_entries.append({
        "url": "waymate://auth",
        "title": "Authentication, Google Sign-in & Password Recovery",
        "content": (
            "WayMate provides secure and convenient authentication: "
            "- Log In: Username or Email with secure password authentication. "
            "- Google Sign-In: 1-Tap Google Sign-In issuing verified JWT tokens, compatible with Expo Go and web. Supports custom Google accounts. "
            "- Sign Up: Register with Full Name, Email, Password, and select Primary Travel Style: "
            "  1. Motorcycle (Xe máy / Mô tô phượt) "
            "  2. Road Trip (Xe hơi / Ô tô đường trường) "
            "  3. Backpack (Du lịch bụi / Balo) "
            "- Forgot Password (3-Step OTP Recovery): "
            "  Step 1: Enter registered email to receive a 6-digit OTP code (expires in 1 minute). "
            "  Step 2: Verify the 6-digit OTP code. "
            "  Step 3: Set and confirm new password (min 6 characters) with real-time password strength meter. "
            "- Change Password: Existing authenticated users can update credentials directly from Profile."
        ),
        "metadata": {
            "type": "guide",
            "category": "auth",
            "tags": ["login", "signup", "google signin", "otp", "password reset", "security"]
        }
    })

    # 12. App Settings: Themes, Languages, Units & Offline
    knowledge_entries.append({
        "url": "waymate://settings",
        "title": "WayMate App Settings: Theme, Language, and Telemetry Units",
        "content": (
            "WayMate settings accessible via the TopBar: "
            "- Theme Switching: Seamless toggle between Dark Mode (deep carbon black with electric cyan and red glow) and Light Mode (clean high-contrast daylight view for outdoor sunlight). "
            "- Dual Language Support: "
            "  • English (ENG): Full English interface and instructions. "
            "  • Vietnamese (VIE - Tiếng Việt): Giao diện tiếng Việt hoàn chỉnh cho cộng đồng phượt thủ Việt Nam. "
            "- Telemetry Units: "
            "  • Metric: KM and km/h for speed and distance. "
            "  • Imperial: Miles and mph. "
            "- Auto-Fill Demo: Instant populator for testing demo credentials and trip creation."
        ),
        "metadata": {
            "type": "guide",
            "category": "settings",
            "tags": ["theme", "dark mode", "light mode", "language", "english", "vietnamese", "units"]
        }
    })

    # 13. Safety Gear, Riding Etiquette & Packing Tips
    knowledge_entries.append({
        "url": "waymate://safety-gear",
        "title": "Rider Safety Gear & Packing Checklist",
        "content": (
            "Safety is the #1 priority at WayMate: "
            "- Essential Helmet: Full-face ECE 22.06 or DOT certified helmet. Modular helmets with pinlock anti-fog are ideal for rainy mountain passes. "
            "- Riding Jackets & Pants: Cordura/mesh jacket with CE Level 2 armor at back, shoulders, and elbows. "
            "- Motorcycle Gloves: Full-gauntlet or reinforced leather gloves with carbon knuckle sliders. "
            "- Riding Boots: Ankle-supporting waterproof boots with reinforced shanks. "
            "- Communication: Bluetooth intercoms (Cardo Mesh or Sena) for real-time rider group comms, road hazard warnings, and navigation prompts. "
            "- Tool & Emergency Kit: Compact 12V tire inflator, tubeless plug kit, chain lubricant (Motul/Motorex), zip ties, multi-tool, and emergency first-aid kit."
        ),
        "metadata": {
            "type": "guide",
            "category": "safety",
            "tags": ["safety", "gear", "helmet", "intercom", "gloves", "emergency kit", "maintenance"]
        }
    })

    # 14. Frequently Asked Questions (FAQ)
    knowledge_entries.append({
        "url": "waymate://faq",
        "title": "WayMate Frequently Asked Questions (FAQ)",
        "content": (
            "FAQ 1: How do I plan and post a new trip? "
            "Answer: In the Community Feed, tap 'Post New Trip' or the '+' icon. Enter the title, distance (km), duration, pinned GPS coordinates, optional Google Maps link, pit stops, and lodging. Tap 'PUBLISH TRIP'. "
            "FAQ 2: How does the oil change reminder work? "
            "Answer: In 'My Vehicles', check your vehicle card. When remaining km drops below 500 km, status turns 'Due Soon'. After servicing, tap 'Log Oil Change' to record the date and current ODO. "
            "FAQ 3: How do I open routes in Google Maps? "
            "Answer: On any trip detail screen, tap 'Preview Trip on Google Maps'. If a custom map link is provided, it opens directly; otherwise it navigates to the pinned GPS coordinates. "
            "FAQ 4: How do I join a group ride? "
            "Answer: On the trip detail screen, view the Group Size slot (e.g. '4 / 6 Riders') and tap 'Join Ride Slot'. The ride organizer will be notified! "
            "FAQ 5: How do I switch languages or units? "
            "Answer: Tap the language button (ENG / VIE) or the unit button (KM / Miles) in the top navigation bar at any time."
        ),
        "metadata": {
            "type": "faq",
            "category": "help",
            "tags": ["faq", "questions", "how to", "join ride", "post trip", "oil reminder", "google maps"]
        }
    })

    return knowledge_entries

def main():
    print("[WayMate] Building WayMate Knowledge Base...")
    entries = generate_waymate_knowledge()
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"[WayMate] Saved {len(entries)} knowledge entries to {OUTPUT_FILE}")

    with open(OUTPUT_BACKUP, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"[WayMate] Saved backup to {OUTPUT_BACKUP}")

if __name__ == "__main__":
    main()
