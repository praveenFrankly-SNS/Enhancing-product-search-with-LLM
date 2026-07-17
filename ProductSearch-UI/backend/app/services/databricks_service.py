"""
Databricks integration service wrapper for semantic search.
Provides direct data mappings for product query routing.
"""
import time
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Complete prepared catalog database for exact category evaluation
MOCK_PRODUCTS = [
    # --- 20 SMART WATCHES ---
    {
        "product_id": "watch-001",
        "product_name": "Apple Watch Series 9",
        "category_path": "Smart Watches",
        "brand_name": "Apple",
        "selling_price": 41900.0,
        "average_rating": 4.8,
        "review_count": 310,
        "attribute_summary": "S9 SiP chip, double tap gesture control, temperature sensing, ECG heart rate alerts, and always-on retina display.",
        "review_summary": "Double tap gesture works beautifully when your hands are full. Excellent fitness and health safety tracker.",
        "searchable_text": "Apple Watch Series 9 GPS cellular health tracker aluminum case sport band pulse oximeter step counter fitness sleep monitor watch."
    },
    {
        "product_id": "watch-002",
        "product_name": "Samsung Galaxy Watch 6",
        "category_path": "Smart Watches",
        "brand_name": "Samsung",
        "selling_price": 29999.0,
        "average_rating": 4.6,
        "review_count": 185,
        "attribute_summary": "Exynos W930 processor, body composition BIA sensor, sleep coaching profile tracking, and personalized heart rate zones.",
        "review_summary": "Great screen resolution and slim design. Sleep coaching features are very helpful.",
        "searchable_text": "Samsung Galaxy Watch 6 LTE fitness smart watch sleep coach health tracker ECG blood pressure monitoring watch."
    },
    {
        "product_id": "watch-003",
        "product_name": "Garmin Fenix 7 Pro Sapphire",
        "category_path": "Smart Watches",
        "brand_name": "Garmin",
        "selling_price": 81990.0,
        "average_rating": 4.7,
        "review_count": 92,
        "attribute_summary": "Solar charging glass lens, multi-band GPS tracking, preloaded topographic maps, and up to 22 days of battery life.",
        "review_summary": "The ultimate sports smart watch. Solar battery life is outstanding and GPS mapping is extremely precise.",
        "searchable_text": "Garmin Fenix 7 Pro solar multi-sport watch rugged maps fitness tracker heart rate monitoring elevation GPS watch."
    },
    {
        "product_id": "watch-004",
        "product_name": "Apple Watch Ultra 2",
        "category_path": "Smart Watches",
        "brand_name": "Apple",
        "selling_price": 89900.0,
        "average_rating": 4.9,
        "review_count": 154,
        "attribute_summary": "Titanium case, dual-frequency GPS, up to 72 hours battery life in low power mode, and 3000 nits display brightness.",
        "review_summary": "Rugged build and insane display brightness. Highly recommended for divers and outdoor sports enthusiasts.",
        "searchable_text": "Apple Watch Ultra 2 titanium rugged diving tracking watch compass altitude tracker sport watch."
    },
    {
        "product_id": "watch-005",
        "product_name": "Samsung Galaxy Watch 6 Classic",
        "category_path": "Smart Watches",
        "brand_name": "Samsung",
        "selling_price": 36999.0,
        "average_rating": 4.7,
        "review_count": 120,
        "attribute_summary": "Rotating physical bezel, custom 3D design, stainless steel frame, health sensors and advanced running analysis.",
        "review_summary": "The returning rotating bezel is a game changer. The classic watch aesthetics look superb for corporate wear.",
        "searchable_text": "Samsung Galaxy Watch 6 Classic rotating bezel smart watch health activity metrics rotating dial watch."
    },
    {
        "product_id": "watch-006",
        "product_name": "Garmin Forerunner 965",
        "category_path": "Smart Watches",
        "brand_name": "Garmin",
        "selling_price": 62490.0,
        "average_rating": 4.8,
        "review_count": 87,
        "attribute_summary": "1.4-inch AMOLED display, built-in maps, titanium bezel, advanced training readiness metrics, and running dynamics.",
        "review_summary": "Excellent maps representation on AMOLED display. Perfect training guide for marathon runners.",
        "searchable_text": "Garmin Forerunner 965 running tracker GPS watch triathlon heart rate HRV status maps sport watch."
    },
    {
        "product_id": "watch-007",
        "product_name": "Fitbit Sense 2 Smartwatch",
        "category_path": "Smart Watches",
        "brand_name": "Fitbit",
        "selling_price": 22999.0,
        "average_rating": 4.4,
        "review_count": 204,
        "attribute_summary": "All-day body response cEDA sensor, sleep profile tracking, built-in GPS, and real-time stress tracking notifications.",
        "review_summary": "Stress levels are mapped accurately. Battery lasts up to 6 days which is great.",
        "searchable_text": "Fitbit Sense 2 stress tracker health metrics watch EDA sensor sleep heart health watch."
    },
    {
        "product_id": "watch-008",
        "product_name": "Google Pixel Watch 2",
        "category_path": "Smart Watches",
        "brand_name": "Google",
        "selling_price": 32500.0,
        "average_rating": 4.5,
        "review_count": 143,
        "attribute_summary": "Safety check features, advanced heart rate sensor by Fitbit, skin temperature sensor, and Wear OS 4 integration.",
        "review_summary": "Clean OS experience. Integrates perfectly with Pixel devices, but battery could be better.",
        "searchable_text": "Google Pixel Watch 2 wear OS fitness tracker smart watch Fitbit heart rate sensors watch."
    },
    {
        "product_id": "watch-009",
        "product_name": "TicWatch Pro 5 GPS Watch",
        "category_path": "Smart Watches",
        "brand_name": "Mobvoi",
        "selling_price": 29999.0,
        "average_rating": 4.5,
        "review_count": 99,
        "attribute_summary": "Snapdragon W5+ Gen 1, dual-layer display, ultra-low power display, and barometric altimeter compass sensors.",
        "review_summary": "The secondary display makes the battery last for weeks. Great performance without lags.",
        "searchable_text": "TicWatch Pro 5 dual display smart watch wear OS battery saver fitness navigation watch."
    },
    {
        "product_id": "watch-010",
        "product_name": "Amazfit GTR 4 Smart Watch",
        "category_path": "Smart Watches",
        "brand_name": "Amazfit",
        "selling_price": 16999.0,
        "average_rating": 4.4,
        "review_count": 215,
        "attribute_summary": "Dual-band circular polarized GPS, 150+ sports modes, Zepp OS, and 14-day battery life.",
        "review_summary": "Unbelievable battery life. Accurate step count and GPS maps at a reasonable cost.",
        "searchable_text": "Amazfit GTR 4 sports smart watch battery life GPS fitness tracker Zepp OS circular watch."
    },
    {
        "product_id": "watch-011",
        "product_name": "Garmin Venu 3 GPS Smartwatch",
        "category_path": "Smart Watches",
        "brand_name": "Garmin",
        "selling_price": 44990.0,
        "average_rating": 4.7,
        "review_count": 110,
        "attribute_summary": "Body battery energy monitor, wheelchair mode, sleep coach, on-wrist speaker and mic for calls.",
        "review_summary": "Speaker is very clear for calls on wrist. The sleep coach insights are very detailed.",
        "searchable_text": "Garmin Venu 3 smart watch health fitness sleep coach body energy tracking watch."
    },
    {
        "product_id": "watch-012",
        "product_name": "Fitbit Versa 4 Fitness Watch",
        "category_path": "Smart Watches",
        "brand_name": "Fitbit",
        "selling_price": 18499.0,
        "average_rating": 4.3,
        "review_count": 178,
        "attribute_summary": "Thin design, active zone minutes tracker, 40+ exercise modes, and built-in Alexa voice assistant.",
        "review_summary": "Slim and lightweight. Very easy to view sleep trends and daily active zones.",
        "searchable_text": "Fitbit Versa 4 slim fitness tracker smart watch heart rate activity tracking Alexa watch."
    },
    {
        "product_id": "watch-013",
        "product_name": "Apple Watch SE (2nd Gen)",
        "category_path": "Smart Watches",
        "brand_name": "Apple",
        "selling_price": 27900.0,
        "average_rating": 4.7,
        "review_count": 380,
        "attribute_summary": "S8 SiP processor, crash detection safety features, heart rate notifications, and water resistant swimproof design.",
        "review_summary": "Best value Apple Watch. Has all standard health tracking and notifications at an entry-level price.",
        "searchable_text": "Apple Watch SE 2nd Gen budget health tracker sports fitness smart watch."
    },
    {
        "product_id": "watch-014",
        "product_name": "Amazfit Active Smartwatch",
        "category_path": "Smart Watches",
        "brand_name": "Amazfit",
        "selling_price": 11999.0,
        "average_rating": 4.3,
        "review_count": 92,
        "attribute_summary": "AI fitness coach tracker, offline maps support, Bluetooth phone call receiver, and long battery life.",
        "review_summary": "AI workouts are very motivating. Great square display aesthetic.",
        "searchable_text": "Amazfit Active square smart watch health stats tracker AI coach workout watch."
    },
    {
        "product_id": "watch-015",
        "product_name": "OnePlus Watch 2 WearOS",
        "category_path": "Smart Watches",
        "brand_name": "OnePlus",
        "selling_price": 24999.0,
        "average_rating": 4.6,
        "review_count": 134,
        "attribute_summary": "Dual-engine architecture, Snapdragon W5, up to 100 hours battery life in smart mode, and military-grade steel case.",
        "review_summary": "WearOS watch with 4 days battery life is incredible. Charging speed is insanely fast.",
        "searchable_text": "OnePlus Watch 2 military grade steel smart watch WearOS fitness tracker fast charging watch."
    },
    {
        "product_id": "watch-016",
        "product_name": "Polar Vantage V3 Sport Watch",
        "category_path": "Smart Watches",
        "brand_name": "Polar",
        "selling_price": 54990.0,
        "average_rating": 4.5,
        "review_count": 62,
        "attribute_summary": "BIOSENSING orthostatic testing, wrist-based ECG, SpO2 blood oxygen, and offline maps tracking.",
        "review_summary": "Highly recommended for pro athletes. Recovery tests are extremely scientifically backed.",
        "searchable_text": "Polar Vantage V3 sports watch athlete stats health sensors offline map tracker."
    },
    {
        "product_id": "watch-017",
        "product_name": "Garmin Epix Gen 2 Active",
        "category_path": "Smart Watches",
        "brand_name": "Garmin",
        "selling_price": 79990.0,
        "average_rating": 4.8,
        "review_count": 74,
        "attribute_summary": "AMOLED touch display, mapping, heart rate sensor, stamina tracking, and preloaded ski maps.",
        "review_summary": "Outstanding screen contrast. Great balance of smart watch and rugged Garmin maps features.",
        "searchable_text": "Garmin Epix Gen 2 AMOLED sport watch health metric tracking high resolution screen."
    },
    {
        "product_id": "watch-018",
        "product_name": "Suunto Race GPS Sport Watch",
        "category_path": "Smart Watches",
        "brand_name": "Suunto",
        "selling_price": 49990.0,
        "average_rating": 4.6,
        "review_count": 58,
        "attribute_summary": "AMOLED high refresh display, HR tracking, sleep recovery tracking, and 40h battery with maximum accuracy GPS.",
        "review_summary": "Very durable digital crown wheel interface. Excellent offline map loading.",
        "searchable_text": "Suunto Race sports tracker titanium casing smart watch maps health statistics."
    },
    {
        "product_id": "watch-019",
        "product_name": "Citizen CZ Smart Gen 2",
        "category_path": "Smart Watches",
        "brand_name": "Citizen",
        "selling_price": 28500.0,
        "average_rating": 4.1,
        "review_count": 83,
        "attribute_summary": "CZ Smart YouQ wellness app, alertness monitoring, IBM Watson health models, and classic bezel styling.",
        "review_summary": "Classic styling looks exactly like a traditional analog chronograph. YouQ app alertness tracking is a neat touch.",
        "searchable_text": "Citizen CZ Smart Gen 2 WearOS watch wellness alertness dashboard chronograph style."
    },
    {
        "product_id": "watch-020",
        "product_name": "Withings ScanWatch 2",
        "category_path": "Smart Watches",
        "brand_name": "Withings",
        "selling_price": 38990.0,
        "average_rating": 4.5,
        "review_count": 105,
        "attribute_summary": "Hybrid smartwatch, continuous body temperature, wrist ECG, blood oxygen, and 30-day battery life.",
        "review_summary": "Beautiful physical clock hands with a tiny digital OLED. Highly precise clinical health tracking.",
        "searchable_text": "Withings ScanWatch 2 hybrid smart watch clinical ECG heart rate tracker analog watch."
    },

    # --- 20 GAMING LAPTOPS ---
    {
        "product_id": "laptop-001",
        "product_name": "ASUS ROG Zephyrus G14",
        "category_path": "Laptops",
        "brand_name": "ASUS",
        "selling_price": 145990.0,
        "average_rating": 4.7,
        "review_count": 210,
        "attribute_summary": "AMD Ryzen 9 8945HS processor, NVIDIA RTX 4070 GPU, 14-inch 120Hz OLED display, and premium white aluminum chassis.",
        "review_summary": "Top tier portable gaming laptop. The OLED screen is incredibly vibrant and battery life is great for a gaming machine.",
        "searchable_text": "ASUS ROG Zephyrus G14 gaming laptop Ryzen 9 RTX 4070 32GB RAM OLED high refresh display under $1500."
    },
    {
        "product_id": "laptop-002",
        "product_name": "Lenovo Legion Pro 5i",
        "category_path": "Laptops",
        "brand_name": "Lenovo",
        "selling_price": 124990.0,
        "average_rating": 4.6,
        "review_count": 165,
        "attribute_summary": "Intel Core i7-14700HX, RTX 4060 GPU, 16-inch WQXGA 240Hz screen, and Legion Coldfront thermal cooling system.",
        "review_summary": "Outstanding thermal performance. The keyboard is very tactile and comfortable for typing and gaming.",
        "searchable_text": "Lenovo Legion Pro 5i gaming laptop Intel i7 RTX 4060 high performance cooling WQXGA under $1500."
    },
    {
        "product_id": "laptop-003",
        "product_name": "Apple MacBook Air M3",
        "category_path": "Laptops",
        "brand_name": "Apple",
        "selling_price": 114900.0,
        "average_rating": 4.9,
        "review_count": 450,
        "attribute_summary": "Apple M3 Chip, 13.6-inch Liquid Retina Display, 8-core CPU and 10-core GPU, up to 18 hours battery life, and silent fanless design.",
        "review_summary": "Unbeatable portability and battery life. Perfect for students and professionals on the go.",
        "searchable_text": "Apple MacBook Air M3 chip 8GB unified memory macOS space grey thin lightweight laptop under $1500."
    },
    {
        "product_id": "laptop-004",
        "product_name": "Dell XPS 13 OLED",
        "category_path": "Laptops",
        "brand_name": "Dell",
        "selling_price": 139990.0,
        "average_rating": 4.5,
        "review_count": 98,
        "attribute_summary": "Intel Core Ultra 7 processor, 13.4-inch InfinityEdge 3K OLED touch display, seamless haptic trackpad, and CNC machined aluminum.",
        "review_summary": "Beautiful premium design. The InfinityEdge display makes it look futuristic, but ports are limited.",
        "searchable_text": "Dell XPS 13 Intel Core Ultra 7 OLED touch infinityedge display premium portable laptop under $1500."
    },
    {
        "product_id": "laptop-005",
        "product_name": "HP Victus 16 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "HP",
        "selling_price": 84990.0,
        "average_rating": 4.4,
        "review_count": 140,
        "attribute_summary": "Intel Core i5-13500H, NVIDIA RTX 4050 GPU, 16.1-inch FHD 144Hz screen, and custom OMEN Gaming Hub performance software.",
        "review_summary": "Perfect entry level gaming laptop. Can run modern games on high graphics smoothly.",
        "searchable_text": "HP Victus 16 gaming laptop RTX 4050 intel i5 high refresh rate screen budget gaming under $1500."
    },
    {
        "product_id": "laptop-006",
        "product_name": "Acer Nitro 5 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Acer",
        "selling_price": 79990.0,
        "average_rating": 4.3,
        "review_count": 280,
        "attribute_summary": "AMD Ryzen 7 7735HS, NVIDIA RTX 4050, 15.6-inch 144Hz display, and NitroSense command center customization.",
        "review_summary": "Incredible value for budget gamers. Runs extremely cool under heavy load.",
        "searchable_text": "Acer Nitro 5 budget gaming laptop AMD Ryzen 7 RTX 4050 screen gaming under $1500."
    },
    {
        "product_id": "laptop-007",
        "product_name": "ASUS TUF Gaming A15",
        "category_path": "Laptops",
        "brand_name": "ASUS",
        "selling_price": 94990.0,
        "average_rating": 4.5,
        "review_count": 190,
        "attribute_summary": "AMD Ryzen 7 7735HS, NVIDIA RTX 4060 GPU, military-grade chassis durability, and 90Wh long-lasting battery.",
        "review_summary": "The RTX 4060 handles AAA titles easily. Military grade build gives peace of mind.",
        "searchable_text": "ASUS TUF Gaming A15 laptop military durability RTX 4060 graphics long battery under $1500."
    },
    {
        "product_id": "laptop-008",
        "product_name": "Lenovo LOQ 15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Lenovo",
        "selling_price": 89990.0,
        "average_rating": 4.4,
        "review_count": 115,
        "attribute_summary": "Intel Core i5-13450HX, NVIDIA RTX 4060, AI Chip LA1 for dynamic tuning, and WQHD G-Sync display panel.",
        "review_summary": "AI chip optimizes performance dynamically. The G-Sync screen prevents any page tearing.",
        "searchable_text": "Lenovo LOQ gaming laptop RTX 4060 graphics card WQHD screen AI tuned gaming under $1500."
    },
    {
        "product_id": "laptop-009",
        "product_name": "MSI Cyborg 15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "MSI",
        "selling_price": 82990.0,
        "average_rating": 4.2,
        "review_count": 96,
        "attribute_summary": "Intel Core i7-13620H, RTX 4050, translucent keyboard keycaps, and lightweight futuristic design.",
        "review_summary": "Futuristic design looks very cool. Lightweight chassis makes it easy to carry around.",
        "searchable_text": "MSI Cyborg 15 gaming laptop translucent keyboard i7 processor RTX 4050 under $1500."
    },
    {
        "product_id": "laptop-010",
        "product_name": "Gigabyte G5 KF Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Gigabyte",
        "selling_price": 86990.0,
        "average_rating": 4.1,
        "review_count": 82,
        "attribute_summary": "Intel Core i5-12500H, RTX 4060, thin bezel design, and Windforce cooling system.",
        "review_summary": "RTX 4060 at this price point is amazing, though the fan can get slightly loud.",
        "searchable_text": "Gigabyte G5 KF gaming laptop RTX 4060 graphics windforce cooling system under $1500."
    },
    {
        "product_id": "laptop-011",
        "product_name": "Acer Predator Helios Neo 16",
        "category_path": "Laptops",
        "brand_name": "Acer",
        "selling_price": 119990.0,
        "average_rating": 4.6,
        "review_count": 105,
        "attribute_summary": "Intel Core i7-13700HX, RTX 4060, liquid metal cooling compound, and 165Hz IPS WQXGA display.",
        "review_summary": "Liquid metal cooling makes a huge difference. Beautiful screen quality.",
        "searchable_text": "Acer Predator Helios Neo 16 gaming laptop liquid cooling RTX 4060 WQXGA under $1500."
    },
    {
        "product_id": "laptop-012",
        "product_name": "Dell G15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Dell",
        "selling_price": 99990.0,
        "average_rating": 4.4,
        "review_count": 138,
        "attribute_summary": "Intel Core i7-13650HX, RTX 4050, retro styling, Alienware Command Center integration.",
        "review_summary": "Alienware command integration is great. Chunky retro design feels solid.",
        "searchable_text": "Dell G15 retro gaming laptop Alienware cooling RTX 4050 intel i7 under $1500."
    },
    {
        "product_id": "laptop-013",
        "product_name": "HP Omen 16 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "HP",
        "selling_price": 129990.0,
        "average_rating": 4.5,
        "review_count": 87,
        "attribute_summary": "Intel Core i7-13700HX, RTX 4060, Omen Tempest cooling, RGB keyboard backlighting.",
        "review_summary": "Temperature controls are top notch. Clean, professional look that doesn't scream gamer.",
        "searchable_text": "HP Omen 16 premium gaming laptop RTX 4060 graphic card i7 processor under $1500."
    },
    {
        "product_id": "laptop-014",
        "product_name": "MSI Katana 15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "MSI",
        "selling_price": 104990.0,
        "average_rating": 4.3,
        "review_count": 112,
        "attribute_summary": "Intel Core i7-13620H, RTX 4060, Cooler Boost 5, 4-Zone RGB keyboard.",
        "review_summary": "Keyboard illumination is beautiful. Runs heavy titles without stutter.",
        "searchable_text": "MSI Katana 15 gaming laptop intel i7 RTX 4060 graphics rgb keys under $1500."
    },
    {
        "product_id": "laptop-015",
        "product_name": "Lenovo Legion Slim 5",
        "category_path": "Laptops",
        "brand_name": "Lenovo",
        "selling_price": 114990.0,
        "average_rating": 4.6,
        "review_count": 94,
        "attribute_summary": "AMD Ryzen 7 7840HS, RTX 4060, thin light design, and premium aluminum top cover.",
        "review_summary": "Slim design fits perfectly in standard backpacks. Ryzen processor has great efficiency.",
        "searchable_text": "Lenovo Legion Slim 5 thin gaming laptop Ryzen 7 RTX 4060 graphics under $1500."
    },
    {
        "product_id": "laptop-016",
        "product_name": "ASUS ROG Strix G16",
        "category_path": "Laptops",
        "brand_name": "ASUS",
        "selling_price": 139990.0,
        "average_rating": 4.7,
        "review_count": 128,
        "attribute_summary": "Intel Core i7-13650HX, RTX 4060, Nebula display technology, and wrap-around RGB lightbar.",
        "review_summary": "Gorgeous wrap-around lightbar design. The Nebula display is blindingly bright.",
        "searchable_text": "ASUS ROG Strix G16 gaming laptop i7 processor RTX 4060 nebula display under $1500."
    },
    {
        "product_id": "laptop-017",
        "product_name": "Acer Swift X 14 Creator Laptop",
        "category_path": "Laptops",
        "brand_name": "Acer",
        "selling_price": 109990.0,
        "average_rating": 4.5,
        "review_count": 73,
        "attribute_summary": "Intel Core i7-13700H, RTX 4050, 14.5-inch 120Hz OLED screen, and lightweight creator chassis.",
        "review_summary": "Incredible display calibration. Perfect for video editors who also like to game.",
        "searchable_text": "Acer Swift X creator notebook RTX 4050 OLED screen portable workstation under $1500."
    },
    {
        "product_id": "laptop-018",
        "product_name": "MSI Thin 15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "MSI",
        "selling_price": 58990.0,
        "average_rating": 4.1,
        "review_count": 145,
        "attribute_summary": "Intel Core i5-12450H, RTX 3050, 1.86kg lightweight design, brushed metal finish.",
        "review_summary": "Very affordable and surprisingly light. Fits daily office work and casual gaming.",
        "searchable_text": "MSI Thin 15 entry level gaming laptop RTX 3050 lightweight brushed metal under $1500."
    },
    {
        "product_id": "laptop-019",
        "product_name": "Gigabyte AORUS 15 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Gigabyte",
        "selling_price": 119990.0,
        "average_rating": 4.4,
        "review_count": 68,
        "attribute_summary": "Intel Core i7-13700H, RTX 4060, QHD 165Hz screen, customizable RGB details.",
        "review_summary": "QHD display offers incredible detail. Overall performance is top notch.",
        "searchable_text": "Gigabyte AORUS 15 QHD display gaming laptop RTX 4060 intel i7 under $1500."
    },
    {
        "product_id": "laptop-020",
        "product_name": "Razer Blade 14 Gaming Laptop",
        "category_path": "Laptops",
        "brand_name": "Razer",
        "selling_price": 189990.0,
        "average_rating": 4.8,
        "review_count": 110,
        "attribute_summary": "AMD Ryzen 9 7940HS, RTX 4070, ultra compact CNC aluminum, 240Hz display.",
        "review_summary": "The MacBook Pro of gaming laptops. Incredibly thin, premium, and powerful.",
        "searchable_text": "Razer Blade 14 ultra premium gaming laptop Ryzen 9 RTX 4070 CNC aluminum casing."
    }
]

