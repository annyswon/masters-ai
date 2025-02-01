import streamlit as st
import logging
import sqlite3
import json
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI
client = OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_available_items",
            "description": "Get current available items for booking in warehouse",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_bookings",
            "description": "Get currently taken items from warehouse",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_item",
            "description": "This function allows to take an item from the warehouse. It first verifies if the item is available, and if so, it updates the warehouse booking database to reflect the reservation. The function then returns a confirmation message with the booking status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Name of item from warehouse"
                    }
                },
                "required": [
                    "item"
                ],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "return_item",
            "description": "Give back the specified item to a warehouse",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Name of item from warehouse"
                    }
                },
                "required": [
                    "item"
                ],
                "additionalProperties": False
            },
            "strict": True
        }
    },
]


# Streamlit UI setup
st.set_page_config(page_title="Warehouse Keeper Agent", layout="wide")
st.title("📦 Warehouse Keeper Agent")

# Database connection
def get_data_from_db(query, params=()):
    try:
        conn = sqlite3.connect("assets/warehouse.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

# Function to check item availability
def check_availability(item_name):
    query = "SELECT name, SUM(quantity) FROM items WHERE name LIKE ? GROUP BY name"
    data = get_data_from_db(query, (f"%{item_name}%",))
    return data

# Function to fetch all available items
def get_all_available_items():
    query = "SELECT name, SUM(quantity) FROM items GROUP BY name HAVING SUM(quantity) > 0"
    return get_data_from_db(query)

# Function to fetch current bookings
def get_current_bookings():
    query = "SELECT b.user_name, i.name FROM bookings b JOIN items i ON b.item_id = i.item_id WHERE b.status = 'Booked'"
    return get_data_from_db(query)

# Function to book an item
def book_item(item_name, user_name):
    available_items = check_availability(item_name)
    if available_items and available_items[0][1] > 0:
        conn = sqlite3.connect("assets/warehouse.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bookings (item_id, user_name, booking_date, status) VALUES ((SELECT item_id FROM items WHERE name LIKE ? LIMIT 1), ?, DATE('now'), 'Booked')", (f"%{item_name}%", user_name))
        cursor.execute("UPDATE items SET quantity = quantity - 1 WHERE name LIKE ?", (f"%{item_name}%",))
        conn.commit()
        conn.close()
        return f"✅ {user_name} successfully booked {item_name}!"
    return "❌ Item not available for booking."

# Function to return an item
def return_item(item_name, user_name):
    conn = sqlite3.connect("assets/warehouse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM bookings WHERE user_name = ? AND item_id IN (SELECT item_id FROM items WHERE name LIKE ?) AND status = 'Booked' LIMIT 1", (user_name, f"%{item_name}%"))
    booking = cursor.fetchone()
    if booking:
        cursor.execute("UPDATE bookings SET status = 'Returned' WHERE user_name = ? AND item_id = ?", (user_name, booking[0]))
        cursor.execute("UPDATE items SET quantity = quantity + 1 WHERE item_id = ?", (booking[0],))
        conn.commit()
        conn.close()
        return f"✅ {user_name} successfully returned {item_name}!"
    conn.close()
    return "❌ No active booking found for this item."

# Function to handle external ChatGPT requests and returning function names from tools
def chatgpt_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": "You are a warehouse keeper which in action for managing items in it"},
                {"role": "user", "content": prompt}
            ],
            tools=tools
        )
        logger.info(f"Chatgpt response {response.choices[0].message}")
        return response.choices[0].message
    except Exception as e:
        logger.error(f"ChatGPT API error: {e}")
        return "⚠️ Unable to process request at this time."

# Layout with columns
col1, col2 = st.columns([3, 1])

# Left Column - Chat Interaction
with col1:
    user_input = st.text_input("Ask me about the warehouse:")
    if st.button("Submit"):
        user_words = user_input.lower().split()
        
        response = chatgpt_response(user_input)
        if response.tool_calls == None:
            st.write(response.content)
        else:
            for call in response.tool_calls:
                if call.function.name == "get_available_items":
                    st.write("### 📋 Available Items")
                    with st.container():
                        available_items = get_all_available_items()
                        if available_items:
                            st.markdown("<div style='max-height: 40vh; overflow-y: auto;'>", unsafe_allow_html=True)
                            for item in available_items:
                                st.write(f"{item[0]}: {item[1]} available")
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.write("No items available.")
                            
                elif call.function.name == "get_current_bookings":
                    st.write("### 🔖 Current Bookings")
                    with st.container():
                        current_bookings = get_current_bookings()
                        if current_bookings:
                            st.markdown("<div style='max-height: 40vh; overflow-y: auto;'>", unsafe_allow_html=True)
                            for booking in current_bookings:
                                st.write(f"{booking[1]} - Booked by {booking[0]}")
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.write("No active bookings.")

                elif call.function.name == "take_item":
                    st.write(book_item(json.loads(call.function.arguments)["item"], "User"))
                elif call.function.name == "return_item":
                    st.write(return_item(json.loads(call.function.arguments)["item"], "User"))
                else:
                    st.write("I cannot understand you!")
        
        logger.info(f"User input: {user_input} | Response: {response}")

# Right Column - Warehouse Status
with col2:
    st.write("### 📋 Available Items")
    with st.container():
        available_items = get_all_available_items()
        if available_items:
            st.markdown("<div style='max-height: 40vh; overflow-y: auto;'>", unsafe_allow_html=True)
            for item in available_items:
                st.write(f"{item[0]}: {item[1]} available")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("No items available.")
    
    st.write("### 🔖 Current Bookings")
    with st.container():
        current_bookings = get_current_bookings()
        if current_bookings:
            st.markdown("<div style='max-height: 40vh; overflow-y: auto;'>", unsafe_allow_html=True)
            for booking in current_bookings:
                st.write(f"{booking[1]} - Booked by {booking[0]}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("No active bookings.")