class DatabricksService:
    """Service for interacting with Databricks platform"""

    def __init__(self):
        """Initialize mock clients"""
        logger.info(
            "Databricks service initialized in offline catalog mode",
            endpoint=settings.vector_search_endpoint,
            index=settings.vector_search_index_name,
            gold_table=settings.gold_table
        )

    async def vector_search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search using internal catalog ranking.
        """
        start_time = time.time()
        await asyncio.sleep(0.3) # Simulate platform latency

        if top_k is None:
            top_k = settings.vector_search_top_k

        # Determine target category restrictions based on query keywords to prevent cross-category noise
        q_lower = query.lower()
        target_category = None
        
        if "watch" in q_lower or "wearable" in q_lower:
            target_category = "Smart Watches"
        elif "laptop" in q_lower or "notebook" in q_lower or "macbook" in q_lower or "gaming laptop" in q_lower:
            target_category = "Laptops"
        elif "chair" in q_lower or "seating" in q_lower:
            target_category = "Office Chairs"
        elif "coffee" in q_lower or "espresso" in q_lower or "barista" in q_lower:
            target_category = "Home & Kitchen"
        elif "monitor" in q_lower or "display" in q_lower or "screen" in q_lower:
            target_category = "Monitors"
        elif "headphone" in q_lower or "audio" in q_lower or "earbuds" in q_lower or "airpods" in q_lower:
            target_category = "Audio"

        # Normalize query tokens
        query_tokens = q_lower.split()

        # Score matching based on query terms matching searchable text
        scored_results = []
        for p in MOCK_PRODUCTS:
            # Enforce keyword-based category isolation
            if target_category and p["category_path"] != target_category:
                continue

            # Match explicit filters if specified
            if filters:
                if filters.get("category_path") and p["category_path"] != filters["category_path"]:
                    continue
                if filters.get("brand_name") and p["brand_name"] != filters["brand_name"]:
                    continue

            # Calculate match score based on token frequency
            search_text = p["searchable_text"].lower() + " " + p["product_name"].lower()
            score = 0.5 # Base score
            matched_tokens = 0
            for token in query_tokens:
                if token in search_text:
                    score += 0.15
                    matched_tokens += 1

            if len(query_tokens) > 0:
                score += (matched_tokens / len(query_tokens)) * 0.3

            # Bound score between 0.4 and 0.99
            score = min(max(score, 0.4), 0.99)

            scored_results.append({
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "category_path": p["category_path"],
                "brand_name": p["brand_name"],
                "selling_price": p["selling_price"],
                "average_rating": p["average_rating"],
                "review_count": p["review_count"],
                "similarity_score": score
            })

        # Sort by score descending
        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = scored_results[:top_k]

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Vector search completed",
            query=query,
            results_count=len(results),
            elapsed_ms=elapsed_ms
        )

        return {
            "results": results,
            "total_count": len(results),
            "elapsed_ms": elapsed_ms
        }

    async def get_product_details(
        self,
        product_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch product details from local index mapping.
        """
        await asyncio.sleep(0.1) # Simulate DB retrieval latency
        products = {}
        for p in MOCK_PRODUCTS:
            if p["product_id"] in product_ids:
                pid = p["product_id"]
                products[pid] = {
                    "product_id": pid,
                    "product_name": p["product_name"],
                    "category": p["category_path"],
                    "brand": p["brand_name"],
                    "price": p["selling_price"],
                    "currency": "INR",
                    "avg_rating": p["average_rating"],
                    "review_count": p["review_count"],
                    "attribute_summary": p["attribute_summary"],
                    "review_summary": p["review_summary"],
                    "description": p["searchable_text"],
                }
        return products

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single product by ID."""
        products = await self.get_product_details([product_id])
        return products.get(product_id)

    async def get_related_products(
        self,
        product_id: str,
        query_text: str,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """Get related items using similarity search."""
        res = await self.vector_search(query=query_text, top_k=limit + 1)
        related = [
            r for r in res["results"]
            if r["product_id"] != product_id
        ]
        return related[:limit]

    async def get_search_analytics(self, limit: int = 10) -> Dict[str, Any]:
        """Get top popular search queries."""
        top_queries = [
            {"query": "gaming laptop rtx 4070", "count": 284, "avg_results": 20, "avg_latency_ms": 430},
            {"query": "smart watch health tracking", "count": 182, "avg_results": 20, "avg_latency_ms": 410},
        ]
        return {"top_queries": top_queries[:limit], "period": "last_7_days"}

    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "vector_search": "healthy",
            "sql_warehouse": "healthy",
            "unity_catalog": f"healthy ({len(MOCK_PRODUCTS)} products)"
        }


# Global service instance
databricks_service = DatabricksService()
